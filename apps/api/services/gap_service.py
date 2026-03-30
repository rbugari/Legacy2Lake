"""
Gap & Decision Workspace Service - Sprint 3

Manages the utm_project_gaps table: create, list, update, resolve, reopen.
Includes auto-import of gaps from executive_summary_service signals.
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

try:
    from apps.api.utils.logger import logger
    from apps.api.services.persistence_service import SupabasePersistence
    from apps.api.services.executive_summary_service import build_gaps_summary
except ImportError:
    try:
        from utils.logger import logger
        from services.persistence_service import SupabasePersistence
        from services.executive_summary_service import build_gaps_summary
    except ImportError:
        from ..utils.logger import logger
        from .persistence_service import SupabasePersistence
        from .executive_summary_service import build_gaps_summary


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class GapCreate(BaseModel):
    category:          str = Field(default="other")
    severity:          str = Field(default="MEDIUM")
    title:             str
    description:       Optional[str] = None
    why_it_matters:    Optional[str] = None
    recommended_owner: Optional[str] = None
    source_stage:      str = Field(default="manual")
    asset_id:          Optional[str] = None
    decision_note:     Optional[str] = None


class GapUpdate(BaseModel):
    category:          Optional[str] = None
    severity:          Optional[str] = None
    title:             Optional[str] = None
    description:       Optional[str] = None
    why_it_matters:    Optional[str] = None
    recommended_owner: Optional[str] = None
    decision_note:     Optional[str] = None
    resolution_status: Optional[str] = None


class GapResolve(BaseModel):
    decision_note: Optional[str] = None


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class GapService:
    """
    Gap & Decision Workspace Service — Sprint 3.
    """

    TABLE = "utm_project_gaps"

    def __init__(
        self,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.user_id   = user_id
        self.db = SupabasePersistence(tenant_id=tenant_id, client_id=client_id)

    # ── List ──────────────────────────────────────────────────────────────

    async def list_gaps(
        self,
        project_id: str,
        *,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        query = (
            self.db.client.table(self.TABLE)
            .select("*")
            .eq("project_id", project_id)
        )
        if self.tenant_id:
            query = query.eq("tenant_id", self.tenant_id)
        if status:
            query = query.eq("resolution_status", status)
        if severity:
            query = query.eq("severity", severity)
        if category:
            query = query.eq("category", category)

        query = query.order("created_at", desc=True)
        res = query.execute()
        return res.data or []

    # ── Create ────────────────────────────────────────────────────────────

    async def create_gap(self, project_id: str, payload: GapCreate) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "project_id":         project_id,
            "category":           payload.category,
            "severity":           payload.severity.upper(),
            "title":              payload.title,
            "description":        payload.description,
            "why_it_matters":     payload.why_it_matters,
            "recommended_owner":  payload.recommended_owner,
            "source_stage":       payload.source_stage,
            "resolution_status":  "OPEN",
            "decision_note":      payload.decision_note,
        }
        if self.tenant_id:
            data["tenant_id"] = self.tenant_id
        if payload.asset_id:
            data["asset_id"] = payload.asset_id
        if self.user_id:
            data["created_by"] = self.user_id

        res = self.db.client.table(self.TABLE).insert(data).execute()
        return res.data[0] if res.data else {}

    # ── Update ────────────────────────────────────────────────────────────

    async def update_gap(self, gap_id: str, payload: GapUpdate) -> Dict[str, Any]:
        updates: Dict[str, Any] = {k: v for k, v in payload.dict().items() if v is not None}
        if not updates:
            return {}

        if "severity" in updates:
            updates["severity"] = updates["severity"].upper()
        if "resolution_status" in updates:
            updates["resolution_status"] = updates["resolution_status"].upper()

        query = self.db.client.table(self.TABLE).update(updates).eq("gap_id", gap_id)
        if self.tenant_id:
            query = query.eq("tenant_id", self.tenant_id)
        res = query.execute()
        return res.data[0] if res.data else {}

    # ── Resolve ───────────────────────────────────────────────────────────

    async def resolve_gap(self, gap_id: str, payload: GapResolve) -> Dict[str, Any]:
        updates: Dict[str, Any] = {
            "resolution_status": "RESOLVED",
            "resolved_at":       datetime.utcnow().isoformat(),
        }
        if payload.decision_note:
            updates["decision_note"] = payload.decision_note
        if self.user_id:
            updates["resolved_by"] = self.user_id

        query = self.db.client.table(self.TABLE).update(updates).eq("gap_id", gap_id)
        if self.tenant_id:
            query = query.eq("tenant_id", self.tenant_id)
        res = query.execute()
        return res.data[0] if res.data else {}

    # ── Reopen ────────────────────────────────────────────────────────────

    async def reopen_gap(self, gap_id: str) -> Dict[str, Any]:
        updates = {
            "resolution_status": "OPEN",
            "resolved_at":       None,
            "resolved_by":       None,
        }
        query = self.db.client.table(self.TABLE).update(updates).eq("gap_id", gap_id)
        if self.tenant_id:
            query = query.eq("tenant_id", self.tenant_id)
        res = query.execute()
        return res.data[0] if res.data else {}

    # ── Import from signals ───────────────────────────────────────────────

    async def import_from_signals(self, project_id: str) -> Dict[str, Any]:
        """
        Auto-import gaps derived from quick_assessment + asset signals.
        Skips items that are already present (simple title+project dedup).
        Returns counts of imported and skipped gaps.
        """
        project = await self.db.get_project_metadata(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        assets = await self.db.get_project_assets(project_id) or []
        gaps_summary = build_gaps_summary(project, assets)

        # Collect all gap items
        all_items: List[Dict] = []
        for group in gaps_summary.get("grouped", {}).values():
            all_items.extend(group)

        # Fetch existing titles to deduplicate
        existing = await self.list_gaps(project_id)
        existing_titles = {g["title"].lower() for g in existing}

        imported = 0
        skipped  = 0

        for item in all_items:
            title = item.get("title", "")
            if title.lower() in existing_titles:
                skipped += 1
                continue

            payload = GapCreate(
                category=item.get("category", "other"),
                severity=item.get("severity", "MEDIUM"),
                title=title,
                description=item.get("description"),
                why_it_matters=item.get("why_it_matters"),
                source_stage=item.get("source_stage", "discovery"),
                asset_id=item.get("asset_id"),
            )
            await self.create_gap(project_id, payload)
            existing_titles.add(title.lower())
            imported += 1

        logger.info(
            f"[GapService] Import complete: {imported} imported, {skipped} skipped",
            "GapService"
        )
        return {"imported": imported, "skipped": skipped, "total": imported + skipped}

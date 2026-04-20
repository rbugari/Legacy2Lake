"""
TraceabilityService - v4.5
Builds a legacy-to-target traceability map for a given asset.

Each entry in the map has a status badge:
  PRESERVED   - field/table exists in target with same name and semantics
  INFERRED    - field/table exists in target but name or type was derived/renamed
  CHANGED     - explicit transformation applied (cast, logic, aggregation)
  UNRESOLVED  - field/table present in source but not found in target output

Sources used (in order of richness):
  1. utm_asset_columns (source columns + understanding columns)
  2. utm_table_impacts  (source table → operations)
  3. utm_objects        (asset metadata, generated_payload)
  4. utm_code_validations (target generated code, diff data)
"""
from typing import Any, Dict, List, Optional
import re

try:
    from apps.api.utils.logger import logger
    from apps.api.services.persistence_service import SupabasePersistence
except ImportError:
    try:
        from utils.logger import logger
        from services.persistence_service import SupabasePersistence
    except ImportError:
        from ..utils.logger import logger
        from .persistence_service import SupabasePersistence


_STATUS_PRESERVED  = "PRESERVED"
_STATUS_INFERRED   = "INFERRED"
_STATUS_CHANGED    = "CHANGED"
_STATUS_UNRESOLVED = "UNRESOLVED"


def _normalise(name: str) -> str:
    """Lower-case, strip schema prefixes and brackets for fuzzy comparison."""
    if not name:
        return ""
    name = name.lower().strip()
    # Strip schema prefix: dbo.table_name → table_name
    if "." in name:
        name = name.split(".")[-1]
    # Strip SSIS bracket pattern
    name = re.sub(r"^\[(.+)\]$", r"\1", name)
    return name


def _classify_column(
    src_col: str,
    src_type: str,
    target_cols: List[Dict[str, Any]],
    transformations: List[str],
) -> Dict[str, Any]:
    """
    Compare a source column against target columns + known transformations.
    Returns a traceability entry dict.
    """
    src_norm = _normalise(src_col)

    # Check explicit transformations first
    for t in transformations:
        if src_norm in t.lower():
            return {
                "source_name": src_col,
                "source_type": src_type,
                "target_name": _extract_target_from_transform(t, src_norm),
                "status": _STATUS_CHANGED,
                "note": t[:200],
            }

    # Exact match
    for tc in target_cols:
        if _normalise(tc.get("name", "")) == src_norm:
            return {
                "source_name": src_col,
                "source_type": src_type,
                "target_name": tc.get("name", src_col),
                "status": _STATUS_PRESERVED,
                "note": None,
            }

    # Fuzzy match (substring or common rename patterns)
    for tc in target_cols:
        tname = _normalise(tc.get("name", ""))
        if src_norm in tname or tname in src_norm:
            return {
                "source_name": src_col,
                "source_type": src_type,
                "target_name": tc.get("name", ""),
                "status": _STATUS_INFERRED,
                "note": "Name matched by substring — verify mapping",
            }

    return {
        "source_name": src_col,
        "source_type": src_type,
        "target_name": None,
        "status": _STATUS_UNRESOLVED,
        "note": "Column not found in generated target output",
    }


def _extract_target_from_transform(transform: str, src_norm: str) -> Optional[str]:
    """Try to extract target column name from a transformation hint string."""
    # Common pattern: "AS target_col" or "→ target_col"
    m = re.search(r"(?:AS|as|→)\s+([a-zA-Z_][a-zA-Z0-9_]*)", transform)
    if m:
        return m.group(1)
    return None


def _classify_table(
    src_table: str,
    operation: str,
    target_code: str,
) -> Dict[str, Any]:
    """Determine traceability status for a source table reference."""
    src_norm = _normalise(src_table)
    code_lower = (target_code or "").lower()

    if src_norm in code_lower:
        return {
            "source_name": src_table,
            "operation": operation,
            "status": _STATUS_PRESERVED,
            "note": "Table reference found in generated output",
        }

    # Check for renamed/aliased references (spark read, from clause variants)
    # e.g., spark.read.table("some_table") or FROM some_table
    pattern = r"(?:from|read\.table\(|spark\.table\()['\"]?" + re.escape(src_norm) + r"['\"]?"
    if re.search(pattern, code_lower):
        return {
            "source_name": src_table,
            "operation": operation,
            "status": _STATUS_PRESERVED,
            "note": "Table reference found in generated output",
        }

    return {
        "source_name": src_table,
        "operation": operation,
        "status": _STATUS_UNRESOLVED,
        "note": "Table not found in generated target output — may be renamed or abstracted",
    }


class TraceabilityService:
    """Builds a traceability map for a single asset within a project."""

    def __init__(self, tenant_id: str, project_id: str):
        self.tenant_id = tenant_id
        self.project_id = project_id
        self.db = SupabasePersistence(tenant_id=tenant_id)

    def _fetch_asset(self, asset_id: str) -> Optional[Dict[str, Any]]:
        try:
            res = (
                self.db.client.table("utm_objects")
                .select("object_id,source_name,type,category,generated_payload,understanding_payload")
                .eq("object_id", asset_id)
                .eq("project_id", self.project_id)
                .eq("tenant_id", self.tenant_id)
                .limit(1)
                .execute()
            )
            rows = res.data or []
            return rows[0] if rows else None
        except Exception as exc:
            logger.error(f"[Traceability] fetch asset error: {exc}", "TraceabilityService")
            return None

    def _fetch_source_columns(self, asset_id: str) -> List[Dict[str, Any]]:
        try:
            res = (
                self.db.client.table("utm_asset_columns")
                .select("column_name,data_type,source_type,is_pii")
                .eq("asset_id", asset_id)
                .execute()
            )
            return res.data or []
        except Exception:
            return []

    def _fetch_table_impacts(self, asset_id: str) -> List[Dict[str, Any]]:
        try:
            res = (
                self.db.client.table("utm_table_impacts")
                .select("table_name,operation")
                .eq("asset_id", asset_id)
                .eq("project_id", self.project_id)
                .execute()
            )
            return res.data or []
        except Exception:
            return []

    def _fetch_target_code(self, asset_id: str) -> str:
        """Fetch the latest generated code snippet for this asset."""
        try:
            # Try utm_code_validations first (has generated_code field)
            res = (
                self.db.client.table("utm_code_validations")
                .select("generated_code")
                .eq("asset_id", asset_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            rows = res.data or []
            if rows and rows[0].get("generated_code"):
                return rows[0]["generated_code"]
        except Exception:
            pass

        # Fallback: generated_payload on utm_objects
        try:
            res = (
                self.db.client.table("utm_objects")
                .select("generated_payload")
                .eq("object_id", asset_id)
                .limit(1)
                .execute()
            )
            rows = res.data or []
            if rows:
                payload = rows[0].get("generated_payload") or {}
                if isinstance(payload, dict):
                    return payload.get("code", "") or payload.get("content", "") or ""
                if isinstance(payload, str):
                    return payload
        except Exception:
            pass

        return ""

    def _extract_target_columns(self, target_code: str) -> List[Dict[str, Any]]:
        """
        Lightweight extraction of column-like identifiers from generated code.
        Looks for SELECT col_name, df['col_name'], or schema definitions.
        """
        cols: List[Dict[str, Any]] = []
        if not target_code:
            return cols
        seen = set()
        # SQL: SELECT col1, col2 or col1 AS alias
        for m in re.finditer(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:AS\s+([a-zA-Z_][a-zA-Z0-9_]*))?\b", target_code):
            name = m.group(2) or m.group(1)
            if name.lower() not in ("select", "from", "where", "join", "on", "and", "or", "as", "is", "not", "null", "true", "false"):
                if name not in seen:
                    seen.add(name)
                    cols.append({"name": name})
        return cols

    def _extract_transformations(self, asset: Dict[str, Any]) -> List[str]:
        """Extract known transformation hints from understanding_payload."""
        transforms: List[str] = []
        up = asset.get("understanding_payload") or {}
        if isinstance(up, str):
            import json
            try:
                up = json.loads(up)
            except Exception:
                return transforms
        for section in ["transformations", "business_rules", "mappings"]:
            items = (up.get(section) or [])
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, str):
                        transforms.append(item)
                    elif isinstance(item, dict):
                        text = item.get("description") or item.get("rule") or item.get("mapping") or ""
                        if text:
                            transforms.append(str(text))
        return transforms

    def build(self, asset_id: str) -> Dict[str, Any]:
        """
        Build the full traceability map for one asset.
        Returns:
        {
          asset_id, asset_name, asset_type,
          summary: { preserved, inferred, changed, unresolved, total },
          column_entries: [ ... ],
          table_entries: [ ... ],
          computed_at
        }
        """
        from datetime import datetime, timezone

        asset = self._fetch_asset(asset_id)
        if not asset:
            return {
                "asset_id": asset_id,
                "error": "Asset not found or access denied",
                "column_entries": [],
                "table_entries": [],
                "summary": {"preserved": 0, "inferred": 0, "changed": 0, "unresolved": 0, "total": 0},
                "computed_at": datetime.now(timezone.utc).isoformat(),
            }

        asset_name = asset.get("source_name", "unknown")
        target_code = self._fetch_target_code(asset_id)
        target_cols = self._extract_target_columns(target_code)
        transformations = self._extract_transformations(asset)
        source_columns = self._fetch_source_columns(asset_id)
        table_impacts = self._fetch_table_impacts(asset_id)

        column_entries: List[Dict[str, Any]] = []
        for sc in source_columns:
            entry = _classify_column(
                src_col=sc.get("column_name", "?"),
                src_type=sc.get("data_type") or sc.get("source_type") or "UNKNOWN",
                target_cols=target_cols,
                transformations=transformations,
            )
            entry["is_pii"] = sc.get("is_pii", False)
            column_entries.append(entry)

        table_entries: List[Dict[str, Any]] = []
        for ti in table_impacts:
            entry = _classify_table(
                src_table=ti.get("table_name", "?"),
                operation=ti.get("operation", "?"),
                target_code=target_code,
            )
            table_entries.append(entry)

        # Summary counts
        all_entries = column_entries + table_entries
        counts = {
            "preserved": sum(1 for e in all_entries if e["status"] == _STATUS_PRESERVED),
            "inferred":  sum(1 for e in all_entries if e["status"] == _STATUS_INFERRED),
            "changed":   sum(1 for e in all_entries if e["status"] == _STATUS_CHANGED),
            "unresolved": sum(1 for e in all_entries if e["status"] == _STATUS_UNRESOLVED),
        }
        counts["total"] = sum(counts.values())

        # Determine overall status
        if not target_code:
            overall = "NO_TARGET_OUTPUT"
        elif counts["unresolved"] == 0 and counts["changed"] == 0:
            overall = "FULLY_MAPPED"
        elif counts["unresolved"] == 0:
            overall = "MAPPED_WITH_CHANGES"
        elif counts["unresolved"] < counts["total"] * 0.3:
            overall = "MOSTLY_MAPPED"
        else:
            overall = "REQUIRES_REVIEW"

        result = {
            "asset_id": asset_id,
            "asset_name": asset_name,
            "asset_type": asset.get("type", "UNKNOWN"),
            "target_code_available": bool(target_code),
            "overall_status": overall,
            "summary": counts,
            "column_entries": column_entries,
            "table_entries": table_entries,
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }

        # Persist/update cache (best-effort)
        try:
            self.db.client.table("utm_asset_traceability").upsert({
                "tenant_id": self.tenant_id,
                "project_id": self.project_id,
                "asset_id": asset_id,
                "asset_name": asset_name,
                "entries": {
                    "column_entries": column_entries,
                    "table_entries": table_entries,
                    "summary": counts,
                    "overall_status": overall,
                },
                "computed_at": result["computed_at"],
            }, on_conflict="project_id,asset_id").execute()
        except Exception as exc:
            logger.error(f"[Traceability] cache write error: {exc}", "TraceabilityService")

        logger.info(
            f"[Traceability] asset={asset_id} overall={overall} "
            f"preserved={counts['preserved']} unresolved={counts['unresolved']}",
            "TraceabilityService",
        )
        return result

    def list_for_project(self) -> List[Dict[str, Any]]:
        """
        Returns a summary list of traceability status for all assets in the project
        that have generated output. Used for the project-level overview.
        """
        try:
            res = (
                self.db.client.table("utm_asset_traceability")
                .select("asset_id,asset_name,entries,computed_at")
                .eq("project_id", self.project_id)
                .eq("tenant_id", self.tenant_id)
                .order("asset_name", desc=False)
                .execute()
            )
            rows = res.data or []
            result = []
            for r in rows:
                entries = r.get("entries") or {}
                result.append({
                    "asset_id": r["asset_id"],
                    "asset_name": r.get("asset_name"),
                    "overall_status": entries.get("overall_status", "UNKNOWN"),
                    "summary": entries.get("summary", {}),
                    "computed_at": r.get("computed_at"),
                })
            return result
        except Exception as exc:
            logger.error(f"[Traceability] list error: {exc}", "TraceabilityService")
            return []

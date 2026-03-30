"""
Readiness + Confidence Model Service - Sprint 1

Aggregates multiple project signals into a single, explainable readiness state.
Persists result as JSONB on utm_projects.readiness_summary.
"""
from datetime import datetime
from typing import Dict, Any, List, Optional

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


# ---------------------------------------------------------------------------
# Status labels (ordered worst → best)
# ---------------------------------------------------------------------------
STATUS_NOT_RECOMMENDED = "NOT_RECOMMENDED_FOR_AUTOMATION"
STATUS_REQUIRES_CONTEXT = "REQUIRES_CONTEXT"
STATUS_BASELINE_READY   = "BASELINE_READY"
STATUS_READY            = "READY"

_STATUS_RANK = {
    STATUS_NOT_RECOMMENDED: 0,
    STATUS_REQUIRES_CONTEXT: 1,
    STATUS_BASELINE_READY:   2,
    STATUS_READY:            3,
}


# ---------------------------------------------------------------------------
# Signal extractors
# ---------------------------------------------------------------------------

def _signal_from_quick_assessment(qa: Optional[Dict]) -> Dict[str, Any]:
    """Extract readiness signal from a stored quick_assessment payload."""
    if not qa or not isinstance(qa, dict):
        return {"present": False}

    score    = qa.get("score", 0)
    semaforo = (qa.get("semaforo") or "").lower()
    blockers = qa.get("blockers") or []
    techs    = qa.get("detected_techs") or []
    breakdown = qa.get("file_breakdown") or {}
    total_files = qa.get("total_files", 0)

    return {
        "present":      True,
        "score":        score,
        "semaforo":     semaforo,
        "blockers":     blockers,
        "detected_techs": techs,
        "migrable_count": breakdown.get("migrable", 0),
        "total_files":  total_files,
    }


def _signal_from_triage(assets: List[Dict]) -> Dict[str, Any]:
    """Extract readiness signal from triaged asset list."""
    if not assets:
        return {"present": False, "triaged": 0}

    triaged      = len(assets)
    core_count   = sum(1 for a in assets if (a.get("type") or "").upper() == "CORE")
    pii_count    = sum(1 for a in assets if a.get("is_pii"))
    high_complex = sum(
        1 for a in assets
        if (a.get("metadata") or {}).get("complexity_level", "").upper() == "HIGH"
    )
    validated_count = sum(
        1 for a in assets
        if a.get("validation_result") is not None
    )

    return {
        "present":         True,
        "triaged":         triaged,
        "core_count":      core_count,
        "pii_count":       pii_count,
        "high_complex":    high_complex,
        "validated_count": validated_count,
    }


def _signal_from_project(project: Dict) -> Dict[str, Any]:
    """Extract lightweight readiness hints from project metadata."""
    settings = project.get("settings") or {}
    config   = project.get("config")   or {}

    source_tech = (
        project.get("source_tech") or
        settings.get("source_tech") or
        config.get("source_tech")
    )
    target_tech = (
        project.get("target_tech") or
        settings.get("target_tech") or
        config.get("target_tech")
    )
    stage  = project.get("stage",  0)
    status = (project.get("status") or "").upper()

    return {
        "source_tech": source_tech,
        "target_tech": target_tech,
        "stage":       stage,
        "status":      status,
        "has_prompt":  bool(project.get("prompt")),
    }


# ---------------------------------------------------------------------------
# Readiness aggregation
# ---------------------------------------------------------------------------

def compute_readiness(
    project: Dict,
    assets: List[Dict],
) -> Dict[str, Any]:
    """
    Pure function: aggregate all available signals and return a readiness payload.

    Returns a dict with:
        status, confidence_score, top_reasons, blockers,
        recommended_next_action, source_signals, computed_at
    """
    qa_sig  = _signal_from_quick_assessment(project.get("quick_assessment"))
    tri_sig = _signal_from_triage(assets)
    prj_sig = _signal_from_project(project)

    reasons: List[str] = []
    blockers: List[str] = []
    confidence = 50  # baseline

    # ── Signal: quick assessment ────────────────────────────────────────────
    if qa_sig["present"]:
        qa_score = qa_sig["score"]
        semaforo = qa_sig["semaforo"]

        if semaforo == "green":
            confidence += 20
            reasons.append(f"Viability assessment is GREEN ({qa_score}% score)")
        elif semaforo == "yellow":
            confidence += 5
            reasons.append(f"Viability assessment is YELLOW ({qa_score}% score) — review warnings")
        else:
            confidence -= 20
            reasons.append(f"Viability assessment is RED ({qa_score}% score) — high risk")

        blockers.extend(qa_sig.get("blockers") or [])

        if qa_sig["migrable_count"] == 0:
            blockers.append("No migrable ETL packages detected")
            confidence -= 15

        if qa_sig["detected_techs"]:
            reasons.append(f"Detected technology: {', '.join(qa_sig['detected_techs'])}")
    else:
        reasons.append("Viability assessment not yet run")
        confidence -= 10

    # ── Signal: triage ──────────────────────────────────────────────────────
    if tri_sig["present"] and tri_sig["triaged"] > 0:
        confidence += 10
        reasons.append(f"Triage complete — {tri_sig['triaged']} assets inventoried, {tri_sig['core_count']} CORE")

        if tri_sig["pii_count"] > 0:
            reasons.append(f"{tri_sig['pii_count']} PII-flagged asset(s) require compliance review")
            confidence -= 5

        if tri_sig["high_complex"] > 0:
            reasons.append(f"{tri_sig['high_complex']} HIGH complexity asset(s) identified")
            confidence -= 5
    else:
        reasons.append("Triage not yet complete — asset inventory pending")
        confidence -= 5

    # ── Signal: project configuration ───────────────────────────────────────
    if not prj_sig["source_tech"]:
        blockers.append("Source technology not configured")
        confidence -= 10
    if not prj_sig["target_tech"]:
        blockers.append("Target technology not configured")
        confidence -= 10
    if not prj_sig["has_prompt"]:
        confidence -= 5
        reasons.append("No custom migration prompt configured — using defaults")

    # ── Clamp confidence ─────────────────────────────────────────────────────
    confidence = max(0, min(100, confidence))

    # ── Derive status ────────────────────────────────────────────────────────
    if blockers:
        if confidence < 30:
            status = STATUS_NOT_RECOMMENDED
        else:
            status = STATUS_REQUIRES_CONTEXT
    elif confidence >= 70:
        status = STATUS_READY
    elif confidence >= 45:
        status = STATUS_BASELINE_READY
    else:
        status = STATUS_REQUIRES_CONTEXT

    # ── Recommended next action ───────────────────────────────────────────────
    next_action = _recommend_next_action(status, blockers, prj_sig, qa_sig, tri_sig)

    return {
        "status":                  status,
        "confidence_score":        confidence,
        "top_reasons":             reasons[:5],  # cap to top 5
        "blockers":                blockers,
        "recommended_next_action": next_action,
        "source_signals": {
            "quick_assessment_present": qa_sig["present"],
            "triage_complete":          tri_sig.get("triaged", 0) > 0,
            "source_tech_set":          bool(prj_sig["source_tech"]),
            "target_tech_set":          bool(prj_sig["target_tech"]),
            "project_stage":            prj_sig["stage"],
        },
        "computed_at": datetime.utcnow().isoformat(),
    }


def _recommend_next_action(
    status: str,
    blockers: List[str],
    prj_sig: Dict,
    qa_sig: Dict,
    tri_sig: Dict,
) -> str:
    if not prj_sig["source_tech"] or not prj_sig["target_tech"]:
        return "Configure source and target technology in project settings before proceeding."

    if not qa_sig.get("present"):
        return "Run the Forensic Scan in Discovery to generate a viability assessment."

    if qa_sig.get("semaforo") == "red":
        return "Review the blockers identified in the viability assessment before advancing to Triage."

    if not tri_sig.get("present") or tri_sig.get("triaged", 0) == 0:
        return "Advance to Triage stage to inventory and classify all migration assets."

    if status == STATUS_REQUIRES_CONTEXT:
        return "Review and resolve open blockers, then recompute readiness before generating code."

    if status == STATUS_BASELINE_READY:
        return "Project is baseline ready. Proceed to Drafting for code generation."

    if status == STATUS_READY:
        return "Project is ready for automated migration. Proceed to Drafting or Refinement."

    return "Review project configuration and re-run the assessment."


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------

class ReadinessService:
    """
    Readiness + Confidence Model — Sprint 1

    Aggregates project signals into a persisted readiness payload.
    """

    def __init__(self, tenant_id: Optional[str] = None, client_id: Optional[str] = None):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.db = SupabasePersistence(tenant_id=tenant_id, client_id=client_id)

    async def get_readiness(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Returns persisted readiness summary for the project, or None if not computed yet.
        """
        try:
            res = self.db.client.table("utm_projects") \
                .select("readiness_summary") \
                .eq("project_id", project_id) \
                .execute()
            if res.data and res.data[0].get("readiness_summary"):
                return res.data[0]["readiness_summary"]
        except Exception as e:
            logger.warning(f"[Readiness] Could not fetch persisted readiness: {e}", "Readiness")
        return None

    async def compute_and_persist(self, project_id: str) -> Dict[str, Any]:
        """
        Recomputes readiness from all available signals and persists the result.

        Returns the computed readiness payload.
        """
        logger.info(f"[Readiness] Computing for project_id={project_id}", "Readiness")

        project = await self.db.get_project_metadata(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        assets = await self.db.get_project_assets(project_id)

        payload = compute_readiness(project, assets or [])

        await self.db.update_project_metadata(project_id, {"readiness_summary": payload})

        logger.info(
            f"[Readiness] Persisted: status={payload['status']}, confidence={payload['confidence_score']}",
            "Readiness"
        )
        return payload

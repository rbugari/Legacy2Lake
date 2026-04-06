"""
Executive Summary Service - Sprint 2

Derives a business-facing summary from technical signals.
No DB storage in first pass — computed on demand.
Optionally uses LLM (agent-exec) for narrative enrichment.
"""
from datetime import datetime
from typing import Dict, Any, List, Optional

try:
    from apps.api.utils.logger import logger
    from apps.api.services.persistence_service import SupabasePersistence
    from apps.api.services.readiness_service import (
        compute_readiness,
        STATUS_NOT_RECOMMENDED, STATUS_REQUIRES_CONTEXT,
        STATUS_BASELINE_READY, STATUS_READY,
    )
except ImportError:
    try:
        from utils.logger import logger
        from services.persistence_service import SupabasePersistence
        from services.readiness_service import (
            compute_readiness,
            STATUS_NOT_RECOMMENDED, STATUS_REQUIRES_CONTEXT,
            STATUS_BASELINE_READY, STATUS_READY,
        )
    except ImportError:
        from ..utils.logger import logger
        from .persistence_service import SupabasePersistence
        from .readiness_service import (
            compute_readiness,
            STATUS_NOT_RECOMMENDED, STATUS_REQUIRES_CONTEXT,
            STATUS_BASELINE_READY, STATUS_READY,
        )


# ---------------------------------------------------------------------------
# Gap categories
# ---------------------------------------------------------------------------

GAP_CATEGORIES = [
    "schema",
    "mappings",
    "business_rules",
    "orchestration",
    "data_quality",
    "compliance",
    "target_architecture",
]

_SEVERITY_RANK = {"CRITICAL": 3, "HIGH": 2, "MEDIUM": 1, "LOW": 0}


def _build_decision_queue(gaps: List[Dict]) -> Dict[str, Any]:
    """Summarize the highest-value decisions that still need attention."""
    if not gaps:
        return {
            "items": [],
            "focus": "No pending decision queue detected.",
            "open_count": 0,
        }

    sorted_gaps = sorted(
        gaps,
        key=lambda gap: _SEVERITY_RANK.get(gap.get("severity", "LOW"), 0),
        reverse=True,
    )

    items = []
    category_counts: Dict[str, int] = {}
    for gap in sorted_gaps:
        category = gap.get("category", "other")
        category_counts[category] = category_counts.get(category, 0) + 1
        items.append({
            "title": gap.get("title", "Untitled gap"),
            "severity": gap.get("severity", "LOW"),
            "category": category,
            "why_it_matters": gap.get("why_it_matters") or gap.get("description") or "",
            "source_stage": gap.get("source_stage", "unknown"),
            "asset_name": gap.get("asset_name"),
        })

    focus_categories = sorted(
        category_counts.items(),
        key=lambda item: (-item[1], item[0]),
    )[:2]
    if focus_categories:
        focus_labels = [cat.replace("_", " ").title() for cat, _count in focus_categories]
        focus = f"Resolve {', '.join(focus_labels)} items before the next handoff."
    else:
        focus = "Review open decision items before advancing the project."

    return {
        "items": items[:4],
        "focus": focus,
        "open_count": len(gaps),
    }


# ---------------------------------------------------------------------------
# Gap extraction helpers
# ---------------------------------------------------------------------------

def _extract_gaps_from_assets(assets: List[Dict]) -> List[Dict[str, Any]]:
    """Derive gap items from triaged assets."""
    gaps: List[Dict[str, Any]] = []

    for asset in assets:
        meta = asset.get("metadata") or {}
        obj_name = asset.get("object_name") or asset.get("source_name") or asset.get("source_path", "")

        # PII compliance gap
        if asset.get("is_pii"):
            gaps.append({
                "category":    "compliance",
                "severity":    "HIGH",
                "title":       f"PII data detected in {obj_name}",
                "description": asset.get("metadata", {}).get("pii_reason", "Asset flagged as containing personally identifiable information."),
                "why_it_matters": "Regulatory requirements (GDPR, CCPA) mandate masking or encryption before loading to target.",
                "source_stage":   "triage",
                "asset_id":       asset.get("object_id"),
                "asset_name":     obj_name,
            })

        # High complexity translation gap
        complexity = (
            meta.get("complexity_level") or
            meta.get("complexity") or
            asset.get("complexity") or ""
        ).upper()
        if complexity == "HIGH":
            gaps.append({
                "category":    "business_rules",
                "severity":    "MEDIUM",
                "title":       f"High complexity transformation in {obj_name}",
                "description": "Asset has high cyclomatic complexity or nested transformation logic that may require manual review after code generation.",
                "why_it_matters": "High-complexity assets are most likely to contain undocumented business rules that automated translation cannot resolve.",
                "source_stage":   "triage",
                "asset_id":       asset.get("object_id"),
                "asset_name":     obj_name,
            })

        # Type mismatches
        mismatch_count = meta.get("mismatch_count", 0)
        if mismatch_count and int(mismatch_count) > 0:
            gaps.append({
                "category":    "schema",
                "severity":    "MEDIUM",
                "title":       f"{mismatch_count} column type mismatch(es) in {obj_name}",
                "description": f"{mismatch_count} column(s) have incompatible data types between source and target schema.",
                "why_it_matters": "Type mismatches will cause runtime failures in the target pipeline unless resolved with explicit casts.",
                "source_stage":   "triage",
                "asset_id":       asset.get("object_id"),
                "asset_name":     obj_name,
            })

        # Validation failures
        val_result = asset.get("validation_result") or {}
        if isinstance(val_result, dict):
            violations = val_result.get("violations") or []
            if violations:
                gaps.append({
                    "category":    "data_quality",
                    "severity":    "HIGH" if len(violations) >= 3 else "MEDIUM",
                    "title":       f"{len(violations)} validation violation(s) in {obj_name}",
                    "description": "; ".join(str(v) for v in violations[:3]),
                    "why_it_matters": "Generated code has quality rule violations that must be resolved before certification.",
                    "source_stage":   "refinement",
                    "asset_id":       asset.get("object_id"),
                    "asset_name":     obj_name,
                })

    return gaps


def _extract_gaps_from_quick_assessment(qa: Optional[Dict]) -> List[Dict[str, Any]]:
    """Derive gaps from quick assessment blockers."""
    if not qa:
        return []

    gaps = []
    for blocker in qa.get("blockers") or []:
        gaps.append({
            "category":    "target_architecture",
            "severity":    "CRITICAL",
            "title":       blocker,
            "description": blocker,
            "why_it_matters": "Blocker identified during initial viability assessment — must be resolved before triage.",
            "source_stage":   "discovery",
            "asset_id":       None,
            "asset_name":     None,
        })
    return gaps


def _group_gaps(gaps: List[Dict]) -> Dict[str, List[Dict]]:
    """Group gaps by category and sort by severity within each group."""
    grouped: Dict[str, List[Dict]] = {cat: [] for cat in GAP_CATEGORIES}
    other: List[Dict] = []

    for gap in gaps:
        cat = gap.get("category", "").lower()
        if cat in grouped:
            grouped[cat].append(gap)
        else:
            other.append(gap)

    if other:
        grouped["other"] = other

    # Sort each group by severity (desc)
    for cat in grouped:
        grouped[cat].sort(
            key=lambda g: _SEVERITY_RANK.get(g.get("severity", "LOW"), 0),
            reverse=True
        )

    # Remove empty categories
    return {k: v for k, v in grouped.items() if v}


# ---------------------------------------------------------------------------
# Executive summary builder
# ---------------------------------------------------------------------------

_POSTURE_MAP = {
    STATUS_READY:            "Strong — Automation Recommended",
    STATUS_BASELINE_READY:   "Moderate — Proceed with monitoring",
    STATUS_REQUIRES_CONTEXT: "Caution — Open items require resolution",
    STATUS_NOT_RECOMMENDED:  "High Risk — Manual review required",
}


def _derive_manual_effort_areas(gaps: List[Dict]) -> List[str]:
    """Identify areas most likely to need manual effort."""
    category_counts: Dict[str, int] = {}
    for g in gaps:
        cat = g.get("category", "unknown")
        category_counts[cat] = category_counts.get(cat, 0) + 1

    areas = []
    if category_counts.get("business_rules", 0) > 0:
        areas.append(f"Business rules ({category_counts['business_rules']} item(s))")
    if category_counts.get("schema", 0) > 0:
        areas.append(f"Schema alignment ({category_counts['schema']} item(s))")
    if category_counts.get("compliance", 0) > 0:
        areas.append(f"Compliance / PII handling ({category_counts['compliance']} item(s))")
    if category_counts.get("orchestration", 0) > 0:
        areas.append(f"Orchestration dependencies ({category_counts['orchestration']} item(s))")
    return areas[:4]  # cap


def build_executive_summary(
    project: Dict,
    assets: List[Dict],
    readiness: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Build a business-facing executive summary.

    Returns a dict with:
        migration_posture, confidence_score, top_risks,
        manual_effort_areas, open_blockers, recommended_next_action,
        migrable_assets, total_assets, source_tech, target_tech,
        computed_at
    """
    settings = project.get("settings") or {}
    config   = project.get("config")   or {}

    source_tech = project.get("source_tech") or settings.get("source_tech") or config.get("source_tech") or "Unknown"
    target_tech = project.get("target_tech") or settings.get("target_tech") or config.get("target_tech") or "Unknown"

    # Use persisted readiness if available, else compute fresh
    if readiness is None:
        readiness = project.get("readiness_summary")
    if readiness is None:
        readiness = compute_readiness(project, assets)

    status          = readiness.get("status", STATUS_REQUIRES_CONTEXT)
    confidence      = readiness.get("confidence_score", 50)
    blockers        = readiness.get("blockers") or []
    warnings        = readiness.get("warnings") or []
    next_steps      = readiness.get("next_steps") or []
    next_action     = readiness.get("recommended_next_action", "")

    # Asset statistics
    total_assets   = len(assets) if assets else 0
    core_assets    = sum(1 for a in (assets or []) if (a.get("type") or "").upper() == "CORE")
    pii_assets     = sum(1 for a in (assets or []) if a.get("is_pii"))

    # Quick assessment signals
    qa = project.get("quick_assessment") or {}
    qa_score        = qa.get("score", 0)
    detected_techs  = qa.get("detected_techs") or [source_tech]

    # Top risks — ordered by criticality: blockers first, then status signals, then warnings
    blockers_risks: List[str] = list(blockers[:3])
    signal_risks: List[str] = []
    if status == STATUS_NOT_RECOMMENDED:
        signal_risks.append("Viability assessment indicates high automation risk")
    elif status == STATUS_REQUIRES_CONTEXT:
        signal_risks.append("Open context gaps may reduce automation coverage")
    if pii_assets > 0:
        signal_risks.append(f"{pii_assets} asset(s) contain PII — compliance action required before go-live")
    if qa_score < 50 and qa_score > 0:
        signal_risks.append(f"Low viability score ({qa_score}%) — validate source completeness")
    warning_risks: List[str] = list(warnings[:2])

    top_risks: List[str] = list(dict.fromkeys(blockers_risks + signal_risks + warning_risks))

    # Gaps from assets and quick assessment
    asset_gaps = _extract_gaps_from_assets(assets or [])
    qa_gaps    = _extract_gaps_from_quick_assessment(qa)
    all_gaps   = qa_gaps + asset_gaps

    manual_areas = _derive_manual_effort_areas(all_gaps)
    decision_queue = _build_decision_queue(all_gaps)

    return {
        "migration_posture":       _POSTURE_MAP.get(status, "Unknown"),
        "confidence_score":        confidence,
        "source_tech":             source_tech,
        "target_tech":             target_tech,
        "detected_techs":          detected_techs,
        "total_assets":            total_assets,
        "migrable_assets":         core_assets,
        "pii_assets":              pii_assets,
        "top_risks":               top_risks[:5],
        "manual_effort_areas":     manual_areas,
        "open_blockers":           blockers,
        "readiness_warnings":      warnings,
        "readiness_next_steps":    next_steps,
        "recommended_next_action": next_action or (next_steps[0] if next_steps else ""),
        "readiness_status":        status,
        "total_gaps":              len(all_gaps),
        "decision_queue":          decision_queue.get("items", []),
        "decision_focus":          decision_queue.get("focus", ""),
        "decision_open_count":     decision_queue.get("open_count", 0),
        "computed_at":             datetime.utcnow().isoformat(),
    }


# ---------------------------------------------------------------------------
# Gaps summary builder
# ---------------------------------------------------------------------------

def build_gaps_summary(
    project: Dict,
    assets: List[Dict],
) -> Dict[str, Any]:
    """
    Build a grouped summary of identified gaps.

    Returns:
        { total, by_severity, by_category, items, computed_at }
    """
    qa = project.get("quick_assessment") or {}
    asset_gaps = _extract_gaps_from_assets(assets or [])
    qa_gaps    = _extract_gaps_from_quick_assessment(qa)
    all_gaps   = qa_gaps + asset_gaps

    grouped = _group_gaps(all_gaps)

    by_severity: Dict[str, int] = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for gap in all_gaps:
        sev = gap.get("severity", "LOW")
        if sev in by_severity:
            by_severity[sev] += 1

    return {
        "total":       len(all_gaps),
        "by_severity": by_severity,
        "by_category": {cat: len(items) for cat, items in grouped.items()},
        "grouped":     grouped,
        "computed_at": datetime.utcnow().isoformat(),
    }


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------

class ExecutiveSummaryService:
    """
    Executive Summary Service — Sprint 2

    Derives business-facing summary and gap groups from project signals.
    """

    def __init__(self, tenant_id: Optional[str] = None, client_id: Optional[str] = None):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.db = SupabasePersistence(tenant_id=tenant_id, client_id=client_id)

    async def get_executive_summary(self, project_id: str) -> Dict[str, Any]:
        project = await self.db.get_project_metadata(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        assets = await self.db.get_project_assets(project_id) or []
        return build_executive_summary(project, assets)

    async def get_gaps_summary(self, project_id: str) -> Dict[str, Any]:
        project = await self.db.get_project_metadata(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")
        assets = await self.db.get_project_assets(project_id) or []
        return build_gaps_summary(project, assets)

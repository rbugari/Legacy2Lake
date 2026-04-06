"""
Understanding Service — Block 3

Builds four explainable artifacts from existing project facts:
  1. functional_map    — what business flows exist and which assets support them
  2. operational_map   — how execution happens: order, dependencies, fragility
  3. recommendation_set — prioritized migration recommendations grounded in evidence
  4. rule_candidate_summary — reusable transformation logic candidates

All outputs are deterministic, confidence-scored, and uncertainty-explicit.
Persists to utm_projects.understanding_payload (JSONB) on demand.

Evidence references follow the form:
  "ev:<evidence_item_id>"   — utm_evidence_items row
  "asset:<object_id>"       — utm_objects row
  "impact:<table_name>"     — utm_table_impacts aggregation
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from collections import defaultdict

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
# Version and schema
# ---------------------------------------------------------------------------

UNDERSTANDING_VERSION = "v1"


def _is_missing_understanding_column_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return (
        "understanding_generated_at" in message
        or "understanding_version" in message
        or "understanding_payload" in message
    )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Functional Map builder
# ---------------------------------------------------------------------------

def _infer_domain(asset_name: str, target_tables: List[str]) -> str:
    """
    Infer a business domain from asset name and targets.
    Heuristic-only — confidence is set accordingly.
    """
    name_lower = (asset_name or "").lower()
    combined = name_lower + " " + " ".join(t.lower() for t in target_tables)

    if any(kw in combined for kw in ("sale", "order", "invoice", "revenue")):
        return "sales"
    if any(kw in combined for kw in ("product", "catalog", "item", "sku")):
        return "product"
    if any(kw in combined for kw in ("customer", "client", "member", "contact")):
        return "customer"
    if any(kw in combined for kw in ("employee", "staff", "hr", "payroll")):
        return "hr"
    if any(kw in combined for kw in ("finance", "account", "ledger", "budget")):
        return "finance"
    if any(kw in combined for kw in ("geography", "region", "territory", "location")):
        return "geography"
    if any(kw in combined for kw in ("date", "time", "calendar", "period")):
        return "time"
    if any(kw in combined for kw in ("stag", "stage", "raw", "landing", "bronze")):
        return "staging"
    return "general"


def _build_functional_map(
    assets: List[Dict],
    impacts: List[Dict],
    evidence_items: List[Dict],
    column_mappings: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    Functional map: groups assets by inferred business domain and exposes
    which datasets each capability loads.
    """
    # Index evidence by asset_id for lookups
    evidence_by_asset: Dict[str, List[str]] = defaultdict(list)
    for ev in evidence_items:
        aid = ev.get("asset_id") or ev.get("object_id")
        if aid:
            evidence_by_asset[str(aid)].append(f"ev:{ev.get('id', ev.get('evidence_id', ''))}")

    # Index impacts by asset_id
    targets_by_asset: Dict[str, List[str]] = defaultdict(list)
    sources_by_asset: Dict[str, List[str]] = defaultdict(list)
    for imp in impacts:
        aid = str(imp.get("asset_id", ""))
        if not aid:
            continue
        full_name = imp.get("full_name", "")
        if imp.get("is_target"):
            targets_by_asset[aid].append(full_name)
        if imp.get("is_source"):
            sources_by_asset[aid].append(full_name)

    mappings_by_asset: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for mapping in column_mappings or []:
        aid = str(mapping.get("asset_id") or mapping.get("object_id") or "")
        if aid:
            mappings_by_asset[aid].append(mapping)

    # Build capabilities grouped by domain
    domains_map: Dict[str, List[Dict]] = defaultdict(list)
    for asset in assets:
        oid = str(asset.get("object_id", ""))
        if not oid:
            continue

        source_name = (
            asset.get("object_name")
            or asset.get("source_name")
            or asset.get("source_path", "")
        )
        target_tables = targets_by_asset.get(oid, [])
        source_tables = sources_by_asset.get(oid, [])
        ev_refs = evidence_by_asset.get(oid, [])
        asset_ref = f"asset:{oid}"

        domain = _infer_domain(source_name, target_tables)

        has_impacts = bool(target_tables or source_tables)
        has_evidence = bool(ev_refs)
        has_mappings = bool(mappings_by_asset.get(oid, []))
        has_structural_evidence = has_impacts or has_mappings

        if has_impacts and has_evidence:
            confidence = 0.82
        elif has_impacts and has_mappings:
            confidence = 0.72
        elif has_impacts:
            confidence = 0.65
        elif has_mappings:
            confidence = 0.58
        elif has_evidence:
            confidence = 0.50
        else:
            confidence = 0.30

        uncertainty: List[str] = []
        if not has_impacts:
            uncertainty.append("no_table_impacts_recorded")
        if not has_evidence and not has_structural_evidence:
            uncertainty.append("no_evidence_linked")
        if domain == "general":
            uncertainty.append("domain_not_inferred_from_name")

        meta = asset.get("metadata") or {}
        source_tech = asset.get("source_tech") or meta.get("source_tech", "unknown")

        domains_map[domain].append({
            "name": source_name,
            "asset_ref": asset_ref,
            "source_tech": source_tech,
            "datasets": sorted(set(target_tables)),
            "reads_from": sorted(set(source_tables)),
            "evidence_refs": ev_refs + [asset_ref],
            "confidence": confidence,
            "uncertainty": uncertainty,
        })

    domains = []
    for domain_name, capabilities in sorted(domains_map.items()):
        domains.append({
            "name": domain_name,
            "capabilities": sorted(capabilities, key=lambda c: c["name"]),
        })

    return {
        "version": UNDERSTANDING_VERSION,
        "generated_at": _now_iso(),
        "domains": domains,
        "total_assets": len(assets),
        "total_domains": len(domains),
    }


# ---------------------------------------------------------------------------
# Operational Map builder
# ---------------------------------------------------------------------------

def _build_operational_map(
    assets: List[Dict],
    impacts: List[Dict],
) -> Dict[str, Any]:
    """
    Operational map: execution flow derived from asset dependencies.

    Uses table impacts to determine which assets are writers and readers,
    then infers execution order (writers before readers of same tables).
    Fragility signals are raised when single assets feed multiple downstream consumers.
    """
    # Map full_name → list of assets that write to it
    writers_of: Dict[str, List[str]] = defaultdict(list)
    # Map full_name → list of assets that read from it
    readers_of: Dict[str, List[str]] = defaultdict(list)
    # asset_id → targets written
    asset_targets: Dict[str, List[str]] = defaultdict(list)
    # asset_id → sources read
    asset_sources: Dict[str, List[str]] = defaultdict(list)

    for imp in impacts:
        aid = str(imp.get("asset_id", ""))
        full_name = imp.get("full_name", "")
        if not aid or not full_name:
            continue
        if imp.get("is_target"):
            writers_of[full_name].append(aid)
            asset_targets[aid].append(full_name)
        if imp.get("is_source"):
            readers_of[full_name].append(aid)
            asset_sources[aid].append(full_name)

    # asset_id → name
    asset_name_idx: Dict[str, str] = {}
    for asset in assets:
        oid = str(asset.get("object_id", ""))
        asset_name_idx[oid] = (
            asset.get("object_name")
            or asset.get("source_name")
            or asset.get("source_path", oid)
        )

    # Build dependency edges: asset A → asset B if A writes a table that B reads
    depends_on: Dict[str, List[str]] = defaultdict(list)
    for table, readers in readers_of.items():
        writers = writers_of.get(table, [])
        for reader in readers:
            for writer in writers:
                if reader != writer and writer not in depends_on[reader]:
                    depends_on[reader].append(writer)

    # Build processes
    processes = []
    for asset in assets:
        oid = str(asset.get("object_id", ""))
        if not oid:
            continue

        meta = asset.get("metadata") or {}
        targets = sorted(set(asset_targets.get(oid, [])))
        sources = sorted(set(asset_sources.get(oid, [])))
        deps = depends_on.get(oid, [])
        dep_names = [asset_name_idx.get(d, d) for d in deps]

        # Fragility signals
        fragility: List[str] = []
        # How many downstream assets depend on this asset's output?
        tables_written = asset_targets.get(oid, [])
        downstream_count = sum(
            len(readers_of.get(t, [])) - 1  # subtract self
            for t in tables_written
        )
        if downstream_count > 3:
            fragility.append("high_downstream_fan_out")
        if not deps and not sources:
            fragility.append("no_upstream_dependency_detected")
        if meta.get("complexity_level", "").upper() == "HIGH":
            fragility.append("high_complexity_asset")

        # Confidence: better when we have impact data
        has_impacts = bool(targets or sources)
        if has_impacts and deps:
            confidence = 0.75
        elif has_impacts:
            confidence = 0.60
        else:
            confidence = 0.35

        uncertainty: List[str] = []
        if not has_impacts:
            uncertainty.append("no_table_impacts_available")
        if not deps and sources:
            uncertainty.append("source_tables_detected_but_no_writer_found")

        schedule_hint = (
            meta.get("schedule_hint")
            or meta.get("cron_expression")
            or "not_configured"
        )
        trigger = meta.get("trigger_type") or ("schedule" if schedule_hint != "not_configured" else "unknown")

        processes.append({
            "id": f"proc:{oid}",
            "name": asset_name_idx.get(oid, oid),
            "asset_ref": f"asset:{oid}",
            "source_tech": asset.get("source_tech") or meta.get("source_tech", "unknown"),
            "trigger": trigger,
            "schedule_hint": schedule_hint,
            "depends_on": [f"proc:{d}" for d in deps],
            "depends_on_names": dep_names,
            "inputs": sources,
            "outputs": targets,
            "fragility_signals": fragility,
            "evidence_refs": [f"asset:{oid}"],
            "confidence": confidence,
            "uncertainty": uncertainty,
        })

    # Infer execution levels (topological BFS)
    all_ids = {p["id"] for p in processes}
    in_degree: Dict[str, int] = {p["id"]: len(p["depends_on"]) for p in processes}
    queue = [pid for pid, deg in in_degree.items() if deg == 0]
    levels: List[List[str]] = []
    visited: set = set()
    while queue:
        levels.append(list(queue))
        visited.update(queue)
        next_queue = []
        for pid in queue:
            # find processes that had pid as dependency
            for p in processes:
                if pid in p["depends_on"] and p["id"] not in visited:
                    in_degree[p["id"]] -= 1
                    if in_degree[p["id"]] == 0:
                        next_queue.append(p["id"])
        queue = list(set(next_queue))

    return {
        "version": UNDERSTANDING_VERSION,
        "generated_at": _now_iso(),
        "processes": sorted(processes, key=lambda p: p["name"]),
        "execution_levels": levels,
        "total_processes": len(processes),
    }


# ---------------------------------------------------------------------------
# Recommendation Set builder
# ---------------------------------------------------------------------------

def _build_recommendation_set(
    assets: List[Dict],
    impacts: List[Dict],
    quick_assessment: Optional[Dict],
    evidence_items: List[Dict],
) -> Dict[str, Any]:
    """
    Prioritized recommendations grounded in project evidence.

    Sources:
    - quick_assessment score/blockers
    - PII flags on assets
    - high-complexity assets
    - assets with no table impacts (blind spots)
    - large fan-in tables (many writers)
    """
    items: List[Dict] = []
    seq = 1

    def _add(
        category: str,
        statement: str,
        rationale: str,
        based_on: List[str],
        impact: str,
        effort: str,
        confidence: float,
        uncertainty: Optional[List[str]] = None,
    ) -> None:
        nonlocal seq
        items.append({
            "id": f"rec:{seq:03d}",
            "category": category,
            "statement": statement,
            "rationale": rationale,
            "based_on": based_on,
            "impact": impact,
            "effort": effort,
            "confidence": confidence,
            "uncertainty": uncertainty or [],
        })
        seq += 1

    # --- QA-derived recommendations ---
    if quick_assessment:
        score = quick_assessment.get("score", 0)
        blockers = quick_assessment.get("blockers") or []
        for blocker in blockers:
            _add(
                category="discovery",
                statement=f"Resolve blocker before proceeding: {blocker}",
                rationale="Blocker detected at initial viability assessment. Continuing without resolution risks wasted effort in later stages.",
                based_on=["quick-assessment"],
                impact="high",
                effort="unknown",
                confidence=0.90,
            )
        if score < 50:
            _add(
                category="migration_strategy",
                statement="Conduct a manual discovery pass before automating any translation.",
                rationale=f"Quick assessment score is {score}/100, indicating insufficient signal for automatic progression.",
                based_on=["quick-assessment"],
                impact="high",
                effort="medium",
                confidence=0.85,
            )

    # --- PII-derived ---
    pii_assets = [a for a in assets if a.get("is_pii")]
    if pii_assets:
        pii_names = [
            a.get("object_name") or a.get("source_name", "unknown")
            for a in pii_assets
        ]
        _add(
            category="compliance",
            statement=f"Apply data masking or tokenization to {len(pii_assets)} PII-flagged asset(s) before generating target code.",
            rationale=f"PII detected in: {', '.join(pii_names[:5])}{'…' if len(pii_names) > 5 else ''}. Target platform pipelines must not expose raw PII.",
            based_on=[f"asset:{a.get('object_id', '')}" for a in pii_assets],
            impact="high",
            effort="medium",
            confidence=0.88,
        )

    # --- High complexity ---
    complex_assets = [
        a for a in assets
        if (a.get("metadata") or {}).get("complexity_level", "").upper() == "HIGH"
    ]
    if complex_assets:
        _add(
            category="human_review",
            statement=f"Schedule human review for {len(complex_assets)} high-complexity asset(s) after code generation.",
            rationale="High cyclomatic complexity indicates business logic that automated translation is unlikely to fully capture.",
            based_on=[f"asset:{a.get('object_id', '')}" for a in complex_assets],
            impact="high",
            effort="medium",
            confidence=0.80,
        )

    # --- Blind spots: assets with no table impacts ---
    impacted_asset_ids = {str(i.get("asset_id", "")) for i in impacts}
    blind_assets = [
        a for a in assets
        if str(a.get("object_id", "")) not in impacted_asset_ids
        and (a.get("type") or "").upper() not in ("LAYOUT", "CONTEXT", "DDL_REF")
    ]
    if blind_assets:
        _add(
            category="discovery",
            statement=f"Run table impact analysis on {len(blind_assets)} asset(s) with no recorded impacts.",
            rationale="Assets without impact records yield no data lineage, blocking downstream documentation and generation.",
            based_on=[f"asset:{a.get('object_id', '')}" for a in blind_assets[:10]],
            impact="medium",
            effort="low",
            confidence=0.78,
            uncertainty=["may_include_schema_only_or_helper_assets"],
        )

    # --- Fan-in tables (many writers) ---
    write_counts: Dict[str, int] = defaultdict(int)
    for imp in impacts:
        if imp.get("is_target"):
            write_counts[imp.get("full_name", "")] += 1
    hot_tables = [(t, c) for t, c in write_counts.items() if c >= 3]
    if hot_tables:
        hot_names = ", ".join(f"{t} ({c})" for t, c in sorted(hot_tables, key=lambda x: -x[1])[:5])
        _add(
            category="architecture",
            statement=f"Review {len(hot_tables)} table(s) with 3+ concurrent writers for race condition potential.",
            rationale=f"High write-fanin detected: {hot_names}. Multiple writers on the same table require sequencing or merge coordination.",
            based_on=[f"impact:{t}" for t, _ in hot_tables[:5]],
            impact="medium",
            effort="medium",
            confidence=0.72,
            uncertainty=["execution_schedule_not_confirmed"],
        )

    # --- Evidence gap ---
    evidenced_asset_ids = {
        str(ev.get("asset_id") or ev.get("object_id", ""))
        for ev in evidence_items
    }
    no_evidence_assets = [
        a for a in assets
        if str(a.get("object_id", "")) not in evidenced_asset_ids
    ]
    if len(no_evidence_assets) > len(assets) * 0.4:
        _add(
            category="documentation",
            statement="Attach supporting evidence (SQL, DDL, or context notes) to assets lacking documentation.",
            rationale=f"{len(no_evidence_assets)} of {len(assets)} asset(s) have no linked evidence. Downstream generation quality depends on documented intent.",
            based_on=["evidence-gap-analysis"],
            impact="medium",
            effort="low",
            confidence=0.75,
        )

    return {
        "version": UNDERSTANDING_VERSION,
        "generated_at": _now_iso(),
        "items": items,
        "total": len(items),
    }


# ---------------------------------------------------------------------------
# Rule Candidate Summary builder
# ---------------------------------------------------------------------------

def _expand_transformation_expr(raw_expr: str, source_column: str, target_column: str) -> str:
    """Convert coarse transformation tokens into richer reusable expressions."""
    token = (raw_expr or "").strip().upper()
    source = source_column or "source"
    target = target_column or source

    if token == "OUTPUT":
        if source.lower() == target.lower():
            return ""
        return f"RENAME({source} -> {target})"
    if token == "DERIVED":
        return f"DERIVED({target} <- {source})"
    if token == "LOOKUP":
        return f"LOOKUP({source} -> {target})"
    if token == "AGGREGATE":
        return f"AGGREGATE({source} -> {target})"
    if token == "RENAME":
        return f"RENAME({source} -> {target})"
    return (raw_expr or "").strip()

def _build_rule_candidates(
    column_mappings: List[Dict],
    assets: List[Dict],
) -> Dict[str, Any]:
    """
    Rule candidates: reusable transformation patterns extracted from column mappings.

    A pattern is a candidate when the same transformation expression appears
    in more than one asset (reuse_scope = 'project') or at least once (reuse_scope = 'asset').
    """
    # Index assets for name lookup
    asset_name_idx: Dict[str, str] = {}
    for asset in assets:
        oid = str(asset.get("object_id", ""))
        asset_name_idx[oid] = (
            asset.get("object_name")
            or asset.get("source_name")
            or asset.get("source_path", oid)
        )

    # Group by transformation expression
    expr_groups: Dict[str, List[Dict]] = defaultdict(list)
    for mapping in column_mappings:
        source_column = mapping.get("source_column") or ""
        target_column = mapping.get("target_column") or ""
        raw_expr = (
            mapping.get("transformation_expr")
            or mapping.get("transformation")
            or mapping.get("transformation_rule")
            or ""
        )
        expr = _expand_transformation_expr(raw_expr, source_column, target_column)
        if not expr or expr.upper() in ("NULL", "NONE", "DIRECT", ""):
            continue
        asset_id = str(mapping.get("asset_id") or mapping.get("object_id") or "")
        expr_groups[expr].append({
            "asset_id": asset_id,
            "source_column": source_column,
            "target_column": target_column,
            "mapping_id": mapping.get("mapping_id") or mapping.get("id") or "",
        })

    candidates: List[Dict] = []
    seq = 1
    for expr, occurrences in expr_groups.items():
        asset_ids_seen = list({o["asset_id"] for o in occurrences if o["asset_id"]})
        asset_names = [asset_name_idx.get(aid, aid) for aid in asset_ids_seen]
        reuse_scope = "project" if len(asset_ids_seen) > 1 else "asset"

        # Infer pattern label from expression
        expr_lower = expr.lower()
        if "round" in expr_lower:
            pattern = "numeric_rounding"
        elif "cast" in expr_lower or "convert" in expr_lower:
            pattern = "type_cast"
        elif "lookup(" in expr_lower:
            pattern = "dimension_lookup"
        elif "aggregate(" in expr_lower:
            pattern = "aggregation_logic"
        elif "rename(" in expr_lower:
            pattern = "column_rename"
        elif "derived(" in expr_lower:
            pattern = "derived_column"
        elif "isnull" in expr_lower or "coalesce" in expr_lower or "ifnull" in expr_lower:
            pattern = "null_coalesce"
        elif "upper" in expr_lower or "lower" in expr_lower:
            pattern = "string_case_normalization"
        elif "trim" in expr_lower or "ltrim" in expr_lower or "rtrim" in expr_lower:
            pattern = "string_trim"
        elif "dateadd" in expr_lower or "datediff" in expr_lower or "getdate" in expr_lower:
            pattern = "date_arithmetic"
        elif "concat" in expr_lower or "+" in expr:
            pattern = "string_concat"
        elif "case" in expr_lower:
            pattern = "conditional_logic"
        else:
            pattern = "custom_expression"

        evidence_refs = [f"asset:{aid}" for aid in asset_ids_seen]
        confidence = 0.85 if reuse_scope == "project" else 0.65

        candidates.append({
            "id": f"rulecand:{seq:03d}",
            "pattern": pattern,
            "sample_expression": expr[:200],
            "observed_in_assets": asset_names,
            "asset_refs": evidence_refs,
            "occurrence_count": len(occurrences),
            "reuse_scope": reuse_scope,
            "evidence_refs": evidence_refs,
            "confidence": confidence,
            "uncertainty": [] if reuse_scope == "project" else ["single_occurrence_no_reuse_confirmed"],
        })
        seq += 1

    # Sort: project-scope first, then by occurrence count desc
    candidates.sort(key=lambda c: (0 if c["reuse_scope"] == "project" else 1, -c["occurrence_count"]))

    return {
        "version": UNDERSTANDING_VERSION,
        "generated_at": _now_iso(),
        "candidates": candidates,
        "total": len(candidates),
        "project_scope_count": sum(1 for c in candidates if c["reuse_scope"] == "project"),
    }


# ---------------------------------------------------------------------------
# Main service
# ---------------------------------------------------------------------------

class UnderstandingService:
    """
    Block 3: Understanding Service.

    Derives the four explainable artifacts from existing DB facts:
      - functional_map
      - operational_map
      - recommendation_set
      - rule_candidate_summary

    Read-only against all source tables.
    Persists result to utm_projects.understanding_payload (JSONB) on request.
    """

    TABLE_PROJECTS = "utm_projects"
    TABLE_OBJECTS = "utm_objects"
    TABLE_IMPACTS = "utm_table_impacts"
    TABLE_EVIDENCE = "utm_evidence_items"
    TABLE_MAPPINGS = "utm_column_mappings"
    _supports_project_understanding_columns: Optional[bool] = None

    def __init__(
        self,
        project_id: str,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
    ):
        self.project_id = project_id
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.db = SupabasePersistence(tenant_id=tenant_id, client_id=client_id)

    # ------------------------------------------------------------------
    # Data fetchers
    # ------------------------------------------------------------------

    def _get_assets(self) -> List[Dict]:
        try:
            res = (
                self.db.client
                .table(self.TABLE_OBJECTS)
                .select("object_id,object_name,source_name,source_path,source_tech,type,metadata,is_pii")
                .eq("project_id", self.project_id)
                .execute()
            )
            return res.data or []
        except Exception as exc:
            logger.warning(f"[Understanding] Could not fetch assets: {exc}", "Understanding")
            return []

    def _get_impacts(self) -> List[Dict]:
        try:
            res = (
                self.db.client
                .table(self.TABLE_IMPACTS)
                .select("asset_id,full_name,operation,is_source,is_target,access_pattern")
                .eq("project_id", self.project_id)
                .execute()
            )
            return res.data or []
        except Exception as exc:
            logger.warning(f"[Understanding] Could not fetch impacts: {exc}", "Understanding")
            return []

    def _get_evidence_items(self) -> List[Dict]:
        try:
            res = (
                self.db.client
                .table(self.TABLE_EVIDENCE)
                .select("evidence_id,asset_id,source_block_type,rationale")
                .eq("project_id", self.project_id)
                .execute()
            )
            normalized: List[Dict[str, Any]] = []
            for row in res.data or []:
                normalized.append({
                    **row,
                    "id": row.get("id") or row.get("evidence_id"),
                    "evidence_type": row.get("evidence_type") or row.get("source_block_type"),
                    "summary": row.get("summary") or row.get("rationale") or row.get("snippet"),
                })
            return normalized
        except Exception as exc:
            logger.warning(f"[Understanding] Could not fetch evidence: {exc}", "Understanding")
            return []

    def _get_column_mappings(self, asset_ids: Optional[List[str]] = None) -> List[Dict]:
        if asset_ids is not None and not asset_ids:
            return []
        try:
            query = (
                self.db.client
                .table(self.TABLE_MAPPINGS)
                .select("id,asset_id,source_column,target_column,transformation_rule")
            )
            if asset_ids is not None:
                query = query.in_("asset_id", asset_ids)

            res = query.execute()
            normalized: List[Dict[str, Any]] = []
            for row in res.data or []:
                normalized.append({
                    **row,
                    "mapping_id": row.get("mapping_id") or row.get("id"),
                    "transformation_expr": row.get("transformation_expr") or row.get("transformation_rule"),
                    "transformation": row.get("transformation") or row.get("transformation_rule"),
                })
            return normalized
        except Exception as exc:
            logger.warning(f"[Understanding] Could not fetch column mappings: {exc}", "Understanding")
            return []

    def _get_quick_assessment(self) -> Optional[Dict]:
        try:
            res = (
                self.db.client
                .table(self.TABLE_PROJECTS)
                .select("quick_assessment")
                .eq("project_id", self.project_id)
                .single()
                .execute()
            )
            row = res.data or {}
            return row.get("quick_assessment")
        except Exception as exc:
            logger.warning(f"[Understanding] Could not fetch quick_assessment: {exc}", "Understanding")
            return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def build_all(self) -> Dict[str, Any]:
        """
        Build all four artifacts and return as a single understanding payload.
        Does NOT persist — call rebuild() to also persist.
        """
        assets = self._get_assets()
        asset_ids = [str(asset.get("object_id")) for asset in assets if asset.get("object_id")]
        impacts = self._get_impacts()
        evidence_items = self._get_evidence_items()
        column_mappings = self._get_column_mappings(asset_ids)
        quick_assessment = self._get_quick_assessment()

        functional_map = _build_functional_map(assets, impacts, evidence_items, column_mappings)
        operational_map = _build_operational_map(assets, impacts)
        recommendation_set = _build_recommendation_set(
            assets, impacts, quick_assessment, evidence_items
        )
        rule_candidates = _build_rule_candidates(column_mappings, assets)

        return {
            "version": UNDERSTANDING_VERSION,
            "generated_at": _now_iso(),
            "project_id": self.project_id,
            "functional_map": functional_map,
            "operational_map": operational_map,
            "recommendation_set": recommendation_set,
            "rule_candidate_summary": rule_candidates,
        }

    async def rebuild(self) -> Dict[str, Any]:
        """
        Build all artifacts and persist to utm_projects.understanding_payload.
        Returns the payload.
        """
        payload = await self.build_all()
        try:
            if self._supports_project_understanding_columns is not False:
                self.db.client.table(self.TABLE_PROJECTS).update(
                    {
                        "understanding_payload": payload,
                        "understanding_generated_at": payload["generated_at"],
                        "understanding_version": UNDERSTANDING_VERSION,
                    }
                ).eq("project_id", self.project_id).execute()
                type(self)._supports_project_understanding_columns = True
                logger.info(
                    f"[Understanding] Persisted understanding payload for project {self.project_id}",
                    "Understanding",
                )
                return payload
        except Exception as exc:
            if _is_missing_understanding_column_error(exc):
                type(self)._supports_project_understanding_columns = False
            else:
                logger.warning(
                    f"[Understanding] Could not persist dedicated understanding columns: {exc}",
                    "Understanding",
                )

        try:
            current = (
                self.db.client
                .table(self.TABLE_PROJECTS)
                .select("settings")
                .eq("project_id", self.project_id)
                .single()
                .execute()
            )
            settings = (current.data or {}).get("settings") or {}
            settings["understanding_payload"] = payload
            settings["understanding_generated_at"] = payload["generated_at"]
            settings["understanding_version"] = UNDERSTANDING_VERSION

            self.db.client.table(self.TABLE_PROJECTS).update(
                {"settings": settings}
            ).eq("project_id", self.project_id).execute()
            logger.info(
                f"[Understanding] Persisted understanding payload in settings fallback for project {self.project_id}",
                "Understanding",
            )
        except Exception as fallback_exc:
            logger.warning(
                f"[Understanding] Could not persist payload in settings fallback (returning in-memory): {fallback_exc}",
                "Understanding",
            )
        return payload

    async def get_functional_map(self) -> Dict[str, Any]:
        """Return functional map only (builds fresh, does not cache)."""
        assets = self._get_assets()
        impacts = self._get_impacts()
        evidence_items = self._get_evidence_items()
        asset_ids = [str(asset.get("object_id")) for asset in assets if asset.get("object_id")]
        column_mappings = self._get_column_mappings(asset_ids)
        return _build_functional_map(assets, impacts, evidence_items, column_mappings)

    async def get_operational_map(self) -> Dict[str, Any]:
        """Return operational map only."""
        assets = self._get_assets()
        impacts = self._get_impacts()
        return _build_operational_map(assets, impacts)

    async def get_recommendation_set(self) -> Dict[str, Any]:
        """Return recommendation set only."""
        assets = self._get_assets()
        impacts = self._get_impacts()
        quick_assessment = self._get_quick_assessment()
        evidence_items = self._get_evidence_items()
        return _build_recommendation_set(assets, impacts, quick_assessment, evidence_items)

    async def get_rule_candidates(self) -> Dict[str, Any]:
        """Return rule candidate summary only."""
        assets = self._get_assets()
        asset_ids = [str(asset.get("object_id")) for asset in assets if asset.get("object_id")]
        column_mappings = self._get_column_mappings(asset_ids)
        return _build_rule_candidates(column_mappings, assets)

    async def get_snapshot(self) -> Dict[str, Any]:
        """
        Return full understanding snapshot (all four artefacts).
        Used by export services and external consumers.
        
        Returns cached understanding if available, otherwise rebuilds.
        """
        try:
            if self._supports_project_understanding_columns is not False:
                result = self.db.client.table(self.TABLE_PROJECTS).select(
                    "understanding_payload, understanding_generated_at"
                ).eq("project_id", self.project_id).single().execute()

                if result.data and result.data.get("understanding_payload"):
                    type(self)._supports_project_understanding_columns = True
                    return result.data["understanding_payload"]
        except Exception as exc:
            if _is_missing_understanding_column_error(exc):
                type(self)._supports_project_understanding_columns = False

        try:
            result = self.db.client.table(self.TABLE_PROJECTS).select(
                "settings"
            ).eq("project_id", self.project_id).single().execute()
            settings = (result.data or {}).get("settings") or {}
            if settings.get("understanding_payload"):
                return settings["understanding_payload"]
        except Exception:
            pass

        # Fall back to rebuild
        return await self.rebuild()

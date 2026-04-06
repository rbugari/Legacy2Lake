"""
Unit tests for the understanding service (Block 3).

Tests are fully deterministic — no DB or network calls.
Each test drives the pure builder functions directly.
"""

import pytest
from apps.api.services.understanding_service import (
    UNDERSTANDING_VERSION,
    _build_functional_map,
    _build_operational_map,
    _build_recommendation_set,
    _build_rule_candidates,
)


# ---------------------------------------------------------------------------
# Fixtures — mirrors demo1 project (SSIS Star Schema DW)
# ---------------------------------------------------------------------------

ASSETS = [
    {
        "object_id": "asset-001",
        "object_name": "pkg_dim_customer",
        "source_name": "pkg_dim_customer.dtsx",
        "source_path": "Triage/pkg_dim_customer.dtsx",
        "source_tech": "SSIS",
        "type": "CORE",
        "metadata": {"complexity_level": "MEDIUM"},
        "is_pii": True,
    },
    {
        "object_id": "asset-002",
        "object_name": "pkg_dim_product",
        "source_name": "pkg_dim_product.dtsx",
        "source_path": "Triage/pkg_dim_product.dtsx",
        "source_tech": "SSIS",
        "type": "CORE",
        "metadata": {"complexity_level": "HIGH"},
        "is_pii": False,
    },
    {
        "object_id": "asset-003",
        "object_name": "pkg_fact_sales",
        "source_name": "pkg_fact_sales.dtsx",
        "source_path": "Triage/pkg_fact_sales.dtsx",
        "source_tech": "SSIS",
        "type": "CORE",
        "metadata": {"complexity_level": "HIGH"},
        "is_pii": False,
    },
    {
        "object_id": "asset-004",
        "object_name": "stg_orders",
        "source_name": "stg_orders.dtsx",
        "source_path": "Triage/stg_orders.dtsx",
        "source_tech": "SSIS",
        "type": "CORE",
        "metadata": {"complexity_level": "LOW"},
        "is_pii": False,
    },
    {
        "object_id": "asset-005",
        "object_name": "create_schema",
        "source_name": "create_schema.sql",
        "source_path": "Triage/create_schema.sql",
        "source_tech": "SQL",
        "type": "SUPPORT",
        "metadata": {},
        "is_pii": False,
    },
]

IMPACTS = [
    # stg_orders writes to stg.orders
    {"asset_id": "asset-004", "full_name": "stg.orders", "operation": "INSERT", "is_target": True, "is_source": False},
    # pkg_fact_sales reads from stg.orders and writes to dbo.fact_sales
    {"asset_id": "asset-003", "full_name": "stg.orders", "operation": "SELECT", "is_target": False, "is_source": True},
    {"asset_id": "asset-003", "full_name": "dbo.fact_sales", "operation": "INSERT", "is_target": True, "is_source": False},
    # pkg_dim_customer reads from raw.customers + writes to dbo.dim_customer
    {"asset_id": "asset-001", "full_name": "raw.customers", "operation": "SELECT", "is_target": False, "is_source": True},
    {"asset_id": "asset-001", "full_name": "dbo.dim_customer", "operation": "INSERT", "is_target": True, "is_source": False},
    # pkg_dim_product writes to dbo.dim_product
    {"asset_id": "asset-002", "full_name": "dbo.dim_product", "operation": "INSERT", "is_target": True, "is_source": False},
]

EVIDENCE_ITEMS = [
    {"id": "ev-001", "asset_id": "asset-001", "evidence_type": "DDL", "summary": "Customer DDL schema"},
    {"id": "ev-002", "asset_id": "asset-002", "evidence_type": "SQL", "summary": "Product staging queries"},
    {"id": "ev-003", "asset_id": "asset-003", "evidence_type": "NOTE", "summary": "Sales load logic"},
]

COLUMN_MAPPINGS = [
    # Pattern: ROUND — appears in 2 assets
    {
        "mapping_id": "map-001",
        "asset_id": "asset-003",
        "source_column": "price",
        "target_column": "sale_price",
        "transformation_expr": "ROUND(amount, 2)",
        "transformation": None,
    },
    {
        "mapping_id": "map-002",
        "asset_id": "asset-002",
        "source_column": "unit_price",
        "target_column": "product_price",
        "transformation_expr": "ROUND(amount, 2)",
        "transformation": None,
    },
    # Pattern: ISNULL — single asset
    {
        "mapping_id": "map-003",
        "asset_id": "asset-001",
        "source_column": "email",
        "target_column": "customer_email",
        "transformation_expr": "ISNULL(email, 'unknown@n/a.com')",
        "transformation": None,
    },
    # Direct — should be excluded
    {
        "mapping_id": "map-004",
        "asset_id": "asset-001",
        "source_column": "first_name",
        "target_column": "first_name",
        "transformation_expr": "DIRECT",
        "transformation": None,
    },
    {
        "mapping_id": "map-005",
        "asset_id": "asset-003",
        "source_column": "qty",
        "target_column": "qty_bucket",
        "transformation_expr": "CASE WHEN qty > 0 THEN 'Y' ELSE 'N' END",
        "transformation": None,
    },
    {
        "mapping_id": "map-006",
        "asset_id": "asset-002",
        "source_column": "name_first",
        "target_column": "full_name",
        "transformation_expr": "CONCAT(name_first, ' ', name_last)",
        "transformation": None,
    },
    {
        "mapping_id": "map-007",
        "asset_id": "asset-004",
        "source_column": "amount",
        "target_column": "amount_decimal",
        "transformation_expr": "CAST(amount AS DECIMAL(18,2))",
        "transformation": None,
    },
]

QUICK_ASSESSMENT_PASSING = {
    "score": 78,
    "semaforo": "green",
    "blockers": [],
    "detected_techs": ["SSIS", "TSQL"],
}

QUICK_ASSESSMENT_BLOCKED = {
    "score": 35,
    "semaforo": "red",
    "blockers": ["Source system access denied", "No DDL available"],
    "detected_techs": ["SSIS"],
}


# ---------------------------------------------------------------------------
# Functional Map tests
# ---------------------------------------------------------------------------

class TestFunctionalMap:

    def test_returns_correct_version(self):
        result = _build_functional_map(ASSETS, IMPACTS, EVIDENCE_ITEMS)
        assert result["version"] == UNDERSTANDING_VERSION

    def test_generated_at_present(self):
        result = _build_functional_map(ASSETS, IMPACTS, EVIDENCE_ITEMS)
        assert "generated_at" in result
        assert result["generated_at"]

    def test_total_assets_count(self):
        result = _build_functional_map(ASSETS, IMPACTS, EVIDENCE_ITEMS)
        assert result["total_assets"] == len(ASSETS)

    def test_domains_is_list(self):
        result = _build_functional_map(ASSETS, IMPACTS, EVIDENCE_ITEMS)
        assert isinstance(result["domains"], list)

    def test_customer_domain_inferred(self):
        result = _build_functional_map(ASSETS, IMPACTS, EVIDENCE_ITEMS)
        domain_names = [d["name"] for d in result["domains"]]
        assert "customer" in domain_names

    def test_sales_domain_inferred(self):
        result = _build_functional_map(ASSETS, IMPACTS, EVIDENCE_ITEMS)
        domain_names = [d["name"] for d in result["domains"]]
        assert "sales" in domain_names

    def test_each_capability_has_confidence(self):
        result = _build_functional_map(ASSETS, IMPACTS, EVIDENCE_ITEMS)
        for domain in result["domains"]:
            for cap in domain["capabilities"]:
                assert "confidence" in cap
                assert 0.0 <= cap["confidence"] <= 1.0

    def test_each_capability_has_uncertainty(self):
        result = _build_functional_map(ASSETS, IMPACTS, EVIDENCE_ITEMS)
        for domain in result["domains"]:
            for cap in domain["capabilities"]:
                assert "uncertainty" in cap
                assert isinstance(cap["uncertainty"], list)

    def test_each_capability_has_evidence_refs(self):
        result = _build_functional_map(ASSETS, IMPACTS, EVIDENCE_ITEMS)
        for domain in result["domains"]:
            for cap in domain["capabilities"]:
                assert "evidence_refs" in cap
                assert isinstance(cap["evidence_refs"], list)

    def test_assets_with_evidence_and_impacts_have_higher_confidence(self):
        result = _build_functional_map(ASSETS, IMPACTS, EVIDENCE_ITEMS)
        # asset-001 has both evidence and impacts → confidence == 0.82
        customer_domain = next((d for d in result["domains"] if d["name"] == "customer"), None)
        assert customer_domain is not None
        cap = next((c for c in customer_domain["capabilities"] if "customer" in c["name"].lower()), None)
        assert cap is not None
        assert cap["confidence"] == 0.82

    def test_empty_assets_returns_empty_domains(self):
        result = _build_functional_map([], [], [])
        assert result["domains"] == []
        assert result["total_assets"] == 0

    def test_datasets_contains_target_tables(self):
        result = _build_functional_map(ASSETS, IMPACTS, EVIDENCE_ITEMS)
        customer_domain = next((d for d in result["domains"] if d["name"] == "customer"), None)
        assert customer_domain is not None
        cap = next((c for c in customer_domain["capabilities"] if "customer" in c["name"].lower()), None)
        assert cap is not None
        assert "dbo.dim_customer" in cap["datasets"]

    def test_reads_from_populated(self):
        result = _build_functional_map(ASSETS, IMPACTS, EVIDENCE_ITEMS)
        customer_domain = next((d for d in result["domains"] if d["name"] == "customer"), None)
        cap = next((c for c in customer_domain["capabilities"] if "customer" in c["name"].lower()), None)
        assert "raw.customers" in cap["reads_from"]

    def test_structural_evidence_does_not_emit_no_evidence_items_linked(self):
        result = _build_functional_map(ASSETS, IMPACTS, [], COLUMN_MAPPINGS)
        for domain in result["domains"]:
            for cap in domain["capabilities"]:
                assert "no_evidence_items_linked" not in cap["uncertainty"]


# ---------------------------------------------------------------------------
# Operational Map tests
# ---------------------------------------------------------------------------

class TestOperationalMap:

    def test_returns_correct_version(self):
        result = _build_operational_map(ASSETS, IMPACTS)
        assert result["version"] == UNDERSTANDING_VERSION

    def test_total_processes_matches_assets(self):
        result = _build_operational_map(ASSETS, IMPACTS)
        assert result["total_processes"] == len(ASSETS)

    def test_each_process_has_id(self):
        result = _build_operational_map(ASSETS, IMPACTS)
        for proc in result["processes"]:
            assert proc["id"].startswith("proc:")

    def test_each_process_has_confidence(self):
        result = _build_operational_map(ASSETS, IMPACTS)
        for proc in result["processes"]:
            assert "confidence" in proc
            assert 0.0 <= proc["confidence"] <= 1.0

    def test_each_process_has_uncertainty(self):
        result = _build_operational_map(ASSETS, IMPACTS)
        for proc in result["processes"]:
            assert "uncertainty" in proc
            assert isinstance(proc["uncertainty"], list)

    def test_each_process_has_fragility_signals(self):
        result = _build_operational_map(ASSETS, IMPACTS)
        for proc in result["processes"]:
            assert "fragility_signals" in proc
            assert isinstance(proc["fragility_signals"], list)

    def test_dependency_inferred_fact_depends_on_stage(self):
        """pkg_fact_sales reads stg.orders which is written by stg_orders → dependency."""
        result = _build_operational_map(ASSETS, IMPACTS)
        fact_proc = next(
            (p for p in result["processes"] if "fact_sales" in p["name"]),
            None,
        )
        assert fact_proc is not None
        assert "proc:asset-004" in fact_proc["depends_on"]

    def test_execution_levels_present_and_non_empty(self):
        result = _build_operational_map(ASSETS, IMPACTS)
        assert "execution_levels" in result
        assert isinstance(result["execution_levels"], list)
        assert len(result["execution_levels"]) > 0

    def test_high_complexity_asset_has_fragility_signal(self):
        result = _build_operational_map(ASSETS, IMPACTS)
        # asset-002 (pkg_dim_product) has HIGH complexity
        product_proc = next(
            (p for p in result["processes"] if "dim_product" in p["name"]),
            None,
        )
        assert product_proc is not None
        assert "high_complexity_asset" in product_proc["fragility_signals"]

    def test_empty_assets_returns_empty_processes(self):
        result = _build_operational_map([], [])
        assert result["processes"] == []
        assert result["total_processes"] == 0


# ---------------------------------------------------------------------------
# Recommendation Set tests
# ---------------------------------------------------------------------------

class TestRecommendationSet:

    def test_returns_correct_version(self):
        result = _build_recommendation_set(ASSETS, IMPACTS, QUICK_ASSESSMENT_PASSING, EVIDENCE_ITEMS)
        assert result["version"] == UNDERSTANDING_VERSION

    def test_total_matches_items_length(self):
        result = _build_recommendation_set(ASSETS, IMPACTS, QUICK_ASSESSMENT_PASSING, EVIDENCE_ITEMS)
        assert result["total"] == len(result["items"])

    def test_each_item_has_required_fields(self):
        result = _build_recommendation_set(ASSETS, IMPACTS, QUICK_ASSESSMENT_PASSING, EVIDENCE_ITEMS)
        required = {"id", "category", "statement", "rationale", "based_on", "impact", "effort", "confidence", "uncertainty"}
        for item in result["items"]:
            assert required <= item.keys(), f"Missing fields in: {item}"

    def test_each_item_confidence_in_range(self):
        result = _build_recommendation_set(ASSETS, IMPACTS, QUICK_ASSESSMENT_PASSING, EVIDENCE_ITEMS)
        for item in result["items"]:
            assert 0.0 <= item["confidence"] <= 1.0

    def test_pii_assets_trigger_compliance_recommendation(self):
        result = _build_recommendation_set(ASSETS, IMPACTS, QUICK_ASSESSMENT_PASSING, EVIDENCE_ITEMS)
        categories = [i["category"] for i in result["items"]]
        assert "compliance" in categories

    def test_blocked_qa_triggers_discovery_recommendations(self):
        result = _build_recommendation_set(ASSETS, IMPACTS, QUICK_ASSESSMENT_BLOCKED, EVIDENCE_ITEMS)
        discovery_items = [i for i in result["items"] if i["category"] == "discovery"]
        assert len(discovery_items) >= 1

    def test_low_qa_score_triggers_migration_strategy_recommendation(self):
        result = _build_recommendation_set(ASSETS, IMPACTS, QUICK_ASSESSMENT_BLOCKED, EVIDENCE_ITEMS)
        strategy_items = [i for i in result["items"] if i["category"] == "migration_strategy"]
        assert len(strategy_items) >= 1

    def test_high_complexity_triggers_human_review_recommendation(self):
        result = _build_recommendation_set(ASSETS, IMPACTS, QUICK_ASSESSMENT_PASSING, EVIDENCE_ITEMS)
        human_items = [i for i in result["items"] if i["category"] == "human_review"]
        assert len(human_items) >= 1

    def test_items_have_ids_with_rec_prefix(self):
        result = _build_recommendation_set(ASSETS, IMPACTS, QUICK_ASSESSMENT_PASSING, EVIDENCE_ITEMS)
        for item in result["items"]:
            assert item["id"].startswith("rec:")

    def test_no_assets_returns_empty_items(self):
        result = _build_recommendation_set([], [], None, [])
        assert result["items"] == []
        assert result["total"] == 0

    def test_uncertainty_is_list_on_all_items(self):
        result = _build_recommendation_set(ASSETS, IMPACTS, QUICK_ASSESSMENT_PASSING, EVIDENCE_ITEMS)
        for item in result["items"]:
            assert isinstance(item["uncertainty"], list)


# ---------------------------------------------------------------------------
# Rule Candidate Summary tests
# ---------------------------------------------------------------------------

class TestRuleCandidates:

    def test_returns_correct_version(self):
        result = _build_rule_candidates(COLUMN_MAPPINGS, ASSETS)
        assert result["version"] == UNDERSTANDING_VERSION

    def test_total_matches_candidates_length(self):
        result = _build_rule_candidates(COLUMN_MAPPINGS, ASSETS)
        assert result["total"] == len(result["candidates"])

    def test_direct_mapping_excluded(self):
        result = _build_rule_candidates(COLUMN_MAPPINGS, ASSETS)
        expressions = [c["sample_expression"] for c in result["candidates"]]
        assert "DIRECT" not in expressions

    def test_round_pattern_detected(self):
        result = _build_rule_candidates(COLUMN_MAPPINGS, ASSETS)
        patterns = [c["pattern"] for c in result["candidates"]]
        assert "numeric_rounding" in patterns

    def test_null_coalesce_pattern_detected(self):
        result = _build_rule_candidates(COLUMN_MAPPINGS, ASSETS)
        patterns = [c["pattern"] for c in result["candidates"]]
        assert "null_coalesce" in patterns

    def test_conditional_logic_pattern_detected(self):
        result = _build_rule_candidates(COLUMN_MAPPINGS, ASSETS)
        patterns = [c["pattern"] for c in result["candidates"]]
        assert "conditional_logic" in patterns

    def test_string_concat_pattern_detected(self):
        result = _build_rule_candidates(COLUMN_MAPPINGS, ASSETS)
        patterns = [c["pattern"] for c in result["candidates"]]
        assert "string_concat" in patterns

    def test_type_cast_pattern_detected(self):
        result = _build_rule_candidates(COLUMN_MAPPINGS, ASSETS)
        patterns = [c["pattern"] for c in result["candidates"]]
        assert "type_cast" in patterns

    def test_project_scope_when_same_expression_in_multiple_assets(self):
        result = _build_rule_candidates(COLUMN_MAPPINGS, ASSETS)
        round_candidate = next(
            (c for c in result["candidates"] if c["pattern"] == "numeric_rounding"),
            None,
        )
        assert round_candidate is not None
        assert round_candidate["reuse_scope"] == "project"

    def test_single_occurrence_is_asset_scope(self):
        result = _build_rule_candidates(COLUMN_MAPPINGS, ASSETS)
        null_candidate = next(
            (c for c in result["candidates"] if c["pattern"] == "null_coalesce"),
            None,
        )
        assert null_candidate is not None
        assert null_candidate["reuse_scope"] == "asset"

    def test_project_scope_has_higher_confidence(self):
        result = _build_rule_candidates(COLUMN_MAPPINGS, ASSETS)
        for c in result["candidates"]:
            if c["reuse_scope"] == "project":
                assert c["confidence"] > 0.8
            else:
                assert c["confidence"] <= 0.8

    def test_each_candidate_has_required_fields(self):
        result = _build_rule_candidates(COLUMN_MAPPINGS, ASSETS)
        required = {"id", "pattern", "sample_expression", "observed_in_assets",
                    "occurrence_count", "reuse_scope", "evidence_refs", "confidence", "uncertainty"}
        for c in result["candidates"]:
            assert required <= c.keys(), f"Missing fields in: {c}"

    def test_ids_have_rulecand_prefix(self):
        result = _build_rule_candidates(COLUMN_MAPPINGS, ASSETS)
        for c in result["candidates"]:
            assert c["id"].startswith("rulecand:")

    def test_project_scope_candidates_listed_first(self):
        result = _build_rule_candidates(COLUMN_MAPPINGS, ASSETS)
        scopes = [c["reuse_scope"] for c in result["candidates"]]
        # All "project" entries should come before "asset" entries
        project_indices = [i for i, s in enumerate(scopes) if s == "project"]
        asset_indices = [i for i, s in enumerate(scopes) if s == "asset"]
        if project_indices and asset_indices:
            assert max(project_indices) < min(asset_indices)

    def test_empty_mappings_returns_empty_candidates(self):
        result = _build_rule_candidates([], ASSETS)
        assert result["candidates"] == []
        assert result["total"] == 0
        assert result["project_scope_count"] == 0

    def test_project_scope_count_field(self):
        result = _build_rule_candidates(COLUMN_MAPPINGS, ASSETS)
        expected = sum(1 for c in result["candidates"] if c["reuse_scope"] == "project")
        assert result["project_scope_count"] == expected

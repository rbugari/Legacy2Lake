"""
Tests for Rule Refinement Service - scoring, ranking, and snapshot creation.
test_rule_refinement_service.py
"""

import pytest
from datetime import datetime
from apps.api.services.rule_refinement_service import RuleRefinementService


class TestRuleRefinementService:
    """Unit tests for rule scoring and refinement."""

    @pytest.fixture
    def svc(self):
        return RuleRefinementService(tenant_id="test-tenant", client_id="test-client")

    @pytest.fixture
    def sample_candidates(self):
        return [
            {
                "id": "rule-1",
                "type": "simple",
                "assets_affected": ["table1", "table2"],
                "processes_affected": ["proc-a", "proc-b"],
                "pattern_type": "regex",
                "confidence": 0.95,
                "evidence": [
                    {"type": "code_pattern", "description": "Found in 3 procedures"}
                ],
                "preferred_impl": "sql",
                "dependencies": ["rule-2"],
                "historical_precedent": True,
                "blockers": [],
            },
            {
                "id": "rule-2",
                "type": "conditional",
                "assets_affected": ["table3"],
                "processes_affected": ["proc-c"],
                "pattern_type": "semantic",
                "confidence": 0.75,
                "evidence": [
                    {"type": "business_rule", "description": "From requirements doc"}
                ],
                "preferred_impl": "pyspark",
                "dependencies": [],
                "historical_precedent": False,
                "blockers": ["missing_data_source"],
            },
            {
                "id": "rule-3",
                "type": "recursive",
                "assets_affected": ["table4"],
                "processes_affected": ["proc-d"],
                "pattern_type": "structural",
                "confidence": 0.6,
                "evidence": [],
                "preferred_impl": "python",
                "dependencies": ["rule-1", "rule-2"],
                "historical_precedent": False,
                "blockers": [],
            },
        ]

    @pytest.fixture
    def operational_context(self):
        return {
            "orchestration": "dag",
            "processes": [
                {"id": "proc-a", "type": "etl"},
                {"id": "proc-b", "type": "sync"},
            ],
            "dependencies": [{"from": "proc-a", "to": "proc-b"}],
        }

    @pytest.fixture
    def project_scope(self):
        return {
            "object_count": 50,
            "stage": "UNDERSTANDING",
        }

    def test_score_rule_candidates_returns_scored_list(
        self, svc, sample_candidates, operational_context, project_scope
    ):
        """Verify scoring produces ranked candidates with composite scores."""
        result = svc.score_rule_candidates(
            sample_candidates, operational_context, project_scope
        )

        assert len(result) == 3
        assert "composite_score" in result[0]
        assert "reusability_score" in result[0]
        assert "complexity_score" in result[0]
        assert "confidence_score" in result[0]
        assert "applicability" in result[0]
        assert "recommendation" in result[0]

    def test_scoring_sorts_by_composite_score(
        self, svc, sample_candidates, operational_context, project_scope
    ):
        """Verify candidates are sorted by composite score descending."""
        result = svc.score_rule_candidates(
            sample_candidates, operational_context, project_scope
        )

        scores = [r["composite_score"] for r in result]
        assert scores == sorted(scores, reverse=True)

    def test_reusability_scoring_prefers_multiple_assets(self, svc):
        """Rules affecting multiple assets should score higher."""
        candidate_local = {
            "id": "local",
            "assets_affected": ["table1"],
            "processes_affected": ["proc1"],
            "pattern_type": "regex",
        }
        candidate_global = {
            "id": "global",
            "assets_affected": ["table1", "table2", "table3"],
            "processes_affected": ["proc1", "proc2"],
            "pattern_type": "regex",
        }

        score_local = svc._calculate_reusability(
            candidate_local, {}, {"object_count": 10}
        )
        score_global = svc._calculate_reusability(
            candidate_global, {}, {"object_count": 10}
        )

        assert score_global > score_local

    def test_complexity_scoring_penalizes_dependencies(self, svc):
        """Candidates with more dependencies should score higher complexity."""
        simple = {"type": "simple", "preferred_impl": "sql", "dependencies": []}
        complex_rule = {
            "type": "recursive",
            "preferred_impl": "python",
            "dependencies": ["a", "b", "c", "d"],
        }

        score_simple = svc._calculate_complexity(simple)
        score_complex = svc._calculate_complexity(complex_rule)

        assert score_complex > score_simple

    def test_applicability_classification_local_vs_global(self, svc):
        """Rules affecting single asset/process are LOCAL; multi are GLOBAL."""
        local = {
            "assets_affected": ["table1"],
            "processes_affected": ["proc1"],
        }
        global_rule = {
            "assets_affected": ["table1", "table2"],
            "processes_affected": ["proc1", "proc2"],
        }

        assert svc._classify_applicability(local, {}) == "LOCAL"
        assert svc._classify_applicability(global_rule, {}) == "GLOBAL"

    def test_priority_from_score_mapping(self, svc):
        """Score ranges should map to priority levels."""
        assert svc._priority_from_score(0.9) == "CRITICAL"
        assert svc._priority_from_score(0.7) == "HIGH"
        assert svc._priority_from_score(0.5) == "MEDIUM"
        assert svc._priority_from_score(0.2) == "LOW"

    def test_effort_estimate_t_shirt_sizing(self, svc):
        """Effort estimates should return XS, S, M, L sizing."""
        xs_rule = {
            "type": "simple",
            "dependencies": ["a"],
        }
        s_rule = {
            "type": "conditional",
            "dependencies": ["a", "b"],
        }
        l_rule = {
            "type": "recursive",
            "dependencies": ["a", "b", "c", "d", "e", "f"],
        }

        assert svc._effort_estimate(xs_rule) == "XS"
        assert svc._effort_estimate(s_rule) == "S"
        assert svc._effort_estimate(l_rule) == "L"

    def test_materialize_recommendation_includes_action_priority_effort(self, svc):
        """Materialized recommendation should have concrete action plan."""
        candidate = {
            "id": "r1",
            "type": "simple",
            "preferred_impl": "sql",
            "composite_score": 0.85,
            "dependencies": ["r2"],
            "blockers": [],
            "evidence": [
                {"type": "pattern", "description": "Found in ETL pipeline"}
            ],
        }

        rec = svc._materialize_recommendation(candidate)

        assert "action" in rec
        assert rec["action"].startswith("Implement")
        assert rec["priority"] == "CRITICAL"
        assert rec["effort_estimate"] in ["XS", "S", "M", "L"]
        assert "evidence_summary" in rec

    def test_create_knowledge_package_snapshot_structure(
        self, svc, sample_candidates, operational_context, project_scope
    ):
        """Knowledge package should contain all expected fields."""
        understanding = {
            "functional_map": {"assets": []},
            "operational_map": operational_context,
            "recommendations": [],
            "rule_candidates": {"candidates": sample_candidates},
        }

        refined = svc.score_rule_candidates(
            sample_candidates, operational_context, project_scope
        )

        snapshot = svc.create_knowledge_package_snapshot(
            project_id="proj-1",
            understanding=understanding,
            refined_rules=refined,
            metadata={"project_name": "Test Project"},
        )

        assert "metadata" in snapshot
        assert snapshot["metadata"]["project_id"] == "proj-1"
        assert snapshot["metadata"]["package_version"] == "v1"
        assert "snapshot_id" in snapshot["metadata"]
        assert "created_at" in snapshot["metadata"]
        assert "understanding" in snapshot
        assert "refined_rules" in snapshot
        assert "package_hash" in snapshot

    def test_snapshot_id_generation_is_deterministic(self, svc):
        """Snapshot IDs should be unique per project."""
        ids = [svc._generate_snapshot_id("proj-1") for _ in range(3)]
        # All different
        assert len(set(ids)) == 3
        # All 12 chars
        assert all(len(id) == 12 for id in ids)

    def test_package_hash_detects_content_changes(self, svc):
        """Package hash should change when content changes."""
        rules1 = [{"id": "r1", "confidence": 0.9}]
        rules2 = [{"id": "r1", "confidence": 0.8}]

        hash1 = svc._compute_package_hash(
            {"functional_map": {}}, rules1
        )
        hash2 = svc._compute_package_hash(
            {"functional_map": {}}, rules2
        )

        assert hash1 != hash2

    def test_package_hash_detects_content_changes(self, svc):
        """Package hash should change when content changes."""
        rules1 = [{"id": "r1", "composite_score": 0.9, "type": "simple"}]
        rules2 = [{"id": "r1", "composite_score": 0.8, "type": "simple"}]

        hash1 = svc._compute_package_hash(
            {"functional_map": {}}, rules1
        )
        hash2 = svc._compute_package_hash(
            {"functional_map": {}}, rules2
        )

        assert hash1 != hash2

    def test_rule_refinement_with_minimal_input(self, svc):
        """Should handle candidates with missing optional fields."""
        minimal = [
            {
                "id": "r1",
                "type": "simple",
            }
        ]

        result = svc.score_rule_candidates(minimal, {}, {})

        assert len(result) == 1
        assert result[0]["composite_score"] >= 0.0
        assert result[0]["composite_score"] <= 1.0

    def test_score_calculation_formula_validation(self, svc):
        """Verify composite score = reusability * (1-complexity) * confidence."""
        candidate = {
            "id": "test",
            "type": "simple",
            "assets_affected": ["a", "b", "c"],
            "processes_affected": ["p1", "p2"],
            "pattern_type": "regex",
            "confidence": 0.8,
            "preferred_impl": "sql",
            "dependencies": [],
            "historical_precedent": True,
        }

        scored = svc.score_rule_candidates(
            [candidate], {}, {}
        )[0]

        expected = (
            scored["reusability_score"]
            * (1 - scored["complexity_score"])
            * scored["confidence_score"]
        )
        assert abs(scored["composite_score"] - expected) < 0.01


class TestRuleRefinementIntegration:
    """Integration tests for full refinement + snapshot workflow."""

    @pytest.fixture
    def svc(self):
        return RuleRefinementService(tenant_id="test", client_id="test")

    def test_full_refinement_pipeline(self, svc):
        """End-to-end: candidates → scoring → snapshot."""
        candidates = [
            {
                "id": f"rule-{i}",
                "type": "simple" if i % 2 == 0 else "conditional",
                "assets_affected": ["t1", "t2"] if i % 2 == 0 else ["t3"],
                "processes_affected": ["p1", "p2"] if i % 2 == 0 else ["p2"],
                "pattern_type": "regex",
                "confidence": 0.5 + 0.1 * i,
                "evidence": [],
                "preferred_impl": "sql",
                "dependencies": [],
                "historical_precedent": False,
                "blockers": [],
            }
            for i in range(5)
        ]

        understanding = {
            "functional_map": {},
            "operational_map": {},
            "recommendations": [],
            "rule_candidates": {"candidates": candidates},
        }

        # Refine
        refined = svc.score_rule_candidates(candidates, {}, {})

        # Create snapshot
        snapshot = svc.create_knowledge_package_snapshot(
            "proj-1", understanding, refined
        )

        assert snapshot["metadata"]["package_version"] == "v1"
        assert len(snapshot["refined_rules"]) == min(5, 20)
        assert snapshot["package_hash"] is not None

    def test_snapshot_with_many_rules_limits_to_top_20(self, svc):
        """Snapshots should limit refined rules to top 20."""
        many_rules = [
            {
                "id": f"rule-{i}",
                "type": "simple",
                "assets_affected": ["t1"],
                "processes_affected": ["p1"],
                "pattern_type": "regex",
                "confidence": 0.5 + (i % 10) * 0.01,
                "evidence": [],
                "preferred_impl": "sql",
                "dependencies": [],
                "historical_precedent": False,
                "blockers": [],
            }
            for i in range(50)
        ]

        refined = svc.score_rule_candidates(many_rules, {}, {})
        snapshot = svc.create_knowledge_package_snapshot(
            "proj-1", {}, refined
        )

        assert len(snapshot["refined_rules"]) == 20

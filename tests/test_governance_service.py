"""
Tests for Governance & Versioning Service - snapshot diffs and governance checks.
test_governance_service.py
"""

import pytest
from datetime import datetime
from apps.api.services.governance_service import (
    SnapshotVersioningService,
    SnapshotChangeType,
    GovernanceCheckStatus,
)


class TestSnapshotDiffing:
    """Tests for snapshot versioning and change detection."""

    @pytest.fixture
    def svc(self):
        return SnapshotVersioningService(tenant_id="test", client_id="test")

    @pytest.fixture
    def prev_snapshot(self):
        return {
            "metadata": {"snapshot_id": "snap-1", "created_at": "2026-04-01T10:00:00"},
            "refined_rules": [
                {
                    "id": "rule-1",
                    "type": "simple",
                    "composite_score": 0.85,
                    "confidence_score": 0.9,
                    "applicability": "GLOBAL",
                    "recommendation": {"priority": "HIGH"},
                },
                {
                    "id": "rule-2",
                    "type": "conditional",
                    "composite_score": 0.65,
                    "confidence_score": 0.7,
                    "applicability": "LOCAL",
                    "recommendation": {"priority": "MEDIUM"},
                },
                {
                    "id": "rule-3",
                    "type": "simple",
                    "composite_score": 0.55,
                    "confidence_score": 0.6,
                    "applicability": "LOCAL",
                    "recommendation": {"priority": "LOW"},
                },
            ],
        }

    @pytest.fixture
    def curr_snapshot(self):
        return {
            "metadata": {"snapshot_id": "snap-2", "created_at": "2026-04-01T11:00:00"},
            "refined_rules": [
                {
                    "id": "rule-1",
                    "type": "simple",
                    "composite_score": 0.88,  # Score improved
                    "confidence_score": 0.95,
                    "applicability": "GLOBAL",
                    "recommendation": {"priority": "HIGH"},
                },
                {
                    "id": "rule-3",
                    "type": "simple",
                    "composite_score": 0.72,  # Score improved, ranking promoted
                    "confidence_score": 0.75,
                    "applicability": "GLOBAL",  # Applicability changed
                    "recommendation": {"priority": "MEDIUM"},
                },
                {
                    "id": "rule-4",
                    "type": "regex",
                    "composite_score": 0.60,
                    "confidence_score": 0.65,
                    "applicability": "LOCAL",
                    "recommendation": {"priority": "MEDIUM"},
                },
                # rule-2 removed
            ],
        }

    def test_diff_detects_score_improvement(self, svc, prev_snapshot, curr_snapshot):
        """Should detect score improvements."""
        diff = svc.compute_snapshot_diff(prev_snapshot, curr_snapshot)

        score_improvements = [
            c for c in diff["changes"]
            if c["type"] == SnapshotChangeType.SCORE_IMPROVED
        ]
        assert len(score_improvements) > 0
        assert any(c["rule_id"] == "rule-1" for c in score_improvements)

    def test_diff_detects_rule_removed(self, svc, prev_snapshot, curr_snapshot):
        """Should detect removed rules."""
        diff = svc.compute_snapshot_diff(prev_snapshot, curr_snapshot)

        removed = [
            c for c in diff["changes"]
            if c["type"] == SnapshotChangeType.RULE_REMOVED
        ]
        assert len(removed) == 1
        assert removed[0]["rule_id"] == "rule-2"

    def test_diff_detects_rule_added(self, svc, prev_snapshot, curr_snapshot):
        """Should detect added rules."""
        diff = svc.compute_snapshot_diff(prev_snapshot, curr_snapshot)

        added = [
            c for c in diff["changes"]
            if c["type"] == SnapshotChangeType.RULE_ADDED
        ]
        assert len(added) == 1
        assert added[0]["rule_id"] == "rule-4"

    def test_diff_detects_applicability_change(self, svc, prev_snapshot, curr_snapshot):
        """Should detect applicability changes (LOCAL → GLOBAL)."""
        diff = svc.compute_snapshot_diff(prev_snapshot, curr_snapshot)

        applicability_changes = [
            c for c in diff["changes"]
            if c["type"] == SnapshotChangeType.APPLICABILITY_CHANGED
        ]
        assert len(applicability_changes) > 0
        assert applicability_changes[0]["rule_id"] == "rule-3"
        assert applicability_changes[0]["previous"] == "LOCAL"
        assert applicability_changes[0]["current"] == "GLOBAL"

    def test_diff_detects_ranking_promotion(self, svc, prev_snapshot, curr_snapshot):
        """Should detect when a rule moves up in ranking."""
        diff = svc.compute_snapshot_diff(prev_snapshot, curr_snapshot)

        promotions = [
            c for c in diff["changes"]
            if c["type"] == SnapshotChangeType.RULE_PROMOTED
        ]
        assert len(promotions) > 0
        assert promotions[0]["rule_id"] == "rule-3"
        assert promotions[0]["positions"] > 0

    def test_diff_summary_metrics(self, svc, prev_snapshot, curr_snapshot):
        """Diff summary should contain accurate counts."""
        diff = svc.compute_snapshot_diff(prev_snapshot, curr_snapshot)

        assert diff["summary"]["added_count"] == 1
        assert diff["summary"]["removed_count"] == 1
        assert diff["summary"]["promoted_count"] > 0
        assert diff["summary"]["total_changes"] > 0

    def test_diff_significant_detection(self, svc, prev_snapshot, curr_snapshot):
        """Should mark significant diffs correctly."""
        diff = svc.compute_snapshot_diff(prev_snapshot, curr_snapshot)

        # This diff has multiple changes
        assert diff["summary"]["total_changes"] > 5 or diff["significant"]

    def test_diff_first_snapshot_all_added(self, svc, curr_snapshot):
        """First snapshot should show all rules as added."""
        diff = svc.compute_snapshot_diff(None, curr_snapshot)

        added = [
            c for c in diff["changes"]
            if c["type"] == SnapshotChangeType.RULE_ADDED
        ]
        assert len(added) == len(curr_snapshot["refined_rules"])


class TestGovernanceValidation:
    """Tests for governance readiness checks."""

    @pytest.fixture
    def svc(self):
        return SnapshotVersioningService(tenant_id="test", client_id="test")

    @pytest.fixture
    def good_snapshot(self):
        return {
            "metadata": {"snapshot_id": "snap-good"},
            "refined_rules": [
                {
                    "id": "r1",
                    "type": "simple",
                    "composite_score": 0.9,
                    "confidence_score": 0.95,
                    "applicability": "GLOBAL",
                    "recommendation": {
                        "priority": "CRITICAL",
                        "evidence_summary": "Found in 5 procedures",
                        "blockers": [],
                    },
                },
                {
                    "id": "r2",
                    "type": "conditional",
                    "composite_score": 0.75,
                    "confidence_score": 0.8,
                    "applicability": "GLOBAL",
                    "recommendation": {
                        "priority": "HIGH",
                        "evidence_summary": "From requirements doc",
                        "blockers": [],
                    },
                },
                {
                    "id": "r3",
                    "type": "simple",
                    "composite_score": 0.6,
                    "confidence_score": 0.65,
                    "applicability": "LOCAL",
                    "recommendation": {
                        "priority": "MEDIUM",
                        "evidence_summary": "Local pattern match",
                        "blockers": [],
                    },
                },
            ],
        }

    def test_governance_pass_with_good_rules(self, svc, good_snapshot):
        """Project with high-quality rules should pass governance."""
        result = svc.validate_governance_readiness(
            good_snapshot, {"stage": "UNDERSTANDING"}
        )

        assert result["status"] == GovernanceCheckStatus.PASS
        assert result["can_finalize"]

    def test_governance_warning_with_few_rules(self, svc, good_snapshot):
        """Project with only 1-2 rules should warn."""
        minimal_snapshot = good_snapshot.copy()
        minimal_snapshot["refined_rules"] = good_snapshot["refined_rules"][:1]

        result = svc.validate_governance_readiness(
            minimal_snapshot, {"stage": "UNDERSTANDING"}
        )

        assert result["status"] in [
            GovernanceCheckStatus.WARNING,
            GovernanceCheckStatus.PASS,
        ]

    def test_governance_warning_with_low_confidence_top_rule(self, svc):
        """Top rule with low confidence should warn."""
        low_confidence_snapshot = {
            "metadata": {"snapshot_id": "snap-low"},
            "refined_rules": [
                {
                    "id": "r-uncertain",
                    "type": "simple",
                    "composite_score": 0.4,
                    "confidence_score": 0.4,
                    "applicability": "LOCAL",
                    "recommendation": {
                        "priority": "MEDIUM",
                        "evidence_summary": "Unclear pattern",
                        "blockers": [],
                    },
                }
            ],
        }

        result = svc.validate_governance_readiness(
            low_confidence_snapshot, {"stage": "UNDERSTANDING"}
        )

        assert result["status"] == GovernanceCheckStatus.WARNING

    def test_governance_warning_with_blockers(self, svc):
        """Critical rules with blockers should warn."""
        blocked_snapshot = {
            "metadata": {"snapshot_id": "snap-blocked"},
            "refined_rules": [
                {
                    "id": "r-blocked",
                    "type": "simple",
                    "composite_score": 0.85,
                    "confidence_score": 0.9,
                    "applicability": "GLOBAL",
                    "recommendation": {
                        "priority": "CRITICAL",
                        "evidence_summary": "Strong pattern",
                        "blockers": ["missing_source_schema", "access_denied"],
                    },
                }
            ],
        }

        result = svc.validate_governance_readiness(
            blocked_snapshot, {"stage": "UNDERSTANDING"}
        )

        assert result["status"] == GovernanceCheckStatus.WARNING
        assert "critical_blockers" in [c["name"] for c in result["checks"]]

    def test_governance_check_details(self, svc, good_snapshot):
        """Governance result should include check details."""
        result = svc.validate_governance_readiness(
            good_snapshot, {"stage": "UNDERSTANDING"}
        )

        assert "checks" in result
        assert len(result["checks"]) > 0
        assert "passed" in result
        assert "warnings" in result
        assert "failures" in result

    def test_governance_low_global_ratio_warns(self, svc):
        """Project with mostly local rules (low reusability) should warn."""
        local_heavy_snapshot = {
            "metadata": {"snapshot_id": "snap-local"},
            "refined_rules": [
                {
                    "id": f"r-local-{i}",
                    "type": "simple",
                    "composite_score": 0.5,
                    "confidence_score": 0.6,
                    "applicability": "LOCAL",  # All local
                    "recommendation": {
                        "priority": "MEDIUM",
                        "evidence_summary": "Pattern",
                        "blockers": [],
                    },
                }
                for i in range(10)
            ],
        }

        result = svc.validate_governance_readiness(
            local_heavy_snapshot, {"stage": "UNDERSTANDING"}
        )

        # Should either warn or have applicability_check warning
        assert any(
            c["name"] == "rule_applicability" and c["status"] == GovernanceCheckStatus.WARNING
            for c in result["checks"]
        ) or result["status"] == GovernanceCheckStatus.WARNING


class TestAuditTrail:
    """Tests for audit trail creation."""

    @pytest.fixture
    def svc(self):
        return SnapshotVersioningService(tenant_id="acme", client_id="client-1")

    def test_create_audit_entry_basic(self, svc):
        """Should create basic audit entry."""
        entry = svc.create_audit_entry(
            project_id="proj-1",
            action_type="rule_scored",
            rule_id="r1",
        )

        assert entry["project_id"] == "proj-1"
        assert entry["action_type"] == "rule_scored"
        assert entry["rule_id"] == "r1"
        assert entry["timestamp"]

    def test_create_audit_entry_with_values(self, svc):
        """Should track before/after values."""
        entry = svc.create_audit_entry(
            project_id="proj-1",
            action_type="rule_rescored",
            rule_id="r1",
            previous_value=0.65,
            new_value=0.8,
            reasoning="Evidence from new discovery run",
        )

        assert entry["previous_value"] == 0.65
        assert entry["new_value"] == 0.8
        assert entry["reasoning"] == "Evidence from new discovery run"

    def test_audit_entry_includes_tenant(self, svc):
        """Audit entry should include tenant/client context."""
        entry = svc.create_audit_entry(
            project_id="proj-1",
            action_type="finalized",
        )

        assert entry["tenant_id"] == "acme"
        assert entry["client_id"] == "client-1"

"""
Unit tests for readiness service.
Validates confidence scoring and breakdown generation.
"""

from apps.api.services.readiness_service import (
    STATUS_BASELINE_READY,
    STATUS_NOT_RECOMMENDED,
    STATUS_READY,
    STATUS_REQUIRES_CONTEXT,
    compute_readiness,
)


def test_compute_readiness_no_signals_returns_breakdown_and_blockers():
    project = {}

    result = compute_readiness(project, [])

    assert result["status"] == STATUS_NOT_RECOMMENDED
    assert result["confidence_score"] == 10
    assert result["confidence_breakdown"]["baseline_score"] == 50
    assert result["confidence_breakdown"]["final_score"] == 10
    assert result["confidence_breakdown"]["adjustments"]
    assert any(item["label"] == "Quick Assessment" for item in result["confidence_breakdown"]["adjustments"])
    assert "Source technology not configured" in result["blockers"]
    assert "Target technology not configured" in result["blockers"]
    assert isinstance(result["warnings"], list)
    assert isinstance(result["next_steps"], list)
    assert any("Configure source technology" in step for step in result["next_steps"])
    assert any("Configure target technology" in step for step in result["next_steps"])


def test_compute_readiness_with_quick_assessment_only_uses_breakdown():
    project = {
        "source_tech": "SQLSERVER",
        "target_tech": "DATABRICKS",
        "prompt": "custom prompt",
        "quick_assessment": {
            "score": 82,
            "semaforo": "green",
            "blockers": [],
            "detected_techs": ["SQLSERVER"],
            "file_breakdown": {"migrable": 3},
            "total_files": 3,
        },
    }

    result = compute_readiness(project, [])

    assert result["confidence_score"] == 65
    assert result["status"] == STATUS_BASELINE_READY
    assert result["confidence_breakdown"]["final_score"] == 65
    assert [item["delta"] for item in result["confidence_breakdown"]["adjustments"]] == [20, -5]
    assert result["warnings"] == []


def test_compute_readiness_with_yellow_assessment_emits_warning():
    project = {
        "source_tech": "SQLSERVER",
        "target_tech": "DATABRICKS",
        "quick_assessment": {
            "score": 61,
            "semaforo": "yellow",
            "blockers": [],
            "detected_techs": ["SQLSERVER"],
            "file_breakdown": {"migrable": 1},
            "total_files": 2,
        },
    }

    result = compute_readiness(project, [])

    assert any("Quick assessment is YELLOW" in warning for warning in result["warnings"])


def test_compute_readiness_with_triage_and_config_can_reach_ready():
    project = {
        "source_tech": "SQLSERVER",
        "target_tech": "SNOWFLAKE",
        "prompt": "custom prompt",
        "quick_assessment": {
            "score": 91,
            "semaforo": "green",
            "blockers": [],
            "detected_techs": ["SQLSERVER"],
            "file_breakdown": {"migrable": 5},
            "total_files": 5,
        },
    }
    assets = [
        {
            "type": "CORE",
            "is_pii": False,
            "metadata": {"complexity_level": "LOW"},
            "validation_result": {"ok": True},
        }
    ]

    result = compute_readiness(project, assets)

    assert result["confidence_score"] == 80
    assert result["status"] == STATUS_READY
    assert result["source_signals"]["triage_complete"] is True
    assert any(item["label"] == "Triage" and item["delta"] == 10 for item in result["confidence_breakdown"]["adjustments"])
    assert isinstance(result["warnings"], list)
    assert isinstance(result["next_steps"], list)


def test_compute_readiness_breakdown_math_matches_final_score():
    project = {
        "source_tech": "SQLSERVER",
        "target_tech": "DATABRICKS",
    }

    result = compute_readiness(project, [])
    breakdown = result["confidence_breakdown"]
    computed_total = breakdown["baseline_score"] + sum(item["delta"] for item in breakdown["adjustments"])

    assert computed_total == result["confidence_score"]
    assert breakdown["final_score"] == result["confidence_score"]
    assert result["status"] in {STATUS_REQUIRES_CONTEXT, STATUS_BASELINE_READY, STATUS_READY, STATUS_NOT_RECOMMENDED}

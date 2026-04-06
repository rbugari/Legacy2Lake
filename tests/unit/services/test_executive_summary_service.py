"""
Unit tests for the executive summary service.

Validates business-facing summary generation and gap grouping from technical signals.
"""

import asyncio

from apps.api.services.executive_summary_service import (
    ExecutiveSummaryService,
    build_executive_summary,
    build_gaps_summary,
)


def test_build_executive_summary_uses_readiness_and_signals():
    project = {
        "source_tech": "SQLSERVER",
        "target_tech": "SNOWFLAKE",
        "quick_assessment": {
            "score": 42,
            "blockers": ["Missing access to source system"],
            "detected_techs": ["SQLSERVER", "TSQL"],
        },
        "readiness_summary": {
            "status": "READY",
            "confidence_score": 84,
            "recommended_next_action": "Proceed to drafting",
            "blockers": ["Missing access to source system"],
            "warnings": ["Using default migration prompt"],
            "next_steps": ["Create project-specific prompt"],
        },
    }
    assets = [
        {
            "type": "CORE",
            "is_pii": True,
            "metadata": {"complexity_level": "HIGH", "mismatch_count": 1},
            "validation_result": {"violations": ["rule-1", "rule-2"]},
            "object_id": "asset-1",
            "object_name": "CustomerLoad",
        },
        {
            "type": "SUPPORT",
            "is_pii": False,
            "metadata": {"complexity_level": "LOW"},
            "validation_result": None,
            "object_id": "asset-2",
            "object_name": "Helper",
        },
    ]

    result = build_executive_summary(project, assets)

    assert result["migration_posture"] == "Strong — Automation Recommended"
    assert result["confidence_score"] == 84
    assert result["source_tech"] == "SQLSERVER"
    assert result["target_tech"] == "SNOWFLAKE"
    assert result["total_assets"] == 2
    assert result["migrable_assets"] == 1
    assert result["pii_assets"] == 1
    assert result["readiness_status"] == "READY"
    assert result["recommended_next_action"] == "Proceed to drafting"
    assert result["open_blockers"] == ["Missing access to source system"]
    assert result["readiness_warnings"] == ["Using default migration prompt"]
    assert result["readiness_next_steps"] == ["Create project-specific prompt"]
    assert result["total_gaps"] == 5
    assert result["decision_open_count"] == 5
    assert len(result["decision_queue"]) == 4
    assert result["decision_queue"][0]["severity"] == "CRITICAL"
    assert "before the next handoff" in result["decision_focus"]
    assert any("Compliance" in area for area in result["manual_effort_areas"])
    assert any("Business rules" in area for area in result["manual_effort_areas"])
    assert any("Schema alignment" in area for area in result["manual_effort_areas"])
    assert any("Missing access" in risk for risk in result["top_risks"])
    assert any("default migration prompt" in risk for risk in result["top_risks"])
    # Blockers must appear before warnings in top_risks (criticality ordering)
    blocker_idx = next(i for i, r in enumerate(result["top_risks"]) if "Missing access" in r)
    warning_idx = next(i for i, r in enumerate(result["top_risks"]) if "default migration prompt" in r)
    assert blocker_idx < warning_idx, "Blockers must precede warnings in top_risks"


def test_build_executive_summary_handles_projects_without_gaps():
    project = {
        "source_tech": "SQLSERVER",
        "target_tech": "SNOWFLAKE",
        "readiness_summary": {
            "status": "READY",
            "confidence_score": 92,
            "recommended_next_action": "Proceed to drafting",
            "blockers": [],
        },
        "quick_assessment": {
            "score": 90,
            "blockers": [],
        },
    }

    result = build_executive_summary(project, [])

    assert result["total_gaps"] == 0
    assert result["decision_open_count"] == 0
    assert result["decision_queue"] == []
    assert result["decision_focus"] == "No pending decision queue detected."


def test_build_executive_summary_falls_back_to_next_step_when_action_empty():
    project = {
        "source_tech": "SQLSERVER",
        "target_tech": "SNOWFLAKE",
        "readiness_summary": {
            "status": "BASELINE_READY",
            "confidence_score": 70,
            "recommended_next_action": "",
            "blockers": [],
            "warnings": ["Quick assessment is YELLOW"],
            "next_steps": ["Address the top warnings and recompute readiness."],
        },
        "quick_assessment": {
            "score": 65,
            "blockers": [],
        },
    }

    result = build_executive_summary(project, [])

    assert result["recommended_next_action"] == "Address the top warnings and recompute readiness."
    assert result["readiness_warnings"] == ["Quick assessment is YELLOW"]
    assert result["readiness_next_steps"] == ["Address the top warnings and recompute readiness."]
    assert any("Quick assessment is YELLOW" in risk for risk in result["top_risks"])


def test_build_gaps_summary_groups_by_category_and_severity():
    project = {
        "quick_assessment": {
            "blockers": ["Missing access to source system"],
        },
    }
    assets = [
        {
            "type": "CORE",
            "is_pii": True,
            "metadata": {"complexity_level": "HIGH", "mismatch_count": 2},
            "validation_result": {"violations": ["rule-1", "rule-2", "rule-3"]},
            "object_id": "asset-1",
            "object_name": "CustomerLoad",
        }
    ]

    result = build_gaps_summary(project, assets)

    assert result["total"] == 5
    assert result["by_severity"]["CRITICAL"] == 1
    assert result["by_severity"]["HIGH"] == 2
    assert result["by_severity"]["MEDIUM"] == 2
    assert result["by_category"]["target_architecture"] == 1
    assert result["by_category"]["compliance"] == 1
    assert result["by_category"]["business_rules"] == 1
    assert result["by_category"]["schema"] == 1
    assert result["by_category"]["data_quality"] == 1
    assert result["grouped"]["data_quality"][0]["severity"] == "HIGH"


def test_executive_summary_service_delegates_to_persistence():
    class DummyDb:
        async def get_project_metadata(self, project_id):
            return {
                "id": project_id,
                "source_tech": "SQLSERVER",
                "target_tech": "SNOWFLAKE",
                "quick_assessment": {"score": 88, "blockers": []},
            }

        async def get_project_assets(self, project_id):
            return [{"type": "CORE", "is_pii": False, "metadata": {}, "validation_result": None}]

    service = ExecutiveSummaryService(tenant_id="tenant-1", client_id="client-1")
    service.db = DummyDb()

    summary = asyncio.run(service.get_executive_summary("project-1"))
    gaps = asyncio.run(service.get_gaps_summary("project-1"))

    assert summary["source_tech"] == "SQLSERVER"
    assert summary["total_assets"] == 1
    assert gaps["total"] == 0
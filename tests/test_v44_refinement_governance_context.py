import json
from unittest.mock import AsyncMock, patch

import pytest

from apps.api.routers.governance import (
    _attach_mode_governance_context,
    _build_mode_governance_context,
    get_governance,
    get_refinement_state,
)


@pytest.mark.asyncio
async def test_build_mode_governance_context_for_intelligent_reengineering():
    context = _build_mode_governance_context("intelligent_reengineering")

    assert context["mode"] == "intelligent_reengineering"
    assert context["evaluation_focus"] == "medallion_consolidation_with_traceability"


@pytest.mark.asyncio
async def test_attach_mode_governance_context_keeps_existing_report_fields():
    report = {"score": 88, "status": "ok"}

    enriched = _attach_mode_governance_context(report, "structured_refinement")

    assert enriched["score"] == 88
    assert enriched["mode_context"]["mode"] == "structured_refinement"


@pytest.mark.asyncio
async def test_get_refinement_state_returns_reengineering_manifest_summary_when_present():
    db = AsyncMock()

    profile_json = json.dumps({"total_files": 5})
    manifest_json = json.dumps(
        {
            "execution_mode": "intelligent_reengineering",
            "objective": "Consolidate shared customer object across packages.",
            "processing_units": [{"unit_name": "customer"}, {"unit_name": "sales"}],
            "reengineering_summary": [{"target_asset_name": "customer"}],
        }
    )

    def _read_file_content(project_name, filename):
        if filename == "refinement.log":
            return "[10:00:00] started"
        if filename == "Refined/profile_metadata.json":
            return profile_json
        if filename == "Refined/reengineering_manifest.json":
            return manifest_json
        return None

    with patch(
        "apps.api.routers.governance.PersistenceService.read_file_content",
        side_effect=_read_file_content,
    ):
        state = await get_refinement_state("project-demo", db)

    assert state["profile"]["total_files"] == 5
    assert state["manifest_summary"]["manifest_name"] == "reengineering_manifest.json"
    assert state["manifest_summary"]["processing_units_count"] == 2
    assert state["manifest_summary"]["consolidation_units_count"] == 1
    assert state["manifest_summary"]["execution_mode"] == "intelligent_reengineering"


@pytest.mark.asyncio
async def test_get_refinement_state_falls_back_to_refinement_manifest():
    db = AsyncMock()

    manifest_json = json.dumps(
        {
            "execution_mode": "structured_refinement",
            "objective": "Bounded medallion optimization.",
            "processing_units": [{"unit_name": "customer"}],
            "reengineering_summary": [],
        }
    )

    def _read_file_content(project_name, filename):
        if filename == "Refined/reengineering_manifest.json":
            return None
        if filename == "Refined/refinement_manifest.json":
            return manifest_json
        return None

    with patch(
        "apps.api.routers.governance.PersistenceService.read_file_content",
        side_effect=_read_file_content,
    ):
        state = await get_refinement_state("project-demo", db)

    assert state["manifest_summary"]["manifest_name"] == "refinement_manifest.json"
    assert state["manifest_summary"]["execution_mode"] == "structured_refinement"


@pytest.mark.asyncio
async def test_get_governance_cached_report_includes_mode_context():
    db = AsyncMock()
    db.get_project_settings.return_value = {"governance_report": {"score": 96}}
    db.get_post_drafting_mode.return_value = "intelligent_reengineering"

    result = await get_governance("project-demo", db)

    assert result["score"] == 96
    assert result["mode_context"]["mode"] == "intelligent_reengineering"


@pytest.mark.asyncio
async def test_get_governance_generated_report_includes_mode_context():
    db = AsyncMock()
    db.tenant_id = "tenant-1"
    db.client_id = "client-1"
    db.get_project_settings.return_value = {}
    db.get_post_drafting_mode.return_value = "structured_refinement"

    with patch(
        "apps.api.routers.governance.GovernanceService.get_certification_report",
        new=AsyncMock(return_value={"score": 81}),
    ):
        result = await get_governance("project-demo", db)

    assert result["score"] == 81
    assert result["mode_context"]["mode"] == "structured_refinement"

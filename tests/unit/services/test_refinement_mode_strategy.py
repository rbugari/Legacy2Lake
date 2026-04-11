import pytest

from apps.api.services.refinement.architect_service import ArchitectService
from apps.api.services.refinement.profiler_service import ProfilerService
from apps.api.services.refinement.refinement_orchestrator import RefinementOrchestrator


class _PersistenceStub:
    def __init__(self, mode):
        self._mode = mode

    async def get_post_drafting_mode(self, project_id):
        return self._mode


@pytest.mark.asyncio
async def test_orchestrator_resolves_explicit_intelligent_reengineering_mode():
    orchestrator = RefinementOrchestrator(project_name="demo", project_uuid="demo")
    orchestrator.persistence = _PersistenceStub("intelligent_reengineering")

    mode = await orchestrator._resolve_refinement_mode("demo")

    assert mode == "intelligent_reengineering"


@pytest.mark.asyncio
async def test_orchestrator_falls_back_to_structured_refinement_for_invalid_mode():
    orchestrator = RefinementOrchestrator(project_name="demo", project_uuid="demo")
    orchestrator.persistence = _PersistenceStub("unexpected_mode")

    mode = await orchestrator._resolve_refinement_mode("demo")

    assert mode == "structured_refinement"


def test_architect_prefers_reengineering_units_when_mode_is_intelligent():
    architect = ArchitectService()
    profile_metadata = {
        "refinement_units": [
            {
                "unit_name": "customer",
                "source_files": ["customer.sql"],
            }
        ],
        "reengineering_units": [
            {
                "unit_name": "customer_360",
                "source_files": ["customer.sql", "crm_customer.sql"],
                "target_asset_name": "customer_360",
                "is_consolidation_candidate": True,
                "source_count": 2,
            }
        ],
    }

    units = architect._resolve_processing_units(profile_metadata, execution_mode="intelligent_reengineering")

    assert len(units) == 1
    assert units[0]["unit_name"] == "customer_360"


def test_profiler_builds_reengineering_units_and_candidates_from_refinement_units():
    profiler = ProfilerService()
    refinement_units = [
        {
            "unit_name": "customer",
            "output_table_name": "customer",
            "source_files": ["load_customer.dtsx", "sync_customer.sql"],
            "pk_columns": ["customer_id"],
            "table_type": "DIMENSION",
            "shared_connections": ["jdbc://crm"],
            "source_count": 2,
        },
        {
            "unit_name": "sales",
            "output_table_name": "sales",
            "source_files": ["fact_sales.py"],
            "pk_columns": ["sale_id"],
            "table_type": "FACT",
            "shared_connections": ["jdbc://shared-only"],
            "source_count": 1,
        },
    ]

    reengineering_units = profiler._build_reengineering_units(refinement_units)
    candidates = profiler._build_consolidation_candidates(reengineering_units)
    shared_entities = profiler._build_shared_entities(reengineering_units)

    assert reengineering_units[0]["unit_name"] == "customer"
    assert reengineering_units[0]["reuse_strategy"] == "project_wide_consolidation"
    assert any(item["candidate"] == "customer" for item in candidates)
    assert any(item["entity"] == "customer" for item in shared_entities)
    assert not any(item["candidate"] == "sales" for item in candidates)

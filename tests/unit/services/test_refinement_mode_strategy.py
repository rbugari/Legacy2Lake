import pytest
from unittest.mock import AsyncMock, patch

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


@pytest.mark.asyncio
async def test_architect_intelligent_reengineering_separates_artifacts_and_consolidates_sources():
    class _FakeStorage:
        def __init__(self):
            self.saved = {}
            self.input_files = {
                "/solutions/demo/refinement/drafting/customer_a.sql": "select 1 as customer_id",
                "/solutions/demo/refinement/drafting/customer_b.sql": "select 2 as customer_id",
            }

        def read_file(self, key):
            if key in self.input_files:
                return self.input_files[key]
            return self.saved.get(key)

        def save_file(self, key, content):
            self.saved[key] = content

    class _FakeCartridge:
        @staticmethod
        def get_file_extension():
            return ".sql"

        @staticmethod
        def generate_scaffolding():
            return {
                "config.py": "# config",
                "utils.py": "# utils",
            }

        @staticmethod
        def generate_bronze(table_metadata):
            return f"-- shared from {len(table_metadata.get('source_files', []))} sources"

        @staticmethod
        def generate_silver(table_metadata):
            return "-- core"

        @staticmethod
        def generate_gold(table_metadata):
            return "-- publish"

        @staticmethod
        def generate_orchestration(_):
            return "{}"

    fake_storage = _FakeStorage()
    architect = ArchitectService()

    profile_metadata = {
        "analyzed_files": ["customer_a.sql", "customer_b.sql"],
        "reengineering_units": [
            {
                "unit_name": "customer_360",
                "output_table_name": "customer_360",
                "target_asset_name": "customer_360",
                "source_files": ["customer_a.sql", "customer_b.sql"],
                "pk_columns": ["customer_id"],
                "table_type": "DIMENSION",
                "reuse_strategy": "project_wide_consolidation",
                "is_consolidation_candidate": True,
            }
        ],
        "refinement_units": [
            {
                "unit_name": "customer_a",
                "source_files": ["customer_a.sql"],
            },
            {
                "unit_name": "customer_b",
                "source_files": ["customer_b.sql"],
            },
        ],
    }

    with patch("apps.api.services.refinement.architect_service.PersistenceService.get_storage", return_value=fake_storage), \
         patch("apps.api.services.refinement.architect_service.PersistenceService.ensure_solution_dir", return_value="/solutions/demo/refinement"), \
         patch("apps.api.services.refinement.cartridges.factory.CartridgeFactory.get_cartridge", return_value=_FakeCartridge()), \
         patch("apps.api.services.refinement.architect_service.SupabasePersistence") as mock_db_cls, \
         patch("apps.api.services.knowledge_service.KnowledgeService.get_default_registry_entries", return_value=[]), \
         patch("apps.api.services.knowledge_service.KnowledgeService.flatten_knowledge", return_value={}):
        mock_db = AsyncMock()
        mock_db.get_design_registry = AsyncMock(return_value=[])
        mock_db_cls.return_value = mock_db

        result = await architect.refine_project(
            project_id="demo",
            profile_metadata=profile_metadata,
            execution_mode="intelligent_reengineering",
        )

    refined_files = result["refined_files"]
    manifest_key = refined_files["manifest"][0]
    manifest = fake_storage.saved[manifest_key]

    assert result["status"] == "COMPLETED"
    assert result["execution_mode"] == "intelligent_reengineering"

    # Consolidation is real: one processing unit for two drafted sources.
    assert len(refined_files["reengineered_shared"]) == 1
    assert len(refined_files["reengineered_core"]) == 1
    assert len(refined_files["reengineered_publish"]) == 1

    # Artifacts are separated by reengineering layout.
    assert "/reengineered/shared/" in refined_files["reengineered_shared"][0]
    assert "/reengineered/core/" in refined_files["reengineered_core"][0]
    assert "/reengineered/publish/" in refined_files["reengineered_publish"][0]

    # Backward compatibility remains: legacy layer buckets still populated.
    assert len(refined_files["bronze"]) == 1
    assert len(refined_files["silver"]) == 1
    assert len(refined_files["gold"]) == 1

    assert "customer_a.sql" in manifest
    assert "customer_b.sql" in manifest
    assert "reengineering_summary" in manifest

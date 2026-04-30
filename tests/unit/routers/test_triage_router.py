"""
Unit tests for triage router background flow.

Focus: understanding snapshot refresh behavior after triage completion.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.api.routers.triage import (
    TriageParams,
    _infer_sql_column_mappings,
    _persist_column_mappings,
    _resolve_triage_asset_category,
    _run_triage_background,
)


@pytest.fixture
def triage_db_mock():
    db = MagicMock()
    db.tenant_id = "550e8400-e29b-41d4-a716-446655440001"
    db.client_id = "550e8400-e29b-41d4-a716-446655440002"

    # Async DB methods used by _run_triage_background
    db.get_project_name_by_id = AsyncMock(return_value="TestProject")
    db.get_project_id_by_name = AsyncMock(return_value="550e8400-e29b-41d4-a716-446655440000")
    db.clear_execution_logs = AsyncMock(return_value=True)
    db.get_project_status = AsyncMock(return_value="TRIAGE")
    db.log_execution = AsyncMock(return_value=True)
    db.check_cancellation = AsyncMock(return_value=False)
    db.update_project_metadata = AsyncMock(return_value=True)
    db.get_project_context = AsyncMock(return_value=[])
    db.get_project_settings = AsyncMock(return_value={})
    db.resolve_agent_model = AsyncMock(return_value={"provider": "azure", "deployment": "gpt-test"})
    db.batch_save_assets = AsyncMock(
        return_value=[
            {
                "id": "asset-001",
                "object_id": "asset-001",
                "filename": "load_customer.dtsx",
                "source_path": "Triage/load_customer.dtsx",
                "metadata": {},
            }
        ]
    )
    db.save_project_layout = AsyncMock(return_value=True)
    db.update_project_settings = AsyncMock(return_value=True)
    db.sync_file_inventory = AsyncMock(return_value=True)
    db.update_project_status = AsyncMock(return_value=True)

    # Sync client call chain (used by some optional persistence paths)
    db.client = MagicMock()
    db.client.table.return_value.update.return_value.eq.return_value.execute.return_value = SimpleNamespace(data=[])

    return db


@pytest.fixture
def triage_dependencies():
    manifest = {
        "file_inventory": [
            {
                "name": "load_customer.dtsx",
                "path": "Triage/load_customer.dtsx",
                "size": 1200,
                "lines": 30,
                "content": "SELECT 1 AS customer_id;",
                "metadata": {},
                "signatures": [],
                "invocations": [],
            }
        ],
        "tech_stats": {"dtsx": 1},
    }

    agent_result = {
        "mesh_graph": {
            "nodes": [
                {
                    "id": "Triage/load_customer.dtsx",
                    "label": "load_customer.dtsx",
                    "category": "CORE",
                    "complexity": "LOW",
                    "confidence": 0.9,
                }
            ],
            "edges": [],
        }
    }

    dag = SimpleNamespace(nodes=[], edges=[], cycles=[], execution_order=[])

    return {
        "manifest": manifest,
        "agent_result": agent_result,
        "dag": dag,
    }


@pytest.mark.anyio
async def test_run_triage_background_refreshes_understanding_after_success(triage_db_mock, triage_dependencies):
    lock_service = MagicMock()
    lock_service.release_lock = AsyncMock(return_value=True)

    with patch("apps.api.routers.triage.SupabasePersistence", return_value=triage_db_mock), \
         patch("apps.api.routers.triage.PersistenceService.get_storage", return_value=MagicMock()), \
         patch("apps.api.routers.triage.PersistenceService.ensure_solution_dir", return_value="solutions/test"), \
         patch("apps.api.routers.triage.DiscoveryService.generate_manifest", return_value=triage_dependencies["manifest"]), \
         patch("apps.api.routers.triage.QuickAssessmentService") as MockQuickAssessment, \
         patch("apps.api.routers.triage.AgentAService") as MockAgentA, \
         patch("apps.api.routers.triage.KnowledgePacketService") as MockKnowledgePacket, \
         patch("apps.api.routers.triage.TableImpactService") as MockTableImpact, \
         patch("apps.api.routers.triage.UnderstandingService") as MockUnderstanding:
        MockQuickAssessment.return_value._classify_file.return_value = ("migrable", "SSIS")

        MockAgentA.return_value.analyze_manifest = AsyncMock(return_value=triage_dependencies["agent_result"])

        MockKnowledgePacket.return_value.scan_project = AsyncMock(
            return_value={
                "total_assets": 1,
                "assets_with_ddl_types": 0,
                "assets_with_profiled_types": 0,
                "pii_columns_detected": 0,
            }
        )

        MockTableImpact.return_value.analyze_impacts = AsyncMock(
            return_value={"total_impacts": 0, "unique_tables": 0}
        )
        MockTableImpact.return_value.build_dependency_dag = AsyncMock(return_value=triage_dependencies["dag"])

        MockUnderstanding.return_value.rebuild = AsyncMock(return_value={"generated_at": "2026-04-01T00:00:00Z"})

        await _run_triage_background(
            project_id="550e8400-e29b-41d4-a716-446655440000",
            params=TriageParams(),
            lock_id="lock-123",
            lock_service=lock_service,
            tenant_id=triage_db_mock.tenant_id,
            owner_user_id=triage_db_mock.tenant_id,
            username="tester",
            db_config={"client_id": triage_db_mock.client_id},
        )

    MockUnderstanding.return_value.rebuild.assert_awaited_once()
    triage_db_mock.update_project_status.assert_awaited_once_with(
        "550e8400-e29b-41d4-a716-446655440000", "TRIAGED"
    )
    lock_service.release_lock.assert_awaited_once_with(lock_id="lock-123", user_id=triage_db_mock.tenant_id)

    saved_assets = triage_db_mock.batch_save_assets.await_args.args[1]
    assert saved_assets[0]["content"] == "SELECT 1 AS customer_id;"


@pytest.mark.anyio
async def test_run_triage_background_continues_when_understanding_refresh_fails(triage_db_mock, triage_dependencies):
    lock_service = MagicMock()
    lock_service.release_lock = AsyncMock(return_value=True)

    with patch("apps.api.routers.triage.SupabasePersistence", return_value=triage_db_mock), \
         patch("apps.api.routers.triage.PersistenceService.get_storage", return_value=MagicMock()), \
         patch("apps.api.routers.triage.PersistenceService.ensure_solution_dir", return_value="solutions/test"), \
         patch("apps.api.routers.triage.DiscoveryService.generate_manifest", return_value=triage_dependencies["manifest"]), \
         patch("apps.api.routers.triage.QuickAssessmentService") as MockQuickAssessment, \
         patch("apps.api.routers.triage.AgentAService") as MockAgentA, \
         patch("apps.api.routers.triage.KnowledgePacketService") as MockKnowledgePacket, \
         patch("apps.api.routers.triage.TableImpactService") as MockTableImpact, \
         patch("apps.api.routers.triage.UnderstandingService") as MockUnderstanding:
        MockQuickAssessment.return_value._classify_file.return_value = ("migrable", "SSIS")

        MockAgentA.return_value.analyze_manifest = AsyncMock(return_value=triage_dependencies["agent_result"])

        MockKnowledgePacket.return_value.scan_project = AsyncMock(
            return_value={
                "total_assets": 1,
                "assets_with_ddl_types": 0,
                "assets_with_profiled_types": 0,
                "pii_columns_detected": 0,
            }
        )

        MockTableImpact.return_value.analyze_impacts = AsyncMock(
            return_value={"total_impacts": 0, "unique_tables": 0}
        )
        MockTableImpact.return_value.build_dependency_dag = AsyncMock(return_value=triage_dependencies["dag"])

        MockUnderstanding.return_value.rebuild = AsyncMock(side_effect=Exception("refresh failed"))

        await _run_triage_background(
            project_id="550e8400-e29b-41d4-a716-446655440000",
            params=TriageParams(),
            lock_id="lock-456",
            lock_service=lock_service,
            tenant_id=triage_db_mock.tenant_id,
            owner_user_id=triage_db_mock.tenant_id,
            username="tester",
            db_config={"client_id": triage_db_mock.client_id},
        )

    triage_db_mock.update_project_status.assert_awaited_once_with(
        "550e8400-e29b-41d4-a716-446655440000", "TRIAGED"
    )
    lock_service.release_lock.assert_awaited_once_with(lock_id="lock-456", user_id=triage_db_mock.tenant_id)


def test_infer_sql_column_mappings_handles_insert_select_with_expressions():
    sql = """
    INSERT INTO dim_cliente (cliente_id, nombre_normalizado, estado)
    SELECT c.id, UPPER(c.nombre) AS nombre, 'A'
    FROM src_clientes c;
    """

    mappings = _infer_sql_column_mappings(sql)
    mapping_pairs = {(m["source_column"], m["target_column"]) for m in mappings}

    assert ("id", "cliente_id") in mapping_pairs
    assert ("nombre", "nombre_normalizado") in mapping_pairs
    # constant-to-target mapping falls back to target as source for traceability
    assert ("estado", "estado") in mapping_pairs


def test_resolve_triage_asset_category_promotes_procedural_sql_without_agent_node():
    category = _resolve_triage_asset_category(
        file_name="01_sp_load_dim_fecha.sql",
        file_category="soporte",
        file_preclassification=None,
        agent_node={},
        raw_content="CREATE PROCEDURE sp_load_dim_fecha() BEGIN SELECT 1; END",
    )

    assert category == "CORE"


def test_resolve_triage_asset_category_keeps_ddl_sql_as_support_without_agent_node():
    category = _resolve_triage_asset_category(
        file_name="00_ddl_nalub_dw.sql",
        file_category="soporte",
        file_preclassification=None,
        agent_node={},
        raw_content="CREATE TABLE dim_fecha (fecha_key INT);",
    )

    assert category == "SUPPORT"


def test_infer_sql_column_mappings_handles_update_set_assignments():
    sql = """
    UPDATE dim_producto
    SET precio_final = ROUND(precio * 1.21, 2),
        categoria = categoria_origen;
    """

    mappings = _infer_sql_column_mappings(sql)
    mapping_pairs = {(m["source_column"], m["target_column"]) for m in mappings}

    assert ("precio", "precio_final") in mapping_pairs
    assert ("categoria_origen", "categoria") in mapping_pairs


@pytest.mark.anyio
async def test_persist_column_mappings_detects_case_when_rule():
    db = MagicMock()
    db.client = MagicMock()

    medulla = {
        "data_flow_logic": [
            {
                "type": "DERIVED_COLUMN",
                "name": "derive_bucket",
                "mappings": [
                    {
                        "usage": "INPUT",
                        "source": "OrderTotal",
                        "target": "OrderBucket",
                        "expression": "CASE WHEN OrderTotal > 1000 THEN 'HIGH' ELSE 'LOW' END",
                    }
                ],
                "raw_properties": {},
            }
        ]
    }

    captured = {}

    class FakeMappingService:
        def __init__(self, supabase_client):
            self.supabase_client = supabase_client

        async def bulk_upsert(self, mappings):
            captured["mappings"] = mappings
            return len(mappings)

    with patch("apps.api.services.column_mapping_service.ColumnMappingService", FakeMappingService):
        count = await _persist_column_mappings("asset-case", medulla, db)

    assert count == 1
    assert captured["mappings"][0].source_column == "OrderTotal"
    assert captured["mappings"][0].target_column == "OrderBucket"
    assert captured["mappings"][0].transformation_rule == "CASE_WHEN(OrderTotal -> OrderBucket)"


@pytest.mark.anyio
async def test_persist_column_mappings_detects_cast_and_concat_rules():
    db = MagicMock()
    db.client = MagicMock()

    medulla = {
        "data_flow_logic": [
            {
                "type": "DERIVED_COLUMN",
                "name": "derive_values",
                "mappings": [
                    {
                        "usage": "INPUT",
                        "source": "AmountRaw",
                        "target": "AmountDecimal",
                        "expression": "CAST(AmountRaw AS DECIMAL(18,2))",
                    },
                    {
                        "usage": "INPUT",
                        "source": "NameFirst",
                        "target": "FullName",
                        "expression": "CONCAT(NameFirst, ' ', NameLast)",
                    },
                ],
                "raw_properties": {},
            }
        ]
    }

    captured = {}

    class FakeMappingService:
        def __init__(self, supabase_client):
            self.supabase_client = supabase_client

        async def bulk_upsert(self, mappings):
            captured["mappings"] = mappings
            return len(mappings)

    with patch("apps.api.services.column_mapping_service.ColumnMappingService", FakeMappingService):
        count = await _persist_column_mappings("asset-cast-concat", medulla, db)

    assert count == 2
    rules = [m.transformation_rule for m in captured["mappings"]]
    assert "CAST(AmountRaw -> AmountDecimal)" in rules
    assert "CONCAT(NameFirst -> FullName)" in rules

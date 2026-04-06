import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from apps.api.services.persistence_service import SupabasePersistence
from apps.api.services.understanding_service import UnderstandingService, _build_rule_candidates


def _make_query(*, data=None, error=None):
    query = MagicMock()
    query.eq.return_value = query
    query.in_.return_value = query
    query.single.return_value = query
    if error is not None:
        query.execute.side_effect = error
    else:
        query.execute.return_value = MagicMock(data=data)
    return query


@pytest.fixture(autouse=True)
def reset_support_flags():
    SupabasePersistence._supports_understanding_columns = None
    UnderstandingService._supports_project_understanding_columns = None
    yield
    SupabasePersistence._supports_understanding_columns = None
    UnderstandingService._supports_project_understanding_columns = None


def test_get_project_metadata_caches_missing_understanding_columns():
    select_calls = []

    def select_side_effect(columns):
        select_calls.append(columns)
        if "understanding_generated_at" in columns:
            return _make_query(error=Exception('column "understanding_generated_at" does not exist'))
        return _make_query(data=[{
            "project_id": "proj-1",
            "tenant_id": "tenant-1",
            "name": "demo",
            "repo_url": None,
            "status": "TRIAGE",
            "stage": "2",
            "prompt": None,
            "settings": {
                "understanding_generated_at": "2026-04-01T12:00:00Z",
                "understanding_version": "v1",
                "understanding_payload": {"version": "v1", "project_id": "proj-1"},
            },
            "config": {},
            "is_active": True,
            "quick_assessment": None,
            "readiness_summary": None,
        }])

    client = MagicMock()
    table = MagicMock()
    table.select.side_effect = select_side_effect
    client.table.return_value = table

    with patch("apps.api.services.persistence_service.create_client", return_value=client):
        db = SupabasePersistence()
        with patch.object(db, "_resolve_uuid", AsyncMock(return_value="proj-1")):
            first = asyncio.run(db.get_project_metadata("proj-1"))
            second = asyncio.run(db.get_project_metadata("proj-1"))

    assert first is not None
    assert second is not None
    assert first["understanding_generated_at"] == "2026-04-01T12:00:00Z"
    assert second["understanding_payload"]["project_id"] == "proj-1"
    assert len([call for call in select_calls if "understanding_generated_at" in call]) == 1
    assert SupabasePersistence._supports_understanding_columns is False


def test_get_evidence_items_normalizes_legacy_schema_columns():
    client = MagicMock()
    table = MagicMock()
    query = _make_query(data=[{
        "evidence_id": "ev-1",
        "asset_id": "asset-1",
        "source_block_type": "sql_fragment",
        "rationale": "Customer join logic",
    }])
    table.select.return_value = query
    client.table.return_value = table

    with patch("apps.api.services.persistence_service.create_client", return_value=client):
        service = UnderstandingService("proj-1")

    evidence = service._get_evidence_items()

    assert evidence == [{
        "evidence_id": "ev-1",
        "asset_id": "asset-1",
        "source_block_type": "sql_fragment",
        "rationale": "Customer join logic",
        "id": "ev-1",
        "evidence_type": "sql_fragment",
        "summary": "Customer join logic",
    }]
    query.eq.assert_called_once_with("project_id", "proj-1")


def test_get_column_mappings_uses_asset_scope_and_normalizes_transformation_rule():
    client = MagicMock()
    table = MagicMock()
    query = _make_query(data=[{
        "id": "map-1",
        "asset_id": "asset-1",
        "source_column": "customer_name",
        "target_column": "customer_name_clean",
        "transformation_rule": "TRIM(customer_name)",
    }])
    table.select.return_value = query
    client.table.return_value = table

    with patch("apps.api.services.persistence_service.create_client", return_value=client):
        service = UnderstandingService("proj-1")

    mappings = service._get_column_mappings(["asset-1"])

    assert mappings == [{
        "id": "map-1",
        "asset_id": "asset-1",
        "source_column": "customer_name",
        "target_column": "customer_name_clean",
        "transformation_rule": "TRIM(customer_name)",
        "mapping_id": "map-1",
        "transformation_expr": "TRIM(customer_name)",
        "transformation": "TRIM(customer_name)",
    }]
    query.in_.assert_called_once_with("asset_id", ["asset-1"])


def test_get_snapshot_reads_settings_fallback_when_columns_are_missing():
    def select_side_effect(columns):
        if columns == "understanding_payload, understanding_generated_at":
            return _make_query(error=Exception('column "understanding_payload" does not exist'))
        if columns == "settings":
            return _make_query(data={
                "settings": {
                    "understanding_payload": {"version": "v1", "project_id": "proj-1"}
                }
            })
        raise AssertionError(f"Unexpected select: {columns}")

    client = MagicMock()
    table = MagicMock()
    table.select.side_effect = select_side_effect
    client.table.return_value = table

    with patch("apps.api.services.persistence_service.create_client", return_value=client):
        service = UnderstandingService("proj-1")

    payload = asyncio.run(service.get_snapshot())

    assert payload == {"version": "v1", "project_id": "proj-1"}
    assert UnderstandingService._supports_project_understanding_columns is False


def test_rule_candidates_accept_transformation_rule_column():
    result = _build_rule_candidates(
        [
            {
                "id": "map-1",
                "asset_id": "asset-1",
                "source_column": "amount",
                "target_column": "amount_rounded",
                "transformation_rule": "ROUND(amount, 2)",
            },
            {
                "id": "map-2",
                "asset_id": "asset-2",
                "source_column": "price",
                "target_column": "price_rounded",
                "transformation_rule": "ROUND(amount, 2)",
            },
        ],
        [
            {"object_id": "asset-1", "object_name": "pkg_a"},
            {"object_id": "asset-2", "object_name": "pkg_b"},
        ],
    )

    assert result["total"] == 1
    assert result["candidates"][0]["pattern"] == "numeric_rounding"
    assert result["candidates"][0]["reuse_scope"] == "project"
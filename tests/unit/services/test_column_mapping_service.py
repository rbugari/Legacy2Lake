"""Unit tests for ColumnMappingService."""

import pytest
from unittest.mock import MagicMock

from apps.api.services.column_mapping_service import ColumnMapping, ColumnMappingService


class _MockTable:
    def __init__(self):
        self.upsert_payload = None
        self.on_conflict = None

    def upsert(self, data, on_conflict=None):
        self.upsert_payload = data
        self.on_conflict = on_conflict
        return self

    def execute(self):
        return MagicMock(data=self.upsert_payload)


class _MockClient:
    def __init__(self):
        self.table_instance = _MockTable()

    def table(self, _name):
        return self.table_instance


@pytest.mark.anyio
async def test_bulk_upsert_deduplicates_by_asset_and_source_column():
    client = _MockClient()
    service = ColumnMappingService(supabase_client=client)

    mappings = [
        ColumnMapping(
            asset_id="asset-1",
            source_column="cliente_id",
            target_column="customer_id",
            transformation_rule="CAST",
        ),
        ColumnMapping(
            asset_id="asset-1",
            source_column="cliente_id",
            target_column="cust_id",
            transformation_rule="RENAME",
        ),
        ColumnMapping(
            asset_id="asset-1",
            source_column="monto_total",
            target_column="total_amount",
        ),
    ]

    count = await service.bulk_upsert(mappings)

    assert count == 2
    assert client.table_instance.on_conflict == "asset_id,source_column"

    persisted = {
        (row["asset_id"], row["source_column"]): row
        for row in client.table_instance.upsert_payload
    }
    assert ("asset-1", "cliente_id") in persisted
    assert persisted[("asset-1", "cliente_id")]["target_column"] == "cust_id"
    assert persisted[("asset-1", "cliente_id")]["transformation_rule"] == "RENAME"


@pytest.mark.anyio
async def test_bulk_upsert_skips_empty_source_column():
    client = _MockClient()
    service = ColumnMappingService(supabase_client=client)

    mappings = [
        ColumnMapping(asset_id="asset-1", source_column="   ", target_column="ignored"),
        ColumnMapping(asset_id="asset-1", source_column="valid_col", target_column="valid_col"),
    ]

    count = await service.bulk_upsert(mappings)

    assert count == 1
    payload = client.table_instance.upsert_payload
    assert len(payload) == 1
    assert payload[0]["source_column"] == "valid_col"

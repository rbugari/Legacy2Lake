from unittest.mock import patch

from apps.api.prompts.catalog import build_cartridge_prompt_id
from apps.api.services.refinement.cartridges.factory import CartridgeFactory


class _FakeResponse:
    data = []


class _FakeTableQuery:
    def select(self, _):
        return self

    def eq(self, *_):
        return self

    def execute(self):
        return _FakeResponse()


class _FakeClient:
    def table(self, _):
        return _FakeTableQuery()


class _FakeSupabasePersistence:
    def __init__(self, tenant_id=None):
        self.client = _FakeClient()


def _cartridge_name_for(target_tech: str) -> str:
    registry = {"paths": {"target_stack": "pyspark"}}
    with patch(
        "apps.api.services.refinement.cartridges.factory.SupabasePersistence",
        _FakeSupabasePersistence,
    ):
        cartridge = CartridgeFactory.get_cartridge(
            project_id="demo",
            registry=registry,
            tenant_id="tenant",
            target_tech=target_tech,
        )
    return cartridge.__class__.__name__


def test_prompt_id_normalizes_snowflake_sql_aliases():
    assert build_cartridge_prompt_id("direct", "snowflake_sql") == "agent_c_direct_snowflake_sql"
    assert build_cartridge_prompt_id("direct", "snowflake_native_sql") == "agent_c_direct_snowflake_sql"
    assert build_cartridge_prompt_id("direct", "snowflake_sql_native") == "agent_c_direct_snowflake_sql"
    assert build_cartridge_prompt_id("direct", "snowflake_sql_direct") == "agent_c_direct_snowflake_sql"


def test_prompt_id_normalizes_fabric_sql_aliases():
    assert build_cartridge_prompt_id("direct", "ms_fabric_sql") == "agent_c_direct_ms_fabric_sql"
    assert build_cartridge_prompt_id("direct", "fabric_sql") == "agent_c_direct_ms_fabric_sql"
    assert build_cartridge_prompt_id("direct", "ms_fabric_warehouse") == "agent_c_direct_ms_fabric_sql"


def test_factory_maps_snowflake_sql_aliases_to_snowflake_cartridge():
    assert _cartridge_name_for("snowflake_sql") == "SnowflakeCartridge"
    assert _cartridge_name_for("snowflake_native_sql") == "SnowflakeCartridge"
    assert _cartridge_name_for("snowflake_sql_native") == "SnowflakeCartridge"


def test_factory_maps_fabric_sql_aliases_to_fabric_cartridge():
    assert _cartridge_name_for("ms_fabric_sql") == "MSFabricCartridge"
    assert _cartridge_name_for("fabric_sql") == "MSFabricCartridge"
    assert _cartridge_name_for("ms_fabric_warehouse") == "MSFabricCartridge"

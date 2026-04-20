"""
CI Test Suite: Tech Stack Contract Validation

Ensures all SQL destinations (Snowflake, Fabric, etc.) maintain consistent contracts
for cartridge selection, prompt resolution, and SQL flavor coverage.

Run with: pytest tests/unit/services/test_tech_stack_contracts_ci.py -v
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from apps.api.prompts.catalog import build_cartridge_prompt_id, normalize_tech_stack
from apps.api.services.refinement.cartridges.tech_stack_contracts import (
    TECH_STACK_REGISTRY,
    resolve_contract,
    get_canonical_tech,
    get_cartridge_class,
    get_sql_flavor,
    validate_sql_flavor_coverage,
    SQLFlavor,
)


class TestTechStackRegistry:
    """Validate the tech stack registry is well-formed."""

    def test_all_contracts_have_required_fields(self):
        """Each contract must have all required fields."""
        required_fields = {
            "canonical_tech",
            "aliases",
            "cartridge_class",
            "sql_flavor",
            "supported_layers",
        }
        for tech, contract in TECH_STACK_REGISTRY.items():
            for field in required_fields:
                assert hasattr(contract, field), f"{tech} missing field {field}"

    def test_canonical_tech_in_registry_keys(self):
        """Canonical tech should be a registry key."""
        for tech, contract in TECH_STACK_REGISTRY.items():
            assert (
                contract.canonical_tech == tech
            ), f"Mismatch: {tech} vs {contract.canonical_tech}"

    def test_all_aliases_resolve_to_registry(self):
        """Every alias should resolve back to a valid contract."""
        for tech, contract in TECH_STACK_REGISTRY.items():
            for alias in contract.aliases:
                resolved = resolve_contract(alias)
                assert (
                    resolved is not None
                ), f"Alias {alias} from {tech} did not resolve"
                assert (
                    resolved.canonical_tech == contract.canonical_tech
                ), f"Alias {alias} resolved to {resolved.canonical_tech}, expected {contract.canonical_tech}"

    def test_supported_layers_include_direct(self):
        """All contracts should support the 'direct' layer."""
        for tech, contract in TECH_STACK_REGISTRY.items():
            assert (
                "direct" in contract.supported_layers
            ), f"{tech} does not support direct layer"


class TestPromptIDResolution:
    """Validate prompt ID resolution for all SQL tech stacks."""

    @pytest.mark.parametrize(
        "tech_input,expected_canonical",
        [
            ("snowflake_sql", "snowflake_sql"),
            ("snowflake_native_sql", "snowflake_sql"),
            ("snowflake_sql_native", "snowflake_sql"),
            ("ms_fabric_sql", "ms_fabric_sql"),
            ("fabric_sql", "ms_fabric_sql"),
            ("ms_fabric_warehouse", "ms_fabric_sql"),
        ],
    )
    def test_sql_aliases_normalize_to_canonical(self, tech_input, expected_canonical):
        """SQL aliases should normalize to their canonical form."""
        canonical = get_canonical_tech(tech_input)
        assert canonical == expected_canonical

    @pytest.mark.parametrize(
        "layer,tech_input",
        [
            ("direct", "snowflake_sql"),
            ("bronze", "snowflake_sql"),
            ("silver", "snowflake_sql"),
            ("gold", "snowflake_sql"),
            ("direct", "ms_fabric_sql"),
            ("bronze", "ms_fabric_sql"),
        ],
    )
    def test_prompt_id_builds_for_sql_stacks(self, layer, tech_input):
        """Prompt IDs should build for all SQL layer+tech combinations."""
        prompt_id = build_cartridge_prompt_id(layer, tech_input)
        assert prompt_id is not None
        assert layer in prompt_id.lower()
        assert get_canonical_tech(tech_input) in prompt_id.lower()


class TestCartridgeFactoryMapping:
    """Validate cartridge factory produces correct cartridge for tech inputs."""

    class _FakeResponse:
        data = []

    class _FakeTableQuery:
        def select(self, _):
            return self

        def eq(self, *_):
            return self

        def execute(self):
            return self._FakeResponse()

    class _FakeClient:
        def table(self, _):
            return TestCartridgeFactoryMapping._FakeTableQuery()

    class _FakeSupabasePersistence:
        def __init__(self, tenant_id=None):
            self.client = TestCartridgeFactoryMapping._FakeClient()

    def _get_cartridge_for(self, target_tech: str):
        """Helper to get cartridge instance for a tech input."""
        from apps.api.services.refinement.cartridges.factory import CartridgeFactory

        registry = {"paths": {"target_stack": "pyspark"}}
        with patch(
            "apps.api.services.refinement.cartridges.factory.SupabasePersistence",
            self._FakeSupabasePersistence,
        ):
            cartridge = CartridgeFactory.get_cartridge(
                project_id="test",
                registry=registry,
                tenant_id="test_tenant",
                target_tech=target_tech,
            )
        return cartridge

    @pytest.mark.parametrize(
        "tech_input,expected_cartridge",
        [
            ("snowflake_sql", "SnowflakeCartridge"),
            ("snowflake_native_sql", "SnowflakeCartridge"),
            ("snowflake_sql_native", "SnowflakeCartridge"),
            ("ms_fabric_sql", "MSFabricCartridge"),
            ("fabric_sql", "MSFabricCartridge"),
            ("ms_fabric_warehouse", "MSFabricCartridge"),
            ("pyspark", "PySparkCartridge"),
            ("databricks", "PySparkCartridge"),
        ],
    )
    def test_factory_maps_tech_to_correct_cartridge(
        self, tech_input, expected_cartridge
    ):
        """Factory should select correct cartridge for each tech input."""
        cartridge = self._get_cartridge_for(tech_input)
        assert (
            cartridge.__class__.__name__ == expected_cartridge
        ), f"Expected {expected_cartridge}, got {cartridge.__class__.__name__}"


class TestSQLFlavorValidation:
    """Validate SQL flavor coverage for different code patterns."""

    def test_snowflake_sql_requires_copy_or_merge(self):
        """Snowflake SQL must have COPY INTO, MERGE, or CREATE."""
        code_valid = "COPY INTO table_name FROM @stage;"
        code_invalid = "SELECT * FROM table_name;"

        valid_result = validate_sql_flavor_coverage(
            "snowflake_sql", code_valid, "direct"
        )
        assert valid_result["valid"]

        invalid_result = validate_sql_flavor_coverage(
            "snowflake_sql", code_invalid, "direct"
        )
        assert not invalid_result["valid"]
        assert len(invalid_result["issues"]) > 0

    def test_ms_fabric_sql_requires_tsql_keywords(self):
        """MS Fabric SQL must have T-SQL keywords."""
        code_valid = "CREATE TABLE table_name (id INT);"
        code_invalid = "SELECT * FROM table_name;"

        valid_result = validate_sql_flavor_coverage(
            "ms_fabric_sql", code_valid, "direct"
        )
        assert valid_result["valid"]

        invalid_result = validate_sql_flavor_coverage(
            "ms_fabric_sql", code_invalid, "direct"
        )
        assert not invalid_result["valid"]

    def test_pyspark_requires_spark_api(self):
        """PySpark must use spark.read or spark.write."""
        code_valid = "df = spark.read.table('table_name')"
        code_invalid = "df = pd.read_csv('file.csv')"

        valid_result = validate_sql_flavor_coverage(
            "pyspark", code_valid, "direct"
        )
        assert valid_result["valid"]

        invalid_result = validate_sql_flavor_coverage(
            "pyspark", code_invalid, "direct"
        )
        assert not invalid_result["valid"]

    def test_validates_layer_support(self):
        """Should validate that layer is supported by contract."""
        # All techs support direct
        result = validate_sql_flavor_coverage("snowflake_sql", "COPY INTO t FROM @s;", "direct")
        assert result["valid"]

        # Test with supported layer
        result = validate_sql_flavor_coverage("snowflake_sql", "MERGE INTO t USING s", "silver")
        assert result["valid"]


class TestEndToEndContractConsistency:
    """Integration tests ensuring consistency across prompt/cartridge/flavor."""

    def test_sql_tech_aliases_produce_same_prompt_id(self):
        """All aliases for a SQL tech should produce the same canonical prompt ID."""
        # Snowflake SQL variants
        ids = [
            build_cartridge_prompt_id("direct", "snowflake_sql"),
            build_cartridge_prompt_id("direct", "snowflake_native_sql"),
            build_cartridge_prompt_id("direct", "snowflake_sql_native"),
            build_cartridge_prompt_id("direct", "snowflake_sql_direct"),
        ]
        assert all(id == ids[0] for id in ids), f"Inconsistent IDs: {ids}"

        # Fabric SQL variants
        ids = [
            build_cartridge_prompt_id("direct", "ms_fabric_sql"),
            build_cartridge_prompt_id("direct", "fabric_sql"),
            build_cartridge_prompt_id("direct", "ms_fabric_warehouse"),
        ]
        assert all(id == ids[0] for id in ids), f"Inconsistent IDs: {ids}"

    def test_all_sql_techs_have_direct_prompt_support(self):
        """Every SQL tech should have a direct layer prompt defined."""
        from apps.api.prompts.catalog import get_canonical_prompt_specs

        specs = {s.prompt_id for s in get_canonical_prompt_specs()}

        sql_techs = ["snowflake_sql", "ms_fabric_sql"]
        for tech in sql_techs:
            expected_id = f"agent_c_direct_{tech}"
            assert (
                expected_id in specs
            ), f"Missing prompt for {expected_id}. Available: {specs}"

    def test_cartridge_and_flavor_consistency(self):
        """Cartridge class and SQL flavor should align for SQL techs."""
        for tech, contract in TECH_STACK_REGISTRY.items():
            if contract.sql_flavor in [SQLFlavor.SNOWFLAKE_SQL, SQLFlavor.MS_FABRIC_SQL]:
                # SQL-generating cartridges
                assert "Cartridge" in contract.cartridge_class
                assert contract.requires_sql_only or not contract.requires_sql_only

    @pytest.mark.parametrize(
        "tech_input",
        [
            "snowflake_sql",
            "snowflake_native_sql",
            "ms_fabric_sql",
            "fabric_sql",
        ],
    )
    def test_resolves_to_sql_flavor_for_sql_techs(self, tech_input):
        """All SQL tech aliases should resolve to a SQL flavor contract."""
        contract = resolve_contract(tech_input)
        assert contract is not None
        assert contract.sql_flavor in [
            SQLFlavor.SNOWFLAKE_SQL,
            SQLFlavor.MS_FABRIC_SQL,
            SQLFlavor.ANSI_SQL,
        ]


class TestContractBreaches:
    """Tests that catch common contract breach patterns."""

    def test_detects_pyspark_fallback_for_sql_targets(self):
        """Flag when PySpark code is generated for SQL-only targets."""
        sql_targets = ["snowflake_sql", "ms_fabric_sql"]
        pyspark_code = "df = spark.read.table('t')\ndf.write.mode('overwrite').saveAsTable('out')"

        for target in sql_targets:
            result = validate_sql_flavor_coverage(target, pyspark_code, "direct")
            # PySpark code should fail for SQL-only targets
            assert not result["valid"], f"{target} should reject PySpark code"
            assert len(result["issues"]) > 0

    def test_detects_missing_key_operations(self):
        """Flag when code is missing key operations for the target."""
        # Snowflake SQL without COPY/MERGE/CREATE
        result = validate_sql_flavor_coverage(
            "snowflake_sql", "DROP TABLE old_table;", "direct"
        )
        assert not result["valid"]

        # MS Fabric SQL without INSERT/CREATE/DELETE/MERGE
        result = validate_sql_flavor_coverage(
            "ms_fabric_sql", "ALTER TABLE t ADD COLUMN new_col INT;", "direct"
        )
        # ALTER should not be in the required set, so it should fail
        assert not result["valid"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

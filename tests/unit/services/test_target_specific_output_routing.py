from apps.api.services.agent_c_service import AgentCService
from apps.api.services.migration_orchestrator import MigrationOrchestrator


def test_agent_c_prefers_sql_code_for_sql_targets():
    generated_code, code_field = AgentCService._extract_generated_code_for_target(
        {
            "code": "print('wrong lane')",
            "pyspark_code": "spark.sql('select 1')",
            "sql_code": "select 1 as sql_target;",
        },
        "snowflake_sql",
    )

    assert code_field == "sql_code"
    assert generated_code == "select 1 as sql_target;"


def test_agent_c_prefers_pyspark_code_for_pyspark_targets():
    generated_code, code_field = AgentCService._extract_generated_code_for_target(
        {
            "code": "select 1 as fallback",
            "pyspark_code": "df = spark.table('src')",
            "sql_code": "select * from src;",
        },
        "pyspark",
    )

    assert code_field == "pyspark_code"
    assert generated_code == "df = spark.table('src')"


def test_agent_c_normalization_removes_wrong_language_field_for_sql_targets():
    normalized = AgentCService._normalize_generated_output_fields(
        {
            "code": "create or replace table tgt as select * from src;",
            "pyspark_code": "df.write.saveAsTable('tgt')",
            "mapping_logic": [],
        },
        "snowflake_sql",
    )

    assert normalized["sql_code"] == "create or replace table tgt as select * from src;"
    assert "pyspark_code" not in normalized


def test_agent_c_normalization_removes_wrong_language_field_for_pyspark_targets():
    normalized = AgentCService._normalize_generated_output_fields(
        {
            "code": "df.write.mode('overwrite').saveAsTable('tgt')",
            "sql_code": "create or replace table tgt as select * from src;",
            "mapping_logic": [],
        },
        "pyspark",
    )

    assert normalized["pyspark_code"] == "df.write.mode('overwrite').saveAsTable('tgt')"
    assert "sql_code" not in normalized


def test_orchestrator_routes_generic_code_to_sql_lane_for_sql_targets():
    notebook_content, sql_content, review_code = MigrationOrchestrator._split_generated_content(
        {
            "code": "create or replace table tgt as select * from src;",
            "pyspark_code": "df.write.saveAsTable('tgt')",
        },
        "snowflake_sql",
    )

    assert notebook_content == ""
    assert sql_content == "create or replace table tgt as select * from src;"
    assert review_code == sql_content


def test_orchestrator_routes_generic_code_to_python_lane_for_pyspark_targets():
    notebook_content, sql_content, review_code = MigrationOrchestrator._split_generated_content(
        {
            "code": "df.write.mode('overwrite').saveAsTable('tgt')",
            "sql_code": "create or replace table tgt as select * from src;",
        },
        "pyspark",
    )

    assert notebook_content == "df.write.mode('overwrite').saveAsTable('tgt')"
    assert sql_content == ""
    assert review_code == notebook_content


def test_orchestrator_rejects_invalid_optimized_payload_for_persistence():
    optimized = MigrationOrchestrator._get_valid_optimized_content(
        {
            "optimized_code": '{"status":"REJECTED","critique":["not code"],"score":2}'
        },
        "pyspark",
    )

    assert optimized is None


def test_orchestrator_uses_clean_artifact_base_name_for_sql_sources():
    assert MigrationOrchestrator._artifact_base_name("02_sp_load_dim_cliente.sql") == "02_sp_load_dim_cliente"


def test_orchestrator_primary_artifact_filename_uses_sql_for_sql_targets():
    assert (
        MigrationOrchestrator._primary_artifact_filename("02_sp_load_dim_cliente.sql", "snowflake_sql")
        == "02_sp_load_dim_cliente.sql"
    )
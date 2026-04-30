"""Tests for drafting layer resolution."""

import pytest

from apps.api.services.migration_orchestrator import MigrationOrchestrator


def _orchestrator():
    return object.__new__(MigrationOrchestrator)


def test_ssis_dimension_prefers_silver_over_weak_gold_lineage_group():
    orchestrator = _orchestrator()
    asset_meta = {
        "source_name": "DimCustomers.dtsx",
        "type": "CORE",
        "metadata": {"lineage_group": "Gold"},
    }

    assert orchestrator._resolve_task_layer(asset_meta, "pyspark") == "silver"


def test_ssis_fact_prefers_gold_for_spark_modernization():
    orchestrator = _orchestrator()
    asset_meta = {
        "source_name": "FactSales.dtsx",
        "type": "CORE",
        "metadata": {"lineage_group": "Silver"},
    }

    assert orchestrator._resolve_task_layer(asset_meta, "pyspark") == "gold"


def test_explicit_metadata_layer_still_wins():
    orchestrator = _orchestrator()
    asset_meta = {
        "source_name": "DimCustomers.dtsx",
        "type": "CORE",
        "metadata": {"layer": "gold", "lineage_group": "Silver"},
    }

    assert orchestrator._resolve_task_layer(asset_meta, "pyspark") == "gold"


def test_sql_dimension_prefers_silver_for_snowflake_even_with_weak_bronze():
    orchestrator = _orchestrator()
    asset_meta = {
        "source_name": "01_sp_load_dim_fecha.sql",
        "type": "CORE",
        "metadata": {"lineage_group": "Bronze"},
    }

    assert orchestrator._resolve_task_layer(asset_meta, "snowflake_sql") == "silver"


def test_sql_fact_prefers_gold_for_snowflake():
    orchestrator = _orchestrator()
    asset_meta = {
        "source_name": "05_sp_load_fact_ventas.sql",
        "type": "CORE",
        "metadata": {"lineage_group": "Silver"},
    }

    assert orchestrator._resolve_task_layer(asset_meta, "snowflake_sql") == "gold"


def test_sql_orchestrator_prefers_direct_for_snowflake():
    orchestrator = _orchestrator()
    asset_meta = {
        "source_name": "10_sp_orquestador_etl.sql",
        "type": "CORE",
        "metadata": {"lineage_group": "Bronze"},
    }

    assert orchestrator._resolve_task_layer(asset_meta, "snowflake_sql") == "direct"


def test_direct_snowflake_orchestrator_override_preserves_calls_without_bronze_objects():
    orchestrator = _orchestrator()
    task_def = {
        "layer": "direct",
        "source_name": "10_sp_orquestador_etl.sql",
        "raw_content": """
CREATE PROCEDURE sp_orquestador_etl()
BEGIN
  CALL sp_load_dim_fecha();
  CALL sp_load_fact_ventas();
END
""",
    }

    code = orchestrator._maybe_apply_direct_sql_orchestrator_override(
        task_def,
        "CREATE TABLE bronze_raw.raw_10_sp_orquestador_etl_sql (id number);",
        "snowflake_sql",
    )

    assert code.startswith("-- L2L DIRECT TRANSLATION: 10_sp_orquestador_etl.sql")
    assert "CREATE OR REPLACE PROCEDURE SP_ORQUESTADOR_ETL()" in code
    assert "CALL SP_LOAD_DIM_FECHA()" in code
    assert "CALL SP_LOAD_FACT_VENTAS()" in code
    assert "CALL IDENTIFIER" not in code
    assert "RETURNS VARIANT" not in code
    assert "CONTROL_SCHEMA STRING DEFAULT" not in code
    assert "raw_10_sp_orquestador_etl_sql" not in code
    assert "LAST_INSERT_ID" not in code
    assert "WHERE ID = v_ctrl_id" in code
    assert ":v_master_start" not in code


def test_snowflake_fact_cobros_override_uses_temp_table_and_merge():
    orchestrator = _orchestrator()
    task_def = {
        "layer": "gold",
        "source_name": "06_sp_load_fact_cobros.sql",
        "raw_content": """
CREATE PROCEDURE sp_load_fact_cobros()
BEGIN
  CREATE TEMPORARY TABLE tmp_fact_cobros AS SELECT * FROM pagos;
  UPDATE fact_cobros SET fecha_carga_dw = NOW();
  INSERT INTO fact_cobros SELECT * FROM tmp_fact_cobros;
END
""",
    }

    code = orchestrator._maybe_apply_direct_sql_orchestrator_override(
        task_def,
        "CREATE OR REPLACE TABLE GOLD_BUSINESS.FACT_COBROS AS SELECT 1;",
        "snowflake_sql",
    )

    assert code.startswith("-- L2L MODERNIZATION TRACE: GOLD - 06_sp_load_fact_cobros.sql")
    assert "CREATE OR REPLACE PROCEDURE SP_LOAD_FACT_COBROS()" in code
    assert "CREATE OR REPLACE TEMPORARY TABLE TMP_FACT_COBROS" in code
    assert "MERGE INTO IDENTIFIER($gold_schema || '.FACT_COBROS')" in code
    assert "EXCEPTION" in code
    assert ":v_ctrl_id" not in code
    assert "STRING DEFAULT" not in code


def test_snowflake_dim_fecha_override_avoids_last_insert_id_and_dynamic_proc_wrapper():
    orchestrator = _orchestrator()
    task_def = {
        "layer": "silver",
        "source_name": "01_sp_load_dim_fecha.sql",
        "raw_content": "CREATE PROCEDURE sp_load_dim_fecha() BEGIN INSERT INTO etl_control_cargas VALUES (1); END",
    }

    code = orchestrator._maybe_apply_direct_sql_orchestrator_override(
        task_def,
        "CALL SILVER_CURATED.SP_LOAD_DIM_FECHA();",
        "snowflake_sql",
    )

    assert code.startswith("-- L2L MODERNIZATION TRACE: SILVER - 01_sp_load_dim_fecha.sql")
    assert "LAST_INSERT_ID" not in code
    assert "CREATE OR REPLACE PROCEDURE IDENTIFIER($silver_schema || '.SP_LOAD_DIM_FECHA')" not in code
    assert "MERGE INTO IDENTIFIER($silver_schema || '.DIM_FECHA')" in code


def test_snowflake_dim_cliente_override_uses_two_phase_scd2_and_durable_control_log():
    orchestrator = _orchestrator()
    task_def = {
        "layer": "silver",
        "source_name": "02_sp_load_dim_cliente.sql",
        "raw_content": "CREATE PROCEDURE sp_load_dim_cliente() BEGIN SELECT * FROM clientes; END",
    }

    code = orchestrator._maybe_apply_direct_sql_orchestrator_override(
        task_def,
        "MERGE INTO SILVER_CURATED.DIM_CLIENTE SELECT * FROM TMP;",
        "snowflake_sql",
    )

    assert code.startswith("-- L2L MODERNIZATION TRACE: SILVER - 02_sp_load_dim_cliente.sql")
    assert "CREATE OR REPLACE PROCEDURE SP_LOAD_DIM_CLIENTE()" in code
    assert "TMP_DIM_CLIENTE_CHANGES" in code
    assert "Phase 1: expire changed current rows" in code
    assert "Phase 2: insert new current rows" in code
    assert "CREATE OR REPLACE TEMPORARY TABLE ETL_CONTROL_CARGAS" not in code
    assert "SHA2(COALESCE(LOWER(TRIM(c.nomContacto)), ''), 256) AS CONTACTO" in code
    assert ":v_inicio" not in code


def test_snowflake_dim_cliente_override_matches_alias_name_without_sp_prefix():
    orchestrator = _orchestrator()
    task_def = {
        "layer": "silver",
        "source_name": "dim_cliente",
        "raw_content": "CREATE PROCEDURE sp_load_dim_cliente() BEGIN SELECT * FROM clientes; END",
    }

    code = orchestrator._maybe_apply_direct_sql_orchestrator_override(
        task_def,
        "MERGE INTO SILVER_CURATED.DIM_CLIENTE SELECT * FROM TMP;",
        "snowflake_sql",
    )

    assert code.startswith("-- L2L MODERNIZATION TRACE: SILVER - dim_cliente")
    assert "TMP_DIM_CLIENTE_CHANGES" in code


def test_snowflake_dim_producto_override_avoids_dynamic_procedure_declaration():
    orchestrator = _orchestrator()
    task_def = {
        "layer": "silver",
        "source_name": "03_sp_load_dim_producto.sql",
        "raw_content": "CREATE PROCEDURE sp_load_dim_producto() BEGIN SELECT * FROM productos; END",
    }

    code = orchestrator._maybe_apply_direct_sql_orchestrator_override(
        task_def,
        "CREATE OR REPLACE PROCEDURE IDENTIFIER($silver_schema || '.SP_LOAD_DIM_PRODUCTO')() RETURNS STRING LANGUAGE SQL AS $$ BEGIN RETURN 'bad'; END; $$;",
        "snowflake_sql",
    )

    assert code.startswith("-- L2L MODERNIZATION TRACE: SILVER - 03_sp_load_dim_producto.sql")
    assert "CREATE OR REPLACE PROCEDURE IDENTIFIER" not in code
    assert "CREATE OR REPLACE PROCEDURE SP_LOAD_DIM_PRODUCTO(" in code
    assert "MERGE INTO IDENTIFIER($silver_schema || '.DIM_PRODUCTO') AS target" in code
    assert "QUALIFY ROW_NUMBER() OVER" in code
    assert ":P_SILVER_SCHEMA" not in code
    assert "LAST_INSERT_ID" not in code


def test_snowflake_fact_ingresos_stock_override_precomputes_counts_before_merge():
    orchestrator = _orchestrator()
    task_def = {
        "layer": "gold",
        "source_name": "08_sp_load_fact_ingresos_stock.sql",
        "raw_content": "CREATE PROCEDURE sp_load_fact_ingresos_stock() BEGIN INSERT INTO fact_ingresos_stock SELECT 1; END",
    }

    code = orchestrator._maybe_apply_direct_sql_orchestrator_override(
        task_def,
        "CREATE PROCEDURE SP_LOAD_FACT_INGRESOS_STOCK() RETURNS STRING LANGUAGE SQL AS $$ BEGIN RETURN 'ok'; END; $$;",
        "snowflake_sql",
    )

    assert code.startswith("-- L2L MODERNIZATION TRACE: GOLD - 08_sp_load_fact_ingresos_stock.sql")
    assert "SELECT COUNT(*)\n      INTO :v_upd" in code
    assert "SELECT COUNT(*)\n      INTO :v_ins" in code
    assert "LAST_INSERT_ID" not in code
    assert "MERGE INTO IDENTIFIER($gold_schema || '.FACT_INGRESOS_STOCK')" in code


def test_snowflake_fact_ventas_override_wraps_merge_in_procedure_and_parameterizes_source_schema():
    orchestrator = _orchestrator()
    task_def = {
        "layer": "gold",
        "source_name": "05_sp_load_fact_ventas.sql",
        "raw_content": "CREATE PROCEDURE sp_load_fact_ventas() BEGIN INSERT INTO fact_ventas SELECT 1; END",
    }

    code = orchestrator._maybe_apply_direct_sql_orchestrator_override(
        task_def,
        "FROM IDENTIFIER('u136155607_nalub.pedidos') p;",
        "snowflake_sql",
    )

    assert code.startswith("-- L2L MODERNIZATION TRACE: GOLD - 05_sp_load_fact_ventas.sql")
    assert "CREATE OR REPLACE PROCEDURE SP_LOAD_FACT_VENTAS()" in code
    assert "FROM IDENTIFIER($source_schema || '.PEDIDOS') p" in code
    assert "MERGE INTO IDENTIFIER($gold_schema || '.FACT_VENTAS') AS tgt" in code
    assert "u136155607_nalub.pedidos" not in code


def test_snowflake_fact_aplicacion_cobros_override_wraps_exception_in_valid_block():
    orchestrator = _orchestrator()
    task_def = {
        "layer": "gold",
        "source_name": "07_sp_load_fact_aplicacion_cobros.sql",
        "raw_content": "CREATE PROCEDURE sp_load_fact_aplicacion_cobros() BEGIN INSERT INTO fact_aplicacion_cobros SELECT 1; END",
    }

    code = orchestrator._maybe_apply_direct_sql_orchestrator_override(
        task_def,
        "MERGE INTO GOLD_BUSINESS.FACT_APLICACION_COBROS SELECT 1; EXCEPTION WHEN OTHER THEN RAISE;",
        "snowflake_sql",
    )

    assert code.startswith("-- L2L MODERNIZATION TRACE: GOLD - 07_sp_load_fact_aplicacion_cobros.sql")
    assert "CREATE OR REPLACE PROCEDURE SP_LOAD_FACT_APLICACION_COBROS()" in code
    assert "MERGE INTO IDENTIFIER($gold_schema || '.FACT_APLICACION_COBROS')" in code
    assert "EXCEPTION\n    WHEN OTHER THEN" in code
    assert ":v_ctrl_id" not in code
    assert "LAST_INSERT_ID" not in code
    assert "DELIMITER" not in code


def test_snowflake_sql_residue_sanitizer_removes_dynamic_proc_calls_and_last_insert_id():
    orchestrator = _orchestrator()
    code = """
SET gold_schema = 'GOLD_BUSINESS';
CREATE OR REPLACE PROCEDURE IDENTIFIER($gold_schema || '.SP_LOAD_FACT_VENTAS')()
RETURNS STRING
LANGUAGE SQL
AS
$$
BEGIN
    assert "CREATE OR REPLACE PROCEDURE SP_LOAD_FACT_COBROS()" in code
    v_ctrl_id := LAST_INSERT_ID();
    CALL IDENTIFIER($gold_schema || '.SP_LOAD_DIM_CLIENTE')();
END;
    assert ":v_ctrl_id" not in code
"""

    sanitized = orchestrator._sanitize_snowflake_sql_residue(code, "snowflake_sql")

    assert "CREATE OR REPLACE PROCEDURE SP_LOAD_FACT_VENTAS()" in sanitized
    assert "CALL SP_LOAD_DIM_CLIENTE()" in sanitized
    assert "LAST_INSERT_ID" not in sanitized
    assert "CREATE OR REPLACE PROCEDURE IDENTIFIER" not in sanitized
    assert "CALL IDENTIFIER" not in sanitized


def test_snowflake_fact_ingresos_stock_override_matches_alias_name_without_sp_prefix():
    orchestrator = _orchestrator()
    task_def = {
        "layer": "gold",
        "source_name": "fact_ingresos_stock",
        "raw_content": "CREATE PROCEDURE sp_load_fact_ingresos_stock() BEGIN INSERT INTO fact_ingresos_stock SELECT 1; END",
    }

    code = orchestrator._maybe_apply_direct_sql_orchestrator_override(
        task_def,
        "CREATE PROCEDURE IDENTIFIER($gold_schema || '.SP_LOAD_FACT_INGRESOS_STOCK')() RETURNS STRING LANGUAGE SQL AS $$ BEGIN RETURN 'ok'; END; $$;",
        "snowflake_sql",
    )

    assert code.startswith("-- L2L MODERNIZATION TRACE: GOLD - fact_ingresos_stock")
    assert "LAST_INSERT_ID" not in code
    assert "MERGE INTO IDENTIFIER($gold_schema || '.FACT_INGRESOS_STOCK')" in code


def test_snowflake_snapshots_override_preserves_delete_then_insert_semantics():
    orchestrator = _orchestrator()
    task_def = {
        "layer": "gold",
        "source_name": "09_sp_load_snapshots.sql",
        "raw_content": "CREATE PROCEDURE sp_load_fact_cartera_snapshot() BEGIN DELETE FROM fact_cartera_snapshot; END",
    }

    code = orchestrator._maybe_apply_direct_sql_orchestrator_override(
        task_def,
        "MERGE INTO GOLD_BUSINESS.FACT_CARTERA_SNAPSHOT SELECT 1;",
        "snowflake_sql",
    )

    assert code.startswith("-- L2L MODERNIZATION TRACE: GOLD - 09_sp_load_snapshots.sql")
    assert "CREATE OR REPLACE PROCEDURE SP_LOAD_FACT_CARTERA_SNAPSHOT(" in code
    assert "CREATE OR REPLACE PROCEDURE SP_LOAD_FACT_INVENTARIO_SNAPSHOT(" in code
    assert "DELETE FROM IDENTIFIER($gold_schema || '.FACT_CARTERA_SNAPSHOT')" in code
    assert "DELETE FROM IDENTIFIER($gold_schema || '.FACT_INVENTARIO_SNAPSHOT')" in code
    assert "RETURN 'sp_load_fact_cartera_snapshot OK';\nEXCEPTION" in code
    assert "RETURN 'sp_load_fact_inventario_snapshot OK';\nEXCEPTION" in code
    assert "EXCEPTION\n    WHEN OTHER THEN\n" in code
    assert "EXCEPTION\n    WHEN OTHER THEN\n        v_msg_error := SQLERRM;\n        IF (v_ctrl_id IS NOT NULL) THEN\n            UPDATE IDENTIFIER($gold_schema || '.ETL_CONTROL_CARGAS')\n               SET FECHA_FIN = CURRENT_TIMESTAMP(),\n                   ESTADO = 'ERROR',\n                   MENSAJE_ERROR = v_msg_error\n             WHERE ID = v_ctrl_id;\n        END IF;\n        RAISE;\nEND;\n\n    RETURN" not in code
    assert ":P_GOLD_SCHEMA" not in code
    assert "SP_LOAD_SNAPSHOTS(" not in code
    assert "SET V_INS_CARTERA" not in code


def test_rejected_audit_is_retryable_once_when_feedback_exists():
    orchestrator = _orchestrator()
    audit_report = {
        "status": "REJECTED",
        "critique": ["Uses MySQL DELIMITER", "Missing Snowflake exception handling"],
        "violations": ["mysql_residue"],
    }

    assert orchestrator._should_retry_after_audit(audit_report, "snowflake_sql", {}) is True
    assert orchestrator._should_retry_after_audit(audit_report, "snowflake_sql", {"retry_attempt": 1}) is False


def test_retry_task_def_injects_structured_agent_f_feedback_and_seed_code():
    orchestrator = _orchestrator()
    task_def = {
        "name": "03_sp_load_dim_producto.sql",
        "support_intelligence": [{"type": "baseline"}],
        "scout_assessment": {"detected_gaps": ["legacy_gap"]},
    }
    audit_report = {
        "status": "REJECTED",
        "critique": ["Missing _IS_CURRENT"],
        "violations": ["bad_scd2_pattern"],
        "optimized_code": "CREATE OR REPLACE PROCEDURE SP_LOAD_DIM_PRODUCTO() RETURNS VARCHAR LANGUAGE SQL AS $$ BEGIN RETURN 'ok'; END; $$;",
    }

    retry_task = orchestrator._build_retry_task_def(task_def, audit_report, "SELECT 1", "snowflake_sql")

    assert retry_task["retry_attempt"] == 1
    assert retry_task["previous_generated_code"].startswith("CREATE OR REPLACE PROCEDURE SP_LOAD_DIM_PRODUCTO")
    assert retry_task["agent_f_retry_feedback"]["must_fix"] == ["Missing _IS_CURRENT", "bad_scd2_pattern"]
    assert retry_task["support_intelligence"][-1]["type"] == "agent_f_retry_contract"
    assert "Missing _IS_CURRENT" in retry_task["scout_assessment"]["detected_gaps"]


@pytest.mark.anyio
async def test_retry_rejected_code_once_reaudits_with_retry_payload():
    orchestrator = _orchestrator()
    captured = {}

    class FakeAgentC:
        async def transpile_task(self, node_data, context=None, set_context=None):
            captured["node_data"] = node_data
            captured["set_context"] = set_context
            return {
                "sql_code": "CREATE OR REPLACE PROCEDURE SP_LOAD_DIM_PRODUCTO() RETURNS VARCHAR LANGUAGE SQL AS $$ BEGIN RETURN 'ok'; END; $$;",
                "code": "CREATE OR REPLACE PROCEDURE SP_LOAD_DIM_PRODUCTO() RETURNS VARCHAR LANGUAGE SQL AS $$ BEGIN RETURN 'ok'; END; $$;",
            }

    class FakeAgentF:
        async def review_code(self, task_info, generated_code, project_id=None):
            captured["review_task_info"] = task_info
            captured["review_generated_code"] = generated_code
            captured["project_id"] = project_id
            return {
                "status": "IMPROVED",
                "score": 8,
                "optimized_code": generated_code,
            }

    orchestrator.agent_c = FakeAgentC()
    orchestrator.agent_f = FakeAgentF()
    orchestrator.project_uuid = "project-uuid"

    task_def = {
        "name": "11_sp_load_dim_proveedor.sql",
        "source_name": "11_sp_load_dim_proveedor.sql",
        "layer": "silver",
    }
    audit_report = {
        "status": "REJECTED",
        "critique": ["Missing _IS_CURRENT"],
        "violations": ["bad_scd2_pattern"],
        "optimized_code": "CREATE OR REPLACE PROCEDURE SP_LOAD_DIM_PRODUCTO_PREV() RETURNS VARCHAR LANGUAGE SQL AS $$ BEGIN RETURN 'retry-seed'; END; $$;",
    }

    retry_outcome = await orchestrator._retry_rejected_code_once(
        task_def,
        [{"name": "neighbor_asset"}],
        "snowflake_sql",
        "SELECT 1",
        audit_report,
    )

    assert retry_outcome is not None
    assert captured["node_data"]["retry_attempt"] == 1
    assert captured["node_data"]["agent_f_retry_feedback"]["must_fix"] == ["Missing _IS_CURRENT", "bad_scd2_pattern"]
    assert captured["node_data"]["previous_generated_code"].startswith("CREATE OR REPLACE PROCEDURE SP_LOAD_DIM_PRODUCTO_PREV")
    assert captured["review_generated_code"].startswith("CREATE OR REPLACE PROCEDURE SP_LOAD_DIM_PRODUCTO()")
    assert retry_outcome["audit_report"]["status"] == "IMPROVED"

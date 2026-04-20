from apps.api.services.agent_f_service import AgentFService


def test_normalize_drafting_direct_keeps_rejected_for_trivial_select_star_sql():
    audit = {
        "status": "REJECTED",
        "score": 4,
        "critique": [
            "Layer metadata is SILVER, but generated header says direct.",
            "SELECT * is too permissive for metadata-rich assets.",
        ],
    }

    sql_code = """
CREATE OR REPLACE TABLE IDENTIFIER($target_table) AS
SELECT *
FROM IDENTIFIER($source_table);
""".strip()

    out = AgentFService._normalize_drafting_direct_review(
        audit_report=audit,
        generated_code=sql_code,
        target_tech="snowflake_sql_native",
        review_layer="direct",
        post_drafting_mode=None,
    )

    assert out["status"] == "REJECTED"


def test_normalize_drafting_direct_keeps_rejected_for_non_executable_sql():
    audit = {
        "status": "REJECTED",
        "score": 4,
        "critique": ["Code is too generic"],
    }

    out = AgentFService._normalize_drafting_direct_review(
        audit_report=audit,
        generated_code="this is not sql",
        target_tech="snowflake_sql_native",
        review_layer="direct",
        post_drafting_mode=None,
    )

    assert out["status"] == "REJECTED"


def test_normalize_drafting_direct_keeps_non_layer_critiques():
    audit = {
        "status": "REJECTED",
        "score": 5,
        "critique": [
            "The code uses SELECT * and should provide explicit mappings.",
            "Layer metadata indicates SILVER and should enforce SCD2.",
        ],
    }

    sql_code = """
CREATE OR REPLACE TABLE IDENTIFIER($target_table) AS
SELECT *
FROM IDENTIFIER($source_table);
""".strip()

    out = AgentFService._normalize_drafting_direct_review(
        audit_report=audit,
        generated_code=sql_code,
        target_tech="snowflake_sql_native",
        review_layer="direct",
        post_drafting_mode=None,
    )

    critiques = out.get("critique", [])
    assert out["status"] == "REJECTED"
    assert any("SELECT *" in c for c in critiques)


def test_normalize_drafting_direct_keeps_rejected_for_procedural_source_stub_sql():
    audit = {
        "status": "REJECTED",
        "score": 4,
        "critique": [
            "The procedure logic was collapsed into a generic CTAS.",
        ],
    }

    sql_code = """
CREATE OR REPLACE TABLE IDENTIFIER($target_table) AS
SELECT *
FROM IDENTIFIER($source_table);
""".strip()

    out = AgentFService._normalize_drafting_direct_review(
        audit_report=audit,
        generated_code=sql_code,
        target_tech="snowflake_sql_native",
        review_layer="direct",
        post_drafting_mode=None,
        task_info={
            "raw_content": """
CREATE PROCEDURE sp_load_dim_cliente()
BEGIN
    DECLARE v_ctrl_id INT;
    CREATE TEMPORARY TABLE tmp_clientes_origen AS SELECT * FROM clientes;
    UPDATE dim_cliente SET es_vigente = 0;
END
""".strip(),
        },
    )

    assert out["status"] == "REJECTED"


def test_sanitize_audit_report_ignores_json_envelope_in_optimized_code():
    audit = {
        "status": "IMPROVED",
        "score": 7,
        "optimized_code": '{"status":"REJECTED","critique":["bad"],"score":2}',
        "critique": [],
    }

    out = AgentFService._sanitize_audit_report(
        audit_report=audit,
        generated_code="SELECT 1;",
        target_tech="snowflake_sql",
    )

    assert out["optimized_code"] == "SELECT 1;"
    assert any("Invalid optimized_code payload was ignored" in item for item in out["critique"])


def test_normalize_drafting_direct_keeps_rejected_for_compile_invalid_sql():
    audit = {
        "status": "REJECTED",
        "score": 5,
        "critique": [
            "LAST_INSERT_ID() is not valid in Snowflake SQL and breaks the transpilation.",
            "The generated procedure is not self-contained or executable because required identifiers are not defined in the procedure signature.",
        ],
    }

    sql_code = """
CREATE OR REPLACE PROCEDURE IDENTIFIER($target_table)()
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
BEGIN
    v_ctrl_id := LAST_INSERT_ID();
END;
$$;
""".strip()

    out = AgentFService._normalize_drafting_direct_review(
        audit_report=audit,
        generated_code=sql_code,
        target_tech="snowflake_sql_native",
        review_layer="direct",
        post_drafting_mode=None,
    )

    assert out["status"] == "REJECTED"


def test_normalize_drafting_direct_keeps_rejected_for_live_snowflake_runtime_invalidity():
    audit = {
        "status": "REJECTED",
        "score": 5,
        "critique": [
            "The generated procedure is not valid for Snowflake SQL Native because CREATE OR REPLACE PROCEDURE IDENTIFIER($target_table) is not a valid procedure signature.",
            "The code calls LAST_INSERT_ID(), which is a MySQL construct and not valid Snowflake SQL. This is a functional compatibility issue and prevents execution in the target platform.",
            "Because the code is not executable as a standalone Snowflake SQL procedure and does not preserve a valid parameter contract, it fails direct translation functional equivalence and runtime compliance.",
        ],
    }

    sql_code = """
CREATE OR REPLACE PROCEDURE IDENTIFIER($target_table)
RETURNS STRING
LANGUAGE SQL
AS
$$
BEGIN
    v_ctrl_id := LAST_INSERT_ID();
END;
$$;
""".strip()

    out = AgentFService._normalize_drafting_direct_review(
        audit_report=audit,
        generated_code=sql_code,
        target_tech="snowflake_sql_native",
        review_layer="direct",
        post_drafting_mode=None,
    )

    assert out["status"] == "REJECTED"


def test_normalize_drafting_direct_keeps_rejected_for_live_dynamic_sql_invalidity():
    audit = {
        "status": "REJECTED",
        "score": 5,
        "critique": [
            "The procedure signature is invalid for Snowflake SQL: CREATE OR REPLACE PROCEDURE IDENTIFIER($target_table)(...) is not a legal way to define a procedure name.",
            "Error handling and logging are partially present, but the overall routine is not production-ready due to invalid Snowflake SQL syntax in multiple EXECUTE IMMEDIATE blocks and the final CALL statement.",
            "The generated artifact is not directly executable as written due to syntax issues around dynamic SQL, procedure definition, and runtime variable binding.",
        ],
    }

    sql_code = """
CREATE OR REPLACE PROCEDURE IDENTIFIER($target_table)(SOURCE_TABLE VARCHAR, TARGET_TABLE VARCHAR, CONTROL_TABLE VARCHAR)
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
BEGIN
    EXECUTE IMMEDIATE 'SELECT 1';
END;
$$;
""".strip()

    out = AgentFService._normalize_drafting_direct_review(
        audit_report=audit,
        generated_code=sql_code,
        target_tech="snowflake_sql_native",
        review_layer="direct",
        post_drafting_mode=None,
    )

    assert out["status"] == "REJECTED"

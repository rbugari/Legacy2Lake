from apps.api.services.refinement.cartridges.pyspark_cartridge import PySparkCartridge
from apps.api.services.refinement.cartridges.snowflake_cartridge import SnowflakeCartridge
from apps.api.services.refinement.refactoring_service import RefactoringService


def test_pyspark_scaffolding_is_portable_by_default():
    cartridge = PySparkCartridge(
        project_id="project-1",
        design_registry={"paths": {"target_stack": "pyspark"}, "naming": {}},
    )

    scaffolding = cartridge.generate_scaffolding()
    config_code = scaffolding["config.py"]

    assert "dbutils" not in config_code
    assert "/mnt/" not in config_code
    assert "os.getenv" in config_code


def test_pyspark_orchestration_avoids_databricks_for_generic_target():
    cartridge = PySparkCartridge(
        project_id="project-1",
        design_registry={"paths": {"target_stack": "pyspark"}, "naming": {}},
    )

    orchestration = cartridge.generate_orchestration([{"table_name": "dim_customer"}])

    assert "DatabricksRunNowOperator" not in orchestration
    assert "dag_databricks" not in orchestration
    assert "TASK_ORDER" in orchestration
    assert "dim_customer" in orchestration


def test_refactoring_notes_are_portable_for_generic_pyspark(monkeypatch):
    saved = {}

    class FakeStorage:
        def read_file(self, file_key):
            return "print('ok')\n"

        def save_file(self, file_key, content):
            saved[file_key] = content

    monkeypatch.setattr(
        "apps.api.services.refinement.refactoring_service.PersistenceService.get_storage",
        lambda: FakeStorage(),
    )

    service = RefactoringService()

    import anyio

    anyio.run(service._apply_refactoring, "demo/refinement/gold/dim_gold.py", "pyspark", [])

    content = saved["demo/refinement/gold/dim_gold.py"]
    assert "Z-ORDERING" not in content
    assert "dbutils" not in content
    assert "generic Spark tuning portable" in content


def test_snowflake_sql_scaffolding_uses_concrete_schema_names():
    cartridge = SnowflakeCartridge(
        project_id="project-1",
        design_registry={"paths": {"target_stack": "snowflake_sql"}, "naming": {}},
    )

    silver_sql = cartridge.generate_silver_sql(
        {"source_path": "01_fecha.sql", "output_table_name": "dim_fecha", "pk_columns": ["id_fecha"]}
    )
    gold_sql = cartridge.generate_gold_sql({"source_path": "05_ventas.sql", "output_table_name": "fact_ventas"})

    assert "{Config." not in silver_sql
    assert "{Config." not in gold_sql
    assert "SILVER_CURATED.DIM_FECHA" in silver_sql
    assert "GOLD_BUSINESS.FACT_VENTAS" in gold_sql
    assert "BRONZE_RAW.T_01_FECHA" in silver_sql
    assert "SILVER_CURATED.T_05_VENTAS" in gold_sql


def test_refactoring_notes_use_sql_comments_for_snowflake_sql(monkeypatch):
    saved = {}

    class FakeStorage:
        def read_file(self, file_key):
            return "SELECT 1;\n"

        def save_file(self, file_key, content):
            saved[file_key] = content

    monkeypatch.setattr(
        "apps.api.services.refinement.refactoring_service.PersistenceService.get_storage",
        lambda: FakeStorage(),
    )

    service = RefactoringService()

    import anyio

    anyio.run(service._apply_refactoring, "demo/refinement/gold/fact.sql", "snowflake_sql", [])

    content = saved["demo/refinement/gold/fact.sql"]
    assert content.startswith("-- [Refactoring Agent]")
    assert "# [Refactoring Agent]" not in content
    assert "Config.get_session" not in content

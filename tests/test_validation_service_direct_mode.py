"""Tests for direct-mode no-hardcode validation behavior."""

import asyncio

from apps.api.services.validation_service import ValidationService


def test_direct_mode_rejects_hardcoded_literals_in_pyspark():
    code = '''
from pyspark.sql import SparkSession

CATALOG = "main"
SCHEMA_SILVER = "silver_curated"
TARGET_TABLE = "main.silver_curated.stg_dim_customer"

spark = SparkSession.builder.getOrCreate()
df = spark.read.table("hive_metastore.bronze_raw.dim_customer")
df.write.mode("overwrite").saveAsTable("main.silver_curated.stg_dim_customer")
'''

    validator = ValidationService()
    result = asyncio.run(validator.validate_code(code=code, tech_id="pyspark", layer="direct"))

    assert result.is_valid is False
    assert any(issue.check_name == "direct_no_hardcode" for issue in result.issues)


def test_direct_mode_accepts_config_driven_pyspark_values():
    code = '''
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()
config = {"catalog": "main", "source_table": "bronze.tbl", "target_table": "silver.tbl"}

catalog = config.get("catalog")
source_table = config.get("source_table")
target_table = config.get("target_table")

df = spark.read.table(source_table)
df.write.mode("overwrite").saveAsTable(target_table)
'''

    validator = ValidationService()
    result = asyncio.run(validator.validate_code(code=code, tech_id="pyspark", layer="direct"))

    assert not any(issue.check_name == "direct_no_hardcode" for issue in result.issues)


def test_direct_mode_rejects_literal_defaults_inside_config_get():
    code = '''
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()
config = globals().get("config", {})

package_table_name = config.get("package_table_name", "DimCustomers.dtsx")
source_object_name = config.get("source_object_name", "Sales.Customers")
target_table = config.get("target_table", "silver.dim_customers")

df = spark.read.table(source_object_name)
df.write.mode("overwrite").saveAsTable(target_table)
'''

    validator = ValidationService()
    result = asyncio.run(validator.validate_code(code=code, tech_id="pyspark", layer="direct"))

    assert result.is_valid is False
    assert any(issue.check_name == "direct_no_hardcode" for issue in result.issues)


def test_direct_mode_rejects_helper_variable_literal_assignment():
    code = '''
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()
package_table_name = "DimCustomers.dtsx"
source_object_name = "Sales.Customers"
target_path = "/mnt/silver/dim_customers"

df = spark.read.table(source_object_name)
df.write.mode("overwrite").parquet(target_path)
'''

    validator = ValidationService()
    result = asyncio.run(validator.validate_code(code=code, tech_id="pyspark", layer="direct"))

    assert result.is_valid is False
    assert any(issue.check_name == "direct_no_hardcode" for issue in result.issues)


def test_direct_mode_allows_format_mode_type_defaults_in_config_get():
    """Regression: config.get("source_format", "table") must NOT be flagged as hardcode.
    The key suffix _format/_mode/_type indicates an operational setting, not a DB object name."""
    code = '''
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()
config = globals().get("config", {})

def execute_task(spark, config):
    df = spark.read.format(config.get("source_format", "table")).load(config.get("source_path"))
    load_mode = config.get("load_mode", "overwrite")
    source_type = config.get("source_type", "jdbc")
    df.write.mode(load_mode).saveAsTable(config.get("target_table"))
    return {"status": "ok"}
'''

    validator = ValidationService()
    result = asyncio.run(validator.validate_code(code=code, tech_id="pyspark", layer="direct"))

    assert not any(issue.check_name == "direct_no_hardcode" for issue in result.issues)


def test_pyspark_validation_allows_multiline_f_string_sql_placeholders():
    code = '''
from pyspark.sql import functions as F

def execute_task(spark, config):
    target_table = config["target_table_name"]
    source_table = config["source_table_name"]

    df = spark.read.table(source_table)
    df = df.withColumn("_updated_at", F.current_timestamp())
    df.write.mode("overwrite").saveAsTable(target_table)

    spark.sql(f"""
        MERGE INTO {target_table} target
        USING staging_view source
        ON target.id = source.id
        WHEN MATCHED THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *
    """)

    return {"status": "completed"}
'''

    validator = ValidationService()
    result = asyncio.run(validator.validate_code(code=code, tech_id="pyspark", layer="silver"))

    assert not any(issue.check_name == "unresolved_placeholders" for issue in result.issues)

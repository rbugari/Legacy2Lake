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

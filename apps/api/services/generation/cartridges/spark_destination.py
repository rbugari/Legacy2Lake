from .base_destination import DestinationCartridge
from typing import List, Dict, Any

class SparkDestination(DestinationCartridge):
    """
    Generator for Apache Spark / Databricks (PySpark).
    """

    def generate_ddl(self, table_metadata: Dict[str, Any]) -> str:
        table_name = table_metadata.get("name", "untitled")
        columns = table_metadata.get("columns", [])
        
        # Simple DDL generation logic for Delta Lake
        # In real usage, this would iterate columns mapping types
        return f"CREATE TABLE IF NOT EXISTS {table_name} USING DELTA;"

    def generate_code(self, source_asset: Dict[str, Any], transformation_logic: str) -> str:
        """
        Generates PySpark code.
        """
        source_name = source_asset.get("name", "source_table")
        
        return f"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import *

spark = SparkSession.builder.appName("Migration_{source_name}").getOrCreate()

# Read Source
df = spark.read.table("{source_name}")

# Transformation (Injected Logic)
# {transformation_logic}

# Write to Delta
df.write.format("delta").mode("overwrite").saveAsTable("target_{source_name}")
"""

    def get_supported_types(self) -> Dict[str, str]:
        return {
            "INTEGER": "IntegerType",
            "VARCHAR": "StringType",
            "DATE": "DateType",
            "TIMESTAMP": "TimestampType"
        }

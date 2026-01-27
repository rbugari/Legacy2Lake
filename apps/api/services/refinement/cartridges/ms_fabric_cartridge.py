from pathlib import Path
from typing import Dict, Any, List
import json
from .base_cartridge import Cartridge

class MSFabricCartridge(Cartridge):
    """
    Generates Microsoft Fabric (PySpark Notebooks + T-SQL) code for Medallion Architecture.
    Optimized for Lakehouse workloads.
    """

    def get_file_extension(self) -> str:
        # Default for Fabric Notebooks is typically .py, but we provide SQL too.
        return ".py"

    def generate_scaffolding(self) -> Dict[str, str]:
        """Generates configuration and utilities tailored for MS Fabric Lakehouses."""
        naming = self.registry.get("naming", {})
        
        s_bronze = naming.get("bronze_schema", "bronze")
        s_silver = naming.get("silver_schema", "silver")
        s_gold = naming.get("gold_schema", "gold")
        
        config_content = f"""# Microsoft Fabric Lakehouse Configuration
# This file centralizes the path and schema mapping for the Medallion Architecture.

class Config:
    # Lakehouse Names / Schemas
    LAKEHOUSE_BRONZE = "{s_bronze}"
    LAKEHOUSE_SILVER = "{s_silver}"
    LAKEHOUSE_GOLD = "{s_gold}"
    
    # Path constants if needed for direct ABFSS access
    # Example: "abfss://<workspace-id>@onelake.dfs.fabric.microsoft.com/<item-id>/Tables/"
    
    @staticmethod
    def get_table_path(lakehouse, table_name):
        return f"{{lakehouse}}.{{table_name}}"
"""

        utils_content = """# Microsoft Fabric / Spark Utils
from pyspark.sql import functions as F

def add_audit_columns(df):
    \"\"\"Applies standard MS Fabric audit columns.\"\"\"
    return df.withColumn("_FabricIngestTime", F.current_timestamp()) \\
             .withColumn("_SourceSystem", F.lit("Legacy2Lake_UTM"))

def optimize_table(table_name):
    \"\"\"Runs VORDER and OPTIMIZE for Fabric performance.\"\"\"
    spark.sql(f"OPTIMIZE {table_name}")
"""
        return {
            "fabric_config.py": config_content,
            "fabric_utils.py": utils_content
        }

    def generate_bronze(self, table_metadata: Dict[str, Any]) -> str:
        source_path = Path(table_metadata.get("source_path", "unknown_source.py"))
        original_code = table_metadata.get("original_code", "")
        
        # Disable original side effects
        processed_lines = []
        for line in original_code.splitlines():
            if any(x in line for x in [".write", ".save", "saveAsTable", "display("]):
                processed_lines.append(f"# [DISABLED] {line}")
            else:
                processed_lines.append(line)
        original_code_safe = "\n".join(processed_lines)
        
        return f"""# MS FABRIC - BRONZE LAYER (Notebook)
# Generated for Microsoft Fabric Lakehouse integration
# Source: {source_path.name}

from fabric_config import Config
from fabric_utils import add_audit_columns

# [LOAD RAW DATA]
{original_code_safe}

# Check if df exists (adapting from legacy logic)
if 'df' not in locals() and 'df_source' in locals():
    df = df_source

# Apply Fabric Bronze Standard
df_bronze = add_audit_columns(df)

# Save to Lakehouse Tables
target_table = f"{{Config.LAKEHOUSE_BRONZE}}.{source_path.stem}"
df_bronze.write.format("delta").mode("append").saveAsTable(target_table)

print(f"Ingested to Bronze: {{target_table}}")
"""

    def generate_silver(self, table_metadata: Dict[str, Any]) -> str:
        source_path = Path(table_metadata.get("source_path", "unknown.py"))
        output_table_name = table_metadata.get("output_table_name", source_path.stem)
        pk_columns = table_metadata.get("pk_columns", ["id"])
        if isinstance(pk_columns, str): pk_columns = [pk_columns]
        
        merge_condition = " AND ".join([f"target.{pk} = source.{pk}" for pk in pk_columns])

        return f"""# MS FABRIC - SILVER LAYER (Notebook)
# Data Cleaning & Standardization
# Primary Keys: {", ".join(pk_columns)}

from fabric_config import Config

# Read from Bronze
df_raw = spark.read.table(f"{{Config.LAKEHOUSE_BRONZE}}.{source_path.stem}")

# Basic Deduplication
df_silver = df_raw.dropDuplicates({pk_columns})

# Upsert into Silver using Delta Merge
target_table = f"{{Config.LAKEHOUSE_SILVER}}.{output_table_name}"

from delta.tables import DeltaTable

if spark.catalog.tableExists(target_table):
    dt = DeltaTable.forName(spark, target_table)
    dt.alias("target").merge(
        df_silver.alias("source"),
        "{merge_condition}"
    ).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
else:
    df_silver.write.format("delta").mode("overwrite").saveAsTable(target_table)

print(f"Silver Layer updated: {{target_table}}")
"""

    def generate_gold(self, table_metadata: Dict[str, Any]) -> str:
        source_path = Path(table_metadata.get("source_path", "unknown.py"))
        output_table_name = table_metadata.get("output_table_name", source_path.stem)
        table_type = table_metadata.get("table_type", "DIMENSION")
        
        return f"""# MS FABRIC - GOLD LAYER (Semantic View)
# Business-ready data for Power BI / Reporting

from fabric_config import Config

# Read from Silver
df_silver = spark.read.table(f"{{Config.LAKEHOUSE_SILVER}}.{output_table_name}")

# Project Gold Logic (can be customized via prompt)
df_gold = df_silver.select("*")

# Write to Gold Lakehouse
target_table = f"{{Config.LAKEHOUSE_GOLD}}.{output_table_name}"
df_gold.write.format("delta").mode("overwrite").saveAsTable(target_table)

print(f"Gold Layer updated: {{target_table}}")
"""

    def generate_bronze_sql(self, table_metadata: Dict[str, Any]) -> str:
        """T-SQL for Fabric SQL Warehouse ingestion."""
        source_path = Path(table_metadata.get("source_path", "unknown"))
        return f"""-- MS FABRIC BRONZE (T-SQL)
-- Target: {source_path.stem}

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = '{source_path.stem}')
BEGIN
    CREATE TABLE bronze.{source_path.stem} AS 
    SELECT *, GETDATE() as [_FabricIngestTime]
    FROM raw_staging.{source_path.stem};
END
ELSE
BEGIN
    INSERT INTO bronze.{source_path.stem}
    SELECT *, GETDATE() as [_FabricIngestTime]
    FROM raw_staging.{source_path.stem};
END;
"""

    def generate_silver_sql(self, table_metadata: Dict[str, Any]) -> str:
        """T-SQL for Fabric SQL Warehouse merge."""
        output_table_name = table_metadata.get("output_table_name", "silver_table")
        pk_columns = table_metadata.get("pk_columns", ["id"])
        if isinstance(pk_columns, str): pk_columns = [pk_columns]
        
        merge_cond = " AND ".join([f"T.[{pk}] = S.[{pk}]" for pk in pk_columns])
        
        return f"""-- MS FABRIC SILVER (T-SQL MERGE)
-- Fabric Warehouse supports standard T-SQL MERGE

MERGE INTO silver.[{output_table_name}] AS T
USING (
    SELECT DISTINCT * FROM bronze.[{output_table_name}]
) AS S
ON {merge_cond}
WHEN MATCHED THEN
    UPDATE SET T.[_UpdateDate] = GETDATE() -- Simplified
WHEN NOT MATCHED THEN
    INSERT (*) VALUES (S.*);
"""

    def generate_gold_sql(self, table_metadata: Dict[str, Any]) -> str:
        """T-SQL for Fabric Gold Views."""
        output_table_name = table_metadata.get("output_table_name", "gold_table")
        return f"""-- MS FABRIC GOLD (VIEW)
CREATE OR ALTER VIEW gold.[v_{output_table_name}]
AS
SELECT * FROM silver.[{output_table_name}];
"""

    def generate_semantic_model(self, table_metadata: Dict[str, Any]) -> str:
        """Generates Power BI Semantic Model definition in TMDL format."""
        output_table_name = table_metadata.get("output_table_name", "gold_table")
        s_gold = self.registry.get("naming", {}).get("gold_schema", "gold")
        
        # Simple TMDL representation for a table and basic measure
        return f"""table {output_table_name}
	lineageTag: {output_table_name}-tag

	partition Partition1 = m
		mode: import
		source =
			let
				Source = Lakehouse.Contents(null){{ [Name="{s_gold}"] }}[Data],
				Table = Source{{ [Name="{output_table_name}"] }}[Data]
			in
				Table

	measure 'Total Records' = COUNTROWS('{output_table_name}')
		formatString: #,0
		displayFolder: "Base Measures"

	column id
		dataType: string
		sourceColumn: id
		summarizeBy: none

	column _FabricIngestTime
		dataType: dateTime
		formatString: General Date
		sourceColumn: _FabricIngestTime
		summarizeBy: none
"""

    def generate_orchestration(self, tables_metadata: List[Dict[str, Any]]) -> str:
        """Generates a Microsoft Fabric Pipeline definition (JSON)."""
        pipeline = {
            "name": f"UTM_Orchestration_{self.project_id}",
            "properties": {
                "activities": []
            }
        }
        
        for table in tables_metadata:
            name = table['table_name']
            
            # Bronze Activity
            act_bronze = {
                "name": f"{name}_Bronze",
                "type": "RunNotebook",
                "typeProperties": {
                    "notebook": {"referenceName": f"{name}_bronze", "type": "NotebookReference"}
                }
            }
            
            # Silver Activity
            act_silver = {
                "name": f"{name}_Silver",
                "type": "RunNotebook",
                "dependsOn": [{"activity": f"{name}_Bronze", "dependencyConditions": ["Succeeded"]}],
                "typeProperties": {
                    "notebook": {"referenceName": f"stg_{name}", "type": "NotebookReference"}
                }
            }
            
            # Gold Activity
            act_gold = {
                "name": f"{name}_Gold",
                "type": "RunNotebook",
                "dependsOn": [{"activity": f"{name}_Silver", "dependencyConditions": ["Succeeded"]}],
                "typeProperties": {
                    "notebook": {"referenceName": f"dim_{name}", "type": "NotebookReference"}
                }
            }
            
            pipeline["properties"]["activities"].extend([act_bronze, act_silver, act_gold])
            
        return json.dumps(pipeline, indent=2)

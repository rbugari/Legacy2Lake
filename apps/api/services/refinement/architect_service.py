
import os
import shutil
from pathlib import Path
import json

try:
    from apps.api.services.persistence_service import PersistenceService
except ImportError:
    try:
        from services.persistence_service import PersistenceService
    except ImportError:
        from ..persistence_service import PersistenceService

class ArchitectService:
    def __init__(self):
        pass

    def refine_project(self, project_id: str, profile_metadata: dict, log: list = None) -> dict:
        """
        Segments Code into Medallion Architecture (Bronze/Silver/Gold).
        Generates config.py and utils.py.
        """
        if log is None: log = []
        
        base_path = PersistenceService.ensure_solution_dir(project_id)
        project_path = Path(base_path)
        input_dir = project_path / PersistenceService.STAGE_DRAFTING
        output_dir = project_path / PersistenceService.STAGE_REFINEMENT
        
        log.append(f"[Architect] Solutions Directory: {base_path}")
        
        # Create Medallion Structure
        bronze_dir = output_dir / "Bronze"
        silver_dir = output_dir / "Silver"
        gold_dir = output_dir / "Gold"
        
        log.append("[Architect] Ensuring Medallion folder structure (Bronze/Silver/Gold)...")
        for d in [bronze_dir, silver_dir, gold_dir]:
            d.mkdir(parents=True, exist_ok=True)

        refined_files = {
            "bronze": [],
            "silver": [],
            "gold": [],
            "config": [],
            "utils": []
        }

        # 1. Generate Shared Artifacts
        self._generate_config(output_dir)
        refined_files["config"].append(str(output_dir / "config.py"))
        log.append("[Architect] Generated: config.py")
        
        self._generate_utils(output_dir)
        refined_files["utils"].append(str(output_dir / "utils.py"))
        log.append("[Architect] Generated: utils.py")

        # 2. Process each analyzed file
        files_to_process = profile_metadata.get("analyzed_files", [])
        log.append(f"[Architect] Processing {len(files_to_process)} source files for Medallion segmentation...")
        
        for filename in files_to_process:
            file_path = input_dir / filename
            if not file_path.exists():
                log.append(f"[Architect] WARNING: File skipped (not found): {filename}")
                continue
                
            # Basic Heuristic:
                
            # Basic Heuristic: 
            # If it's a Source-to-Stage, it has a Bronze aspect.
            # If it has transformations, it's Silver.
            # We will generate BOTH Bronze and Silver versions for every source file for now.
            log.append(f"[Architect] Transforming {filename} -> Bronze & Silver layers")
            
            # Bronze Generation
            bronze_file = bronze_dir / filename.replace(".py", "_bronze.py")
            self._create_bronze_layer(file_path, bronze_file)
            refined_files["bronze"].append(str(bronze_file))
            
            # Silver Generation (Standard + Quarantine)
            silver_file = silver_dir / filename.replace(".py", "_silver.py")
            pk_key = profile_metadata.get("primary_keys", {}).get(filename, ["id"])
            if isinstance(pk_key, str): pk_key = [pk_key]
            
            self._create_silver_layer(file_path, silver_file, pk_columns=pk_key)
            refined_files["silver"].append(str(silver_file))
            
            # Gold Generation
            gold_file = gold_dir / filename.replace(".py", "_gold.py")
            table_type = profile_metadata.get("table_metadata", {}).get(filename, {}).get("type", "DIMENSION")
            self._create_gold_layer(file_path, gold_file, table_type=table_type)
            refined_files["gold"].append(str(gold_file))

        return {
            "status": "COMPLETED",
            "refined_files": refined_files
        }

    def _generate_config(self, output_dir: Path):
        content = """
# Medallion Architecture Configuration
import os

class Config:
    CATALOG = "main_catalog"
    
    # Schemas
    SCHEMA_BRONZE = "bronze_raw"
    SCHEMA_SILVER = "silver_curated"
    SCHEMA_GOLD = "gold_business"
    
    # Paths (if using external locations)
    PATH_BRONZE = "/mnt/datalake/bronze"
    PATH_SILVER = "/mnt/datalake/silver"
    PATH_GOLD = "/mnt/datalake/gold"
    
    @staticmethod
    def get_jdbc_url(secret_scope, secret_key):
        return dbutils.secrets.get(scope=secret_scope, key=secret_key)
"""
        with open(output_dir / "config.py", "w", encoding="utf-8") as f:
            f.write(content)

    def _generate_utils(self, output_dir: Path):
        content = """
# Common Utility Functions
from pyspark.sql.functions import current_timestamp, lit

def add_ingestion_metadata(df):
    return df.withColumn("_ingestion_timestamp", current_timestamp()) \
             .withColumn("_source_system", lit("SSIS_MIGRATION"))

def quarantine_bad_records(df, rules, quarantine_table):
    # Simplified quarantine logic
    # In production, this would use delta expectations or Great Expectations
    pass
"""
        with open(output_dir / "utils.py", "w", encoding="utf-8") as f:
            f.write(content)
            
    def _create_bronze_layer(self, source_path: Path, target_path: Path):
        """
        Generates Bronze Layer Code: Raw Ingestion + Metadata.
        Keeps original read logic active but disables original writes.
        """
        # Read source to get table name (mocking logic)
        with open(source_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        processed_lines = []
        for line in lines:
            # Disable original writes and side effects
            if any(x in line for x in [".write", ".save", "saveAsTable", "display(", "OPTIMIZE", "VACUUM"]):
                processed_lines.append(f"# [DISABLED_BY_ARCHITECT] {line}")
            else:
                processed_lines.append(line)
            
        original_code_safe = "".join(processed_lines)
            
        code = f"""# BRONZE LAYER INGESTION
# Generated by Shift-T Architect Agent
# Source: {source_path.name}

from config import Config
from utils import add_ingestion_metadata
from delta.tables import *
from pyspark.sql.functions import *
# [ORIGINAL READ LOGIC (Adapted)]
# We keep the source reading logic active to define 'df_source'
{original_code_safe}

# Apply Bronze Standard
# NOTE: We assume 'df_source' is defined in the original code. 
# If the original code used 'df' or another name, we attempt to alias it.
if 'df_source' not in locals() and 'df' in locals():
    df_source = df

df_bronze = add_ingestion_metadata(df_source)

# Write to Delta
target_table = f"{{Config.CATALOG}}.{{Config.SCHEMA_BRONZE}}.{source_path.stem}"
df_bronze.write.format("delta").mode("append").option("mergeSchema", "true").saveAsTable(target_table)
"""
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(code)

    def _create_silver_layer(self, source_path: Path, target_path: Path, pk_columns: list = None):
        """
        Generates Silver Layer Code: Cleaning, Deduplication, MERGE.
        Supports Composite Primary Keys.
        """
        if pk_columns is None: pk_columns = ["id"]
        
        # Build Merge Condition
        # "target.id = source.id AND target.date = source.date"
        merge_condition = " AND ".join([f"target.{pk} = source.{pk}" for pk in pk_columns])
        pk_display = ", ".join(pk_columns)

        code = f"""# SILVER LAYER TRANSFORMATION
# Generated by Shift-T Architect Agent
# Source: {source_path.name}
# Primary Key(s): {pk_display}

from config import Config
from delta.tables import *

# Read Bronze
df_bronze = spark.read.table(f"{{Config.CATALOG}}.{{Config.SCHEMA_BRONZE}}.{source_path.stem}")

# Deduplicate
df_clean = df_bronze.dropDuplicates({pk_columns})

# SCD Type 2 Merge (Upsert)
target_table_name = f"{{Config.CATALOG}}.{{Config.SCHEMA_SILVER}}.{source_path.stem}"

if SparkSession.active.catalog.tableExists(target_table_name) and "{pk_columns[0]}" != "id":
    target_table = DeltaTable.forName(spark, target_table_name)
    target_table.alias("target").merge(
        df_clean.alias("source"),
        "{merge_condition}"
    ).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
else:
    # If no specific key was detected, we overwrite or append based on type
    df_clean.write.format("delta").mode("overwrite").saveAsTable(target_table_name)
"""
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(code)
    def _create_gold_layer(self, source_path: Path, target_path: Path, table_type: str = "DIMENSION"):
        """
        Generates Gold Layer Code: Business Aggregations / Semantic Views.
        """
        logic_comment = "# Gold Logic: Business-ready projection."
        select_logic = "df_silver.select(\"*\")"
        
        if table_type == "FACT":
            logic_comment = "# Gold Logic: Fact table aggregation / Semantic measures."
            select_logic = "df_silver.select(\"*\", (col(\"qty\") * col(\"unitprice\")).alias(\"total_amount\"))"

        code = f"""# GOLD LAYER - BUSINESS VIEW ({table_type})
# Generated by Shift-T Architect Agent
# Source: {source_path.name}

from config import Config
from pyspark.sql.functions import *

# Read Silver (Business Curated Data)
target_silver_table = f"{{Config.CATALOG}}.{{Config.SCHEMA_SILVER}}.{source_path.stem}"
df_silver = spark.read.table(target_silver_table)

{logic_comment}
df_gold = {select_logic}

# Write to Gold
target_gold_table = f"{{Config.CATALOG}}.{{Config.SCHEMA_GOLD}}.{source_path.stem}"
df_gold.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(target_gold_table)

print(f"Gold Layer updated: {{target_gold_table}}")
"""
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(code)

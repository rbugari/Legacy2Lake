from pathlib import Path
from typing import Dict, Any, List
from .base_cartridge import Cartridge

class GCPCartridge(Cartridge):
    """
    Generates Google Cloud Platform Code.
    - Processing: BigQuery SQL (Standard SQL)
    - Semantic: LookML (for Looker)
    """

    def get_file_extension(self) -> str:
        return ".sql"

    def generate_scaffolding(self) -> Dict[str, str]:
        """Generates Looker project configuration and BigQuery utils."""
        naming = self.registry.get("naming", {})
        project_id = self.registry.get("gcp_project_id", "my-gcp-project")
        
        # Datasets
        ds_bronze = naming.get("bronze_schema", "raw_bronze")
        ds_silver = naming.get("silver_schema", "clean_silver")
        ds_gold = naming.get("gold_schema", "bi_gold")
        
        # Looker Manifest
        manifest_content = f"""project_name: "{self.project_id}"

# Localization Settings
localization_settings: {{
  default_locale: en
  localization_level: permissive
}}
"""
        
        # Looker Model
        model_content = f"""connection: "bigquery_conn"

include: "/views/*.view.lkml"                # include all views in the views/ folder in this project

explore: gold_sales {{
  label: "Sales Analytics"
  # Joins would go here
}}
"""
        
        # BigQuery Config helper (SQL based, maybe a stored procedure for logging)
        logging_proc = """CREATE OR REPLACE PROCEDURE `utils.log_job`(job_name STRING, status STRING)
BEGIN
  INSERT INTO `utils.job_logs` (job_name, timestamp, status)
  VALUES (job_name, CURRENT_TIMESTAMP(), status);
END;
"""

        return {
            "manifest.lkml": manifest_content,
            "model.lkml": model_content,
            "setup_logging.sql": logging_proc
        }

    def generate_bronze_sql(self, table_metadata: Dict[str, Any]) -> str:
        """BigQuery SQL for Bronze Layer (Ingestion)."""
        source_path = Path(table_metadata.get("source_path", "unknown"))
        dataset = self.registry.get("naming", {}).get("bronze_schema", "raw_bronze")
        table_name = source_path.stem
        
        return f"""-- BIGQUERY BRONZE LAYER
-- Source: {source_path.name}
-- Target: `{dataset}.{table_name}` (Native Table or External Table)

CREATE OR REPLACE TABLE `{dataset}.{table_name}` AS
SELECT 
    *,
    CURRENT_TIMESTAMP() as _ingestion_timestamp,
    'LEGACY_MIGRATION' as _source_system
FROM `{dataset}.external_stage_{table_name}`;
"""

    def generate_silver_sql(self, table_metadata: Dict[str, Any]) -> str:
        """BigQuery SQL for Silver Layer (Merge/Dedupe)."""
        source_path = Path(table_metadata.get("source_path", "unknown"))
        output_table_name = table_metadata.get("output_table_name", source_path.stem)
        
        ds_bronze = self.registry.get("naming", {}).get("bronze_schema", "raw_bronze")
        ds_silver = self.registry.get("naming", {}).get("silver_schema", "clean_silver")
        
        pk_columns = table_metadata.get("pk_columns", ["id"])
        if isinstance(pk_columns, str): pk_columns = [pk_columns]
        
        merge_cond = " AND ".join([f"T.{pk} = S.{pk}" for pk in pk_columns])
        
        return f"""-- BIGQUERY SILVER LAYER
-- Target: `{ds_silver}.{output_table_name}`

MERGE `{ds_silver}.{output_table_name}` T
USING (
    -- Deduplicate Bronze
    SELECT * EXCEPT(rn) FROM (
        SELECT *, ROW_NUMBER() OVER(PARTITION BY {', '.join(pk_columns)} ORDER BY _ingestion_timestamp DESC) as rn
        FROM `{ds_bronze}.{source_path.stem}`
    ) WHERE rn = 1
) S
ON {merge_cond}
WHEN MATCHED THEN
    UPDATE SET 
        T._ingestion_timestamp = S._ingestion_timestamp
        -- Add other columns check
WHEN NOT MATCHED THEN
    INSERT ROW;
"""

    def generate_gold_sql(self, table_metadata: Dict[str, Any]) -> str:
        """BigQuery SQL for Gold Layer (Business Logic)."""
        output_table_name = table_metadata.get("output_table_name", "gold_table")
        ds_silver = self.registry.get("naming", {}).get("silver_schema", "clean_silver")
        ds_gold = self.registry.get("naming", {}).get("gold_schema", "bi_gold")
        
        return f"""-- BIGQUERY GOLD LAYER
-- Target: `{ds_gold}.{output_table_name}`
-- Logic: Business projection

CREATE OR REPLACE TABLE `{ds_gold}.{output_table_name}`
PARTITION BY DATE(_ingestion_timestamp)
AS
SELECT 
    * 
FROM `{ds_silver}.{output_table_name.replace('dim_', 'stg_').replace('fact_', 'stg_')}`;
"""

    def generate_semantic_model(self, table_metadata: Dict[str, Any]) -> str:
        """Generates LookML View for the Gold Table."""
        output_table_name = table_metadata.get("output_table_name", "gold_table")
        ds_gold = self.registry.get("naming", {}).get("gold_schema", "bi_gold")
        project_id = self.registry.get("gcp_project_id", "my-project")
        
        # In a real implementation we would infer columns from metadata.
        # Here we provide a template.
        
        return f"""view: {output_table_name} {{
  sql_table_name: `{project_id}.{ds_gold}.{output_table_name}` ;;
  
  dimension: id {{
    primary_key: yes
    type: string
    sql: ${{TABLE}}.id ;;
  }}
  
  dimension: _ingestion_timestamp {{
    type: date_time
    sql: ${{TABLE}}._ingestion_timestamp ;;
  }}

  measure: count {{
    type: count
    drill_fields: [id]
  }}
}}
"""

    def generate_orchestration(self, tables_metadata: List[Dict[str, Any]]) -> str:
        """Generates an Airflow DAG for BigQuery tasks."""
        project_id = self.project_id
        
        dag_content = f"""from airflow import DAG
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from datetime import datetime, timedelta

default_args = {{
    'owner': 'utm_architect',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}}

with DAG(
    'dag_{project_id}_orchestration',
    default_args=default_args,
    description='Medallion Orchestration for {project_id}',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['utm', 'medallion'],
) as dag:

"""
        # Generate tasks for each table
        for table in tables_metadata:
            name = table['table_name']
            dag_content += f"""
    # Orchestration for {name}
    task_{name}_bronze = BigQueryInsertJobOperator(
        task_id='{name}_bronze',
        configuration={{
            "query": {{
                "query": "CALL `{project_id}.procs.run_bronze_{name}`()",
                "useLegacySql": False,
            }}
        }}
    )

    task_{name}_silver = BigQueryInsertJobOperator(
        task_id='{name}_silver',
        configuration={{
            "query": {{
                "query": "CALL `{project_id}.procs.run_silver_{name}`()",
                "useLegacySql": False,
            }}
        }}
    )

    task_{name}_gold = BigQueryInsertJobOperator(
        task_id='{name}_gold',
        configuration={{
            "query": {{
                "query": "CALL `{project_id}.procs.run_gold_{name}`()",
                "useLegacySql": False,
            }}
        }}
    )

    task_{name}_bronze >> task_{name}_silver >> task_{name}_gold
"""
        return dag_content

    # Implements abstract methods (PySpark variations not used for BQ typically, but we stub them just in case)
    def generate_bronze(self, tm): return self.generate_bronze_sql(tm)
    def generate_silver(self, tm): return self.generate_silver_sql(tm)
    def generate_gold(self, tm): return self.generate_gold_sql(tm)

from pathlib import Path
from typing import Dict, Any, List
import json
from .base_cartridge import Cartridge

class AWSCartridge(Cartridge):
    """
    Generates AWS Cloud Code.
    - Processing: AWS Glue (PySpark)
    - Storage: Redshift (via JDBC) / S3
    - Semantic: QuickSight (JSON Definitions)
    """

    def get_file_extension(self) -> str:
        return ".py"

    def generate_scaffolding(self) -> Dict[str, str]:
        """Generates Glue configuration and utilities."""
        naming = self.registry.get("naming", {})
        
        # S3 Paths for Data Lake
        s3_bucket = self.registry.get("aws_s3_bucket", "my-datalake-bucket")
        p_bronze = f"s3://{s3_bucket}/{naming.get('bronze_schema', 'bronze')}"
        p_silver = f"s3://{s3_bucket}/{naming.get('silver_schema', 'silver')}"
        
        # Redshift JDBC Config
        rs_host = self.registry.get("aws_redshift_host", "my-cluster.redshift.amazonaws.com")
        rs_db = self.registry.get("aws_redshift_db", "dev")
        
        config_content = f"""# AWS Glue & Redshift Configuration

class Config:
    # S3 Locations
    PATH_BRONZE = "{p_bronze}"
    PATH_SILVER = "{p_silver}"
    
    # Redshift Connection
    REDSHIFT_URL = "jdbc:redshift://{rs_host}:5439/{rs_db}"
    REDSHIFT_TEMP_DIR = f"s3://{s3_bucket}/temp/redshift/"
    
    # Connection Name in Glue Catalog
    GLUE_CONN_NAME = "RedshiftConnection"
"""

        utils_content = """# AWS Glue Utils
from awsglue.context import GlueContext
from pyspark.context import SparkContext

def get_glue_context():
    sc = SparkContext()
    return GlueContext(sc)

def write_to_redshift(df, table_name, config):
    \"\"\"Writes DynamicFrame or DataFrame to Redshift.\"\"\"
    # In a real scenario, we'd use glueContext.write_dynamic_frame.from_jdbc_conf
    # Here we mock the standard Spark write for simplicity in generated code
    df.write \\
      .format("io.github.spark_redshift_community.spark.redshift") \\
      .option("url", config.REDSHIFT_URL) \\
      .option("dbtable", table_name) \\
      .option("tempdir", config.REDSHIFT_TEMP_DIR) \\
      .mode("overwrite") \\
      .save()
"""
        return {
            "glue_config.py": config_content,
            "glue_utils.py": utils_content
        }

    def generate_bronze(self, table_metadata: Dict[str, Any]) -> str:
        """Glue Job for Bronze Layer (Ingestion)."""
        source_path = Path(table_metadata.get("source_path", "unknown_source.py"))
        
        return f"""# AWS GLUE - BRONZE LAYER
# Source: {source_path.name}

import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from glue_config import Config

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
args = getResolvedOptions(sys.argv, ['JOB_NAME'])
job.init(args['JOB_NAME'], args)

# [SOURCE LOGIC FROM MIGRATION]
# Assumes 'df' is created here
{table_metadata.get("original_code", "# Code placeholder")}

# Write to S3 (Bronze / Parquet)
target_path = f"{{Config.PATH_BRONZE}}/{source_path.stem}"
if 'df' in locals():
    df.write.mode("append").parquet(target_path)

job.commit()
"""

    def generate_silver(self, table_metadata: Dict[str, Any]) -> str:
        """Glue Job for Silver Layer (Transformation)."""
        source_path = Path(table_metadata.get("source_path", "unknown"))
        output_table_name = table_metadata.get("output_table_name", source_path.stem)
        
        return f"""# AWS GLUE - SILVER LAYER
# Source: {source_path.name}

import sys
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from glue_config import Config

glueContext = GlueContext(SparkContext())
spark = glueContext.spark_session

# Read Bronze
df_bronze = spark.read.parquet(f"{{Config.PATH_BRONZE}}/{source_path.stem}")

# [TRANSFORMATIONS / DEDUPE]
df_silver = df_bronze.dropDuplicates()

# Write to Silver (S3)
target_path = f"{{Config.PATH_SILVER}}/{output_table_name}"
df_silver.write.mode("overwrite").parquet(target_path)
"""

    def generate_gold(self, table_metadata: Dict[str, Any]) -> str:
        """Glue Job to load Redshift (Gold Layer)."""
        output_table_name = table_metadata.get("output_table_name", "gold_table")
        
        return f"""# AWS GLUE - GOLD LAYER (Load to Redshift)
# Target: {output_table_name}

from glue_config import Config
from glue_utils import write_to_redshift, get_glue_context

glueContext = get_glue_context()
spark = glueContext.spark_session

# Read Silver
df_silver = spark.read.parquet(f"{{Config.PATH_SILVER}}/{output_table_name}")

# Business Logic
df_gold = df_silver.select("*")

# Write to Redshift
write_to_redshift(df_gold, "public." + "{output_table_name}", Config)
"""

    def generate_semantic_model(self, table_metadata: Dict[str, Any]) -> str:
        """Generates QuickSight Dataset Definition (JSON)."""
        output_table_name = table_metadata.get("output_table_name", "gold_table")
        rs_host = self.registry.get("aws_redshift_host", "cluster-id")
        
        # Simplified QuickSight JSON structure
        quicksight_model = {
            "DataSetId": f"ds-{output_table_name}",
            "Name": f"dataset_{output_table_name}",
            "PhysicalTableMap": {
                "PhysTable1": {
                    "RelationalTable": {
                        "DataSourceArn": f"arn:aws:quicksight:us-east-1:123456789012:datasource/redshift-{rs_host}",
                        "Schema": "public",
                        "Name": output_table_name,
                        "InputColumns": [
                            {"Name": "id", "Type": "STRING"},
                            {"Name": "amount", "Type": "DECIMAL"}
                        ]
                    }
                }
            },
            "LogicalTableMap": {
                "LogTable1": {
                    "Alias": f"Business View - {output_table_name}",
                    "Source": {"PhysicalTableId": "PhysTable1"}
                }
            }
        }
        
        return json.dumps(quicksight_model, indent=2)

    def generate_orchestration(self, tables_metadata: List[Dict[str, Any]]) -> str:
        """Generates an Airflow DAG for AWS Glue jobs."""
        project_id = self.project_id
        
        dag_content = f"""from airflow import DAG
from airflow.providers.amazon.aws.operators.glue import GlueJobOperator
from datetime import datetime, timedelta

default_args = {{
    'owner': 'utm_architect',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}}

with DAG(
    'dag_aws_{project_id}_orchestration',
    default_args=default_args,
    description='Medallion Orchestration for AWS ({project_id})',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['utm', 'aws', 'glue'],
) as dag:

"""
        for table in tables_metadata:
            name = table['table_name']
            dag_content += f"""
    # Orchestration for {name}
    task_{name}_bronze = GlueJobOperator(
        task_id='{name}_bronze',
        job_name='job_{name}_bronze'
    )

    task_{name}_silver = GlueJobOperator(
        task_id='{name}_silver',
        job_name='job_{name}_silver'
    )

    task_{name}_gold = GlueJobOperator(
        task_id='{name}_gold',
        job_name='job_{name}_gold'
    )

    task_{name}_bronze >> task_{name}_silver >> task_{name}_gold
"""
        return dag_content

    # Stub SQL methods if needed, or raise NotImplemented
    def generate_bronze_sql(self, tm): return "-- Not implemented for Glue flow"
    def generate_silver_sql(self, tm): return "-- Not implemented for Glue flow"
    def generate_gold_sql(self, tm): return "-- Redshift SQL generation logic could go here"

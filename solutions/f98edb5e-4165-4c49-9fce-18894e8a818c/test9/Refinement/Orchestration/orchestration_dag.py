from airflow import DAG
from airflow.providers.databricks.operators.databricks import DatabricksRunNowOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'utm_architect',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'dag_databricks_TEST9_orchestration',
    default_args=default_args,
    description='Medallion Orchestration for Databricks (TEST9)',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['utm', 'databricks', 'pyspark'],
) as dag:


    # Orchestration for DimCustomers
    task_DimCustomers_bronze = DatabricksRunNowOperator(
        task_id='DimCustomers_bronze',
        job_id='job_id_bronze_DimCustomers'
    )

    task_DimCustomers_silver = DatabricksRunNowOperator(
        task_id='DimCustomers_silver',
        job_id='job_id_silver_DimCustomers'
    )

    task_DimCustomers_gold = DatabricksRunNowOperator(
        task_id='DimCustomers_gold',
        job_id='job_id_gold_DimCustomers'
    )

    task_DimCustomers_bronze >> task_DimCustomers_silver >> task_DimCustomers_gold

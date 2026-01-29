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
    'dag_databricks_PruebaUsr_orchestration',
    default_args=default_args,
    description='Medallion Orchestration for Databricks (PruebaUsr)',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['utm', 'databricks', 'pyspark'],
) as dag:


    # Orchestration for DimCategory
    task_DimCategory_bronze = DatabricksRunNowOperator(
        task_id='DimCategory_bronze',
        job_id='job_id_bronze_DimCategory'
    )

    task_DimCategory_silver = DatabricksRunNowOperator(
        task_id='DimCategory_silver',
        job_id='job_id_silver_DimCategory'
    )

    task_DimCategory_gold = DatabricksRunNowOperator(
        task_id='DimCategory_gold',
        job_id='job_id_gold_DimCategory'
    )

    task_DimCategory_bronze >> task_DimCategory_silver >> task_DimCategory_gold

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

    # Orchestration for DimEmployee
    task_DimEmployee_bronze = DatabricksRunNowOperator(
        task_id='DimEmployee_bronze',
        job_id='job_id_bronze_DimEmployee'
    )

    task_DimEmployee_silver = DatabricksRunNowOperator(
        task_id='DimEmployee_silver',
        job_id='job_id_silver_DimEmployee'
    )

    task_DimEmployee_gold = DatabricksRunNowOperator(
        task_id='DimEmployee_gold',
        job_id='job_id_gold_DimEmployee'
    )

    task_DimEmployee_bronze >> task_DimEmployee_silver >> task_DimEmployee_gold

    # Orchestration for DimProduct
    task_DimProduct_bronze = DatabricksRunNowOperator(
        task_id='DimProduct_bronze',
        job_id='job_id_bronze_DimProduct'
    )

    task_DimProduct_silver = DatabricksRunNowOperator(
        task_id='DimProduct_silver',
        job_id='job_id_silver_DimProduct'
    )

    task_DimProduct_gold = DatabricksRunNowOperator(
        task_id='DimProduct_gold',
        job_id='job_id_gold_DimProduct'
    )

    task_DimProduct_bronze >> task_DimProduct_silver >> task_DimProduct_gold

    # Orchestration for DimShipper
    task_DimShipper_bronze = DatabricksRunNowOperator(
        task_id='DimShipper_bronze',
        job_id='job_id_bronze_DimShipper'
    )

    task_DimShipper_silver = DatabricksRunNowOperator(
        task_id='DimShipper_silver',
        job_id='job_id_silver_DimShipper'
    )

    task_DimShipper_gold = DatabricksRunNowOperator(
        task_id='DimShipper_gold',
        job_id='job_id_gold_DimShipper'
    )

    task_DimShipper_bronze >> task_DimShipper_silver >> task_DimShipper_gold

    # Orchestration for DimSupplier
    task_DimSupplier_bronze = DatabricksRunNowOperator(
        task_id='DimSupplier_bronze',
        job_id='job_id_bronze_DimSupplier'
    )

    task_DimSupplier_silver = DatabricksRunNowOperator(
        task_id='DimSupplier_silver',
        job_id='job_id_silver_DimSupplier'
    )

    task_DimSupplier_gold = DatabricksRunNowOperator(
        task_id='DimSupplier_gold',
        job_id='job_id_gold_DimSupplier'
    )

    task_DimSupplier_bronze >> task_DimSupplier_silver >> task_DimSupplier_gold

    # Orchestration for FactSales
    task_FactSales_bronze = DatabricksRunNowOperator(
        task_id='FactSales_bronze',
        job_id='job_id_bronze_FactSales'
    )

    task_FactSales_silver = DatabricksRunNowOperator(
        task_id='FactSales_silver',
        job_id='job_id_silver_FactSales'
    )

    task_FactSales_gold = DatabricksRunNowOperator(
        task_id='FactSales_gold',
        job_id='job_id_gold_FactSales'
    )

    task_FactSales_bronze >> task_FactSales_silver >> task_FactSales_gold

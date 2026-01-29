from airflow import DAG
from airflow.operators.empty import EmptyOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'legacy2lake',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'legacy2lake_dag',
    default_args=default_args,
    description='Automated DAG from Legacy2Lake',
    schedule_interval=timedelta(days=1),
    catchup=False,
) as dag:

    start = EmptyOperator(task_id='start')
    end = EmptyOperator(task_id='end')

    destino_DW_sql = EmptyOperator(task_id='destino_DW_sql')
    DimCategory_dtsx = EmptyOperator(task_id='DimCategory_dtsx')
    DimCustomers_dtsx = EmptyOperator(task_id='DimCustomers_dtsx')
    DimEmployee_dtsx = EmptyOperator(task_id='DimEmployee_dtsx')
    DimProduct_dtsx = EmptyOperator(task_id='DimProduct_dtsx')
    DimShipper_dtsx = EmptyOperator(task_id='DimShipper_dtsx')
    DimSupplier_dtsx = EmptyOperator(task_id='DimSupplier_dtsx')
    FactSales_dtsx = EmptyOperator(task_id='FactSales_dtsx')
    origen_sql = EmptyOperator(task_id='origen_sql')
    readme_md = EmptyOperator(task_id='readme_md')
    layout_json = EmptyOperator(task_id='layout_json')
    layout_json = EmptyOperator(task_id='layout_json')

    start >> destino_DW_sql
    start >> DimCategory_dtsx
    start >> DimCustomers_dtsx
    start >> DimEmployee_dtsx
    start >> DimProduct_dtsx
    start >> DimShipper_dtsx
    start >> DimSupplier_dtsx
    start >> FactSales_dtsx
    start >> origen_sql
    start >> readme_md
    start >> layout_json
    start >> layout_json
    destino_DW_sql >> end
    DimCategory_dtsx >> end
    DimCustomers_dtsx >> end
    DimEmployee_dtsx >> end
    DimProduct_dtsx >> end
    DimShipper_dtsx >> end
    DimSupplier_dtsx >> end
    FactSales_dtsx >> end
    origen_sql >> end
    readme_md >> end
    layout_json >> end
    layout_json >> end

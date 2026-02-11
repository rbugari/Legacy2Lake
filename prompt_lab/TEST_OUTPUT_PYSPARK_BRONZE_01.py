# ==============================================================================
# L2L MODERNIZATION TRACE
# Source: dbo.DimCustomers
# Component: PySpark Notebook
# Logic: Bronze raw ingestion for DimCustomers from SQL Server to Delta Lake (with full context-driven configuration)
# Generated At: 2026-02-10T00:00:00Z
# ==============================================================================

def execute_task(spark, config):
    """
    Bronze ingestion for DimCustomers (Databricks Lakehouse Standard)
    """
    # 1. IMPORTS
    from pyspark.sql.functions import (
        current_timestamp, 
        current_date, 
        input_file_name, 
        lit,
        col
    )
    import logging

    # 2. LOGGING SETUP
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # 3. CONFIGURATION
    CATALOG = config['catalog']
    SCHEMA_BRONZE = config['schema_bronze']
    SOURCE_SYSTEM = config['source_system']
    TABLE_NAME = config['table_name']
    JDBC_URL = config['jdbc_url']  # e.g. "jdbc:sqlserver://..."
    JDBC_PROPS = config['jdbc_properties']  # dict: user, password, driver
    SOURCE_TABLE = config['source_table']

    try:
        logger.info(f"Starting Bronze ingestion for {TABLE_NAME}")
        # [EXTRACT]
        df_source = spark.read \
            .jdbc(url=JDBC_URL, table=SOURCE_TABLE, properties=JDBC_PROPS)
        logger.info(f"Read {df_source.count()} records from source")

        # [TRANSFORM] - Add metadata columns (all 4 required)
        df_bronze = df_source \
            .withColumn("_ingestion_timestamp", current_timestamp()) \
            .withColumn("_ingestion_date", current_date()) \
            .withColumn("_source_file", lit(SOURCE_TABLE)) \
            .withColumn("_source_system", lit(SOURCE_SYSTEM))

        # [VALIDATION]
        record_count = df_bronze.count()
        assert record_count > 0, f"No records to ingest for {TABLE_NAME}"
        logger.info(f"Validated: {record_count} records ready for ingestion")

        # [LOAD]
        target_table = f"{CATALOG}.{SCHEMA_BRONZE}.{TABLE_NAME}"
        df_bronze.write \
            .format("delta") \
            .mode("append") \
            .option("mergeSchema", "true") \
            .option("dataChange", "true") \
            .partitionBy("_ingestion_date") \
            .saveAsTable(target_table)

        logger.info(f"✅ Successfully ingested to Bronze: {target_table}")
        logger.info(f"Schema: {df_bronze.schema.simpleString()}")
        logger.info(f"Partition: _ingestion_date")

    except Exception as e:
        logger.error(f"❌ Bronze ingestion failed for {TABLE_NAME}: {str(e)}")
        raise
    finally:
        logger.info("Bronze ingestion process completed")

# Example config usage (to be removed/commented in production)
# config = {
#     'catalog': 'main_catalog',
#     'schema_bronze': 'bronze_raw',
#     'source_system': 'SSIS_MIGRATION',
#     'table_name': 'dim_customers',
#     'jdbc_url': dbutils.secrets.get('ssis_migration', 'jdbc_url'),
#     'jdbc_properties': {
#         'user': dbutils.secrets.get('ssis_migration', 'username'),
#         'password': dbutils.secrets.get('ssis_migration', 'password'),
#         'driver': 'com.microsoft.sqlserver.jdbc.SQLServerDriver'
#     },
#     'source_table': 'dbo.DimCustomers',
# }
# execute_task(spark, config)

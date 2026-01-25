from pyspark.sql import functions as F
from delta.tables import DeltaTable
import logging

def execute_task(spark, context):
    """
    Principal Engineer Transpilation for FactSales
    Migrates sales data with PII masking, strict type casting, and idempotent Delta Lake MERGE.
    """
    # 1. PARAMETERS & CONFIG
    target_table = 'stg_factsales'  # Silver prefix enforced
    source_table = 'bronze_sales'   # Assumed source
    partition_key = context['metadata'].get('partition_key', 'transaction_date')
    business_keys = ['transaction_id']  # Assumed business key for idempotency
    
    # 2. EXTRACT (Bronze)
    try:
        df_source = spark.table(source_table)
    except Exception as e:
        logging.error(f"Failed to load source table {source_table}: {e}")
        raise

    # 3. TRANSFORM (Apply PII Masking, Business Logic)
    try:
        # Apply SHA2 masking to email (PII)
        df_transformed = df_source.withColumn(
            'email',
            F.sha2(F.col('email'), 256)
        )
        # Additional transformation logic can be added here
    except Exception as e:
        logging.error(f"Transformation failed: {e}")
        raise

    # 3.1 TYPE SAFETY LOOP (Strict Casting)
    # Target DDL (must be provided/queried for strict casting)
    target_schema = [
        ('transaction_id', 'LongType'),
        ('transaction_date', 'DateType'),
        ('email', 'StringType'),
        ('amount', 'DecimalType(18,2)')
    ]
    for col_name, col_type in target_schema:
        try:
            if col_type.startswith('DecimalType'):
                precision, scale = map(int, col_type.replace('DecimalType(', '').replace(')', '').split(','))
                df_transformed = df_transformed.withColumn(col_name, F.col(col_name).cast(f"decimal({precision},{scale})"))
            else:
                spark_type = {
                    'LongType': 'long',
                    'DateType': 'date',
                    'StringType': 'string'
                }[col_type]
                df_transformed = df_transformed.withColumn(col_name, F.col(col_name).cast(spark_type))
        except Exception as e:
            logging.error(f"Casting failed for column {col_name}: {e}")
            raise

    # 4. LOAD (Delta MERGE for Idempotency)
    try:
        # Create temp view for SQL MERGE
        df_transformed.createOrReplaceTempView('vw_factsales_staging')
        merge_sql = f"""
        MERGE INTO {target_table} AS tgt
        USING vw_factsales_staging AS src
        ON tgt.transaction_id = src.transaction_id
        WHEN MATCHED THEN UPDATE SET
            tgt.transaction_date = src.transaction_date,
            tgt.email = src.email,
            tgt.amount = src.amount
        WHEN NOT MATCHED THEN INSERT (
            transaction_id, transaction_date, email, amount
        ) VALUES (
            src.transaction_id, src.transaction_date, src.email, src.amount
        )
        """
        spark.sql(merge_sql)
        # OPTIMIZE/ZORDER for high volume
        spark.sql(f"OPTIMIZE {target_table} ZORDER BY ({partition_key})")
        spark.sql(f"VACUUM {target_table} RETAIN 168 HOURS")  # 7 days
    except Exception as e:
        logging.error(f"Delta MERGE failed: {e}")
        raise

    return True

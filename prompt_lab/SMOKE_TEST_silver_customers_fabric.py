from delta.tables import DeltaTable
from pyspark.sql import functions as F
from pyspark.sql.types import *

def execute_task(spark, config):
    # L2L MODERNIZATION TRACE
    # [EXTRACT]
    # Enforce schema on read - assuming schema is provided externally or inferred
    bronze_path = config['bronze_path']
    silver_path = config['silver_path']
    
    bronze_df = spark.read.format('delta').load(bronze_path)
    print(f"Rows processed (bronze): {bronze_df.count()}")
    
    # [TRANSFORM]
    # Example schema - You must replace with your exact target DDL
    target_schema = StructType([
        StructField('customer_id', LongType(), False),
        StructField('customer_name', StringType(), True),
        StructField('email', StringType(), True),
        StructField('signup_date', DateType(), True),
        StructField('is_active', BooleanType(), True)
    ])
    
    # Explicit type casting and COALESCE for idempotency/data integrity
    silver_df = bronze_df.select(
        F.coalesce(F.col('customer_id'), F.lit(-1)).cast('long').alias('customer_id'),
        F.col('customer_name').cast('string').alias('customer_name'),
        F.col('email').cast('string').alias('email'),
        F.col('signup_date').cast('date').alias('signup_date'),
        F.col('is_active').cast('boolean').alias('is_active')
    )
    print(f"Rows processed (silver/after transform): {silver_df.count()}")

    # [LOAD]
    # Use DeltaTable MERGE INTO for upsert/idempotency
    if DeltaTable.isDeltaTable(spark, silver_path):
        delta_table = DeltaTable.forPath(spark, silver_path)
        delta_table.alias('target').merge(
            silver_df.alias('source'),
            'target.customer_id = source.customer_id'
        ).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
    else:
        silver_df.write.format('delta').mode('overwrite').save(silver_path)

    # Post-load auditing
    final_df = spark.read.format('delta').load(silver_path)
    print(f"Rows processed (silver/post-merge): {final_df.count()}")

# Entrypoint
# You must pass config with 'bronze_path' and 'silver_path' keys
default_config = {
    'bronze_path': '/mnt/datalake/bronze/customers',
    'silver_path': '/mnt/datalake/silver/customers'
}
# Example invocation (uncomment to use in real pipeline)
# execute_task(spark, default_config)

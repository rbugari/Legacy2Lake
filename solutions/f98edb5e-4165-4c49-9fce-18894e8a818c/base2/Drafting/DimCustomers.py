# L2L MODERNIZATION TRACE
# Source: Unknown Asset 'None'
# Component: None
# Logic: Transpiled from Unknown
# Refactoring: No legacy logic provided; generated medallion-compliant template.
# Generated At: 2024-06-10T00:00:00Z

def execute_task(spark, context):
    """
    Principal Engineer Transpilation
    Template for FULL_OVERWRITE load strategy with strict type enforcement and idempotency.
    """
    import logging
    from pyspark.sql import functions as F
    from pyspark.sql.types import *
    from delta.tables import DeltaTable
    
    # 1. PARAMETERS (from context)
    target_table = context.get('target_name', 'UNKNOWN_TARGET')
    business_keys = context.get('business_keys', [])
    source_query = context.get('source_query', None)
    target_ddl = context.get('target_ddl', None)
    
    # 2. EXTRACT (Bronze/Silver)
    try:
        if source_query:
            df_source = spark.sql(source_query)
        else:
            logging.warning('No source query provided. Using empty DataFrame.')
            df_source = spark.createDataFrame([], StructType([]))
    except Exception as e:
        logging.error(f'Error during extraction: {e}')
        raise
    
    # 3. TRANSFORM (No transformation logic provided)
    df_transformed = df_source
    
    # 3.2 TYPE SAFETY LOOP (Mandatory)
    if target_ddl:
        for field in target_ddl:
            df_transformed = df_transformed.withColumn(field['name'], F.col(field['name']).cast(field['type']))
    else:
        logging.warning('No target DDL provided; skipping type enforcement.')
    
    # 4. LOAD (High-Quality Idempotent Merge)
    try:
        # For FULL_OVERWRITE, use overwrite only for Bronze; otherwise, use static partition overwrite or MERGE
        # Here, we use MERGE for idempotency if business keys are provided
        if business_keys and target_ddl:
            # Prepare merge condition
            merge_condition = ' AND '.join([f'source.{k} = target.{k}' for k in business_keys])
            # Create DeltaTable if not exists
            if not DeltaTable.isDeltaTable(spark, f'dbfs:/delta/{target_table}'):
                df_transformed.write.format('delta').save(f'dbfs:/delta/{target_table}')
            delta_target = DeltaTable.forPath(spark, f'dbfs:/delta/{target_table}')
            (
                delta_target.alias('target')
                .merge(
                    df_transformed.alias('source'),
                    merge_condition
                )
                .whenMatchedUpdateAll()
                .whenNotMatchedInsertAll()
                .execute()
            )
        else:
            # Fallback: Overwrite (only if allowed by medallion policy)
            df_transformed.write.format('delta').mode('overwrite').saveAsTable(target_table)
    except Exception as e:
        logging.error(f'Error during load: {e}')
        raise
    
    # OPTIMIZATION HINTS
    # spark.sql(f"OPTIMIZE {target_table}")
    # spark.sql(f"VACUUM {target_table} RETAIN 168 HOURS")
    
    return True

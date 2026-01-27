# L2L MODERNIZATION TRACE
# Source: Unknown Asset 'None'
# Component: None
# Logic: Transpiled from Unknown
# Refactoring: Medallion Standard, FULL_OVERWRITE (static partition)
# Generated At: 2024-06-10T00:00:00Z

def execute_task(spark, context):
    """
    Principal Engineer Transpilation
    FULL_OVERWRITE load for dimension tables (no lookups, no PII).
    """
    import logging
    from pyspark.sql import functions as F
    from pyspark.sql.types import DecimalType, LongType, StringType
    from delta.tables import DeltaTable

    # 1. PARAMETERS (from context)
    try:
        # Example for DimCategory (repeat for each asset as needed)
        target_table = 'dim_category'  # Naming convention enforced
        source_query = """
            SELECT categoryid, categoryname FROM Production.Categories
            WHERE categoryid > 0
        """
        target_path = f"/mnt/gold/dim_category"  # Example path, adjust as per environment
        business_keys = ["categoryid"]

        # 2. EXTRACT (Bronze/Silver)
        df_source = spark.sql(source_query)

        # 3. TRANSFORM (No lookups, no PII)
        # 3.1 TYPE SAFETY LOOP (Assume DDL: categoryid INT, categoryname STRING)
        df_casted = (
            df_source
            .withColumn("categoryid", F.col("categoryid").cast(LongType()))
            .withColumn("categoryname", F.col("categoryname").cast(StringType()))
        )

        # 4. LOAD (FULL_OVERWRITE via DeltaTable overwrite)
        # For FULL_OVERWRITE, static partition overwrite is used (MERGE not required for static dimensions)
        (
            df_casted
            .write
            .format("delta")
            .mode("overwrite")
            .option("overwriteSchema", "true")
            .save(target_path)
        )

        # OPTIMIZATION HINTS (Z-Order, Vacuum)
        # spark.sql(f"OPTIMIZE delta.`{target_path}` ZORDER BY (categoryid)")
        # spark.sql(f"VACUUM delta.`{target_path}` RETAIN 168 HOURS")

        logging.info(f"Successfully loaded {target_table} to {target_path}")
        return True
    except Exception as e:
        logging.error(f"Error in execute_task for {target_table}: {str(e)}")
        raise

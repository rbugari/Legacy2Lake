# L2L MODERNIZATION TRACE
# Source: Sales System Asset 'DimCustomers.dtsx'
# Component: Data Flow (DimCustomer)
# Logic: Transpiled from SSIS OLE DB Source/Destination
# Refactoring: FULL_OVERWRITE to Idempotent MERGE INTO (Delta)
# Generated At: 2024-06-09T00:00:00Z

import logging
from pyspark.sql import functions as F
from delta.tables import DeltaTable
from pyspark.sql.types import DecimalType, StringType, LongType

def execute_task(spark, context):
    """
    Principal Engineer Transpilation for DimCustomer (Silver Layer)
    """
    # 1. PARAMETERS & CONFIG
    target_table = 'stg_DimCustomer'  # Silver naming convention
    source_table = 'Sales.Customers'  # Source table
    business_keys = ['custid']        # Natural key for idempotency
    delta_path = f"/mnt/silver/{target_table}"  # Path can be parameterized

    # 2. EXTRACT (Bronze/Silver)
    try:
        # If max custid watermark is available, use it. Here, we assume full load.
        df_source = spark.sql("""
            SELECT custid, contactname, city, country, address, phone, postalcode
            FROM Sales.Customers
        """)
    except Exception as e:
        logging.error(f"Failed to extract source data: {e}")
        raise

    # 3. TRANSFORM (Type Safety & Business Logic)
    # Target DDL (assumed from context):
    # custid: Long, contactname: String, city: String, country: String, address: String, phone: String, postalcode: String
    try:
        df_casted = (
            df_source
            .withColumn("custid", F.col("custid").cast(LongType()))
            .withColumn("contactname", F.col("contactname").cast(StringType()))
            .withColumn("city", F.col("city").cast(StringType()))
            .withColumn("country", F.col("country").cast(StringType()))
            .withColumn("address", F.col("address").cast(StringType()))
            .withColumn("phone", F.col("phone").cast(StringType()))
            .withColumn("postalcode", F.col("postalcode").cast(StringType()))
        )
    except Exception as e:
        logging.error(f"Type casting failed: {e}")
        raise

    # 4. LOAD (Idempotent MERGE INTO)
    try:
        if DeltaTable.isDeltaTable(spark, delta_path):
            delta_tbl = DeltaTable.forPath(spark, delta_path)
            (
                delta_tbl.alias("t")
                .merge(
                    df_casted.alias("s"),
                    "t.custid = s.custid"
                )
                .whenMatchedUpdateAll()
                .whenNotMatchedInsertAll()
                .execute()
            )
        else:
            # Initial load: write as Delta
            (
                df_casted
                .write
                .format("delta")
                .mode("overwrite")
                .option("overwriteSchema", "true")
                .save(delta_path)
            )
        # Post-load optimization hint
        # spark.sql(f"OPTIMIZE delta.`{delta_path}` ZORDER BY (custid)")
    except Exception as e:
        logging.error(f"Delta MERGE/WRITE failed: {e}")
        raise

    return True

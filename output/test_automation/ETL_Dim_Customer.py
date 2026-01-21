# UTM Generated Notebook (Databricks)
# Source Tech: SSIS
# Source Name: ETL_Dim_Customer.dtsx
# Timestamp: 2026-01-21T07:21:33.078168

from pyspark.sql import functions as F
from delta.tables import *

# --- Execution Mesh Logic ---


# Step 1: READ
# Reading from 
# Discovery: AUTOMATIC

src_drc_-_source_system_code = spark.read.format("delta").table("")


display(src_drc_-_source_system_code)


# Step 2: READ
# Reading from 
# Discovery: AUTOMATIC

src_source_db_customer = spark.sql("""
SELECT CustomerID AS customer_id, PersonID
FROM Sales.Customer
WHERE PersonID IS NOT NULL
UNION ALL
SELECT NULL, NULL
""")


display(src_source_db_customer)


# Step 4: WRITE
# Writing to dbo.dim_customer
# Mode: MERGE


if DeltaTable.isDeltaTable(spark, "dbo.dim_customer"):
    deltaTable = DeltaTable.forName(spark, "dbo.dim_customer")
    
    (deltaTable.alias("target")
      .merge(
        df.alias("source"),
        "target._auto_detect_ = source._auto_detect_"
      )
      .whenMatchedUpdateAll()
      .whenNotMatchedInsertAll()
      .execute())
else:
    # First load
    df.write.format("delta").saveAsTable("dbo.dim_customer")




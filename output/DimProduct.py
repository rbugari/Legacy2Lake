# UTM Generated Notebook (Databricks)
# Source Tech: SSIS
# Source Name: DimProduct.dtsx
# Timestamp: 2026-01-20T07:13:25.789255

from pyspark.sql import functions as F
from delta.tables import *

# --- Execution Mesh Logic ---


# Step 1: READ
# Reading from 
# Discovery: AUTOMATIC

src_ole_db_source = spark.sql("""
SELECT * FROM Production.Products
""")


display(src_ole_db_source)


# Step 4: WRITE
# Writing to dbo.DimProduct
# Mode: MERGE


if DeltaTable.isDeltaTable(spark, "dbo.DimProduct"):
    deltaTable = DeltaTable.forName(spark, "dbo.DimProduct")
    
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
    df.write.format("delta").saveAsTable("dbo.DimProduct")




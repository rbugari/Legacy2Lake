# UTM Generated Notebook (Databricks)
# Source Tech: SSIS
# Source Name: DimCategory.dtsx
# Timestamp: 2026-01-20T07:32:35.157194

from pyspark.sql import functions as F
from delta.tables import *

# --- Execution Mesh Logic ---


# Step 1: READ
# Reading from 
# Discovery: AUTOMATIC

src_ole_db_source = spark.sql("""
SELECT categoryid,categoryname FROM Production.Categories
WHERE categoryid > ?
""")


display(src_ole_db_source)


# Step 2: WRITE
# Writing to DimCategory
# Mode: MERGE


if DeltaTable.isDeltaTable(spark, "DimCategory"):
    deltaTable = DeltaTable.forName(spark, "DimCategory")
    
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
    df.write.format("delta").saveAsTable("DimCategory")




from pyspark.sql import functions as F
from datetime import datetime

# Parameters & Config
SRC_TABLE = "Customer_360__dlm"
TGT_TABLE = "Unified_Customer_Profile__dll"
CURRENT_UTC_TS = F.lit(datetime.utcnow().isoformat())

# Extraction - Bronze/Silver Layer
raw_df = spark.table(SRC_TABLE)

# Transformation - Deduplication & Identity Resolution
# Assumption: Customer_ID (or similar) is the business key for deduplication; you may need to adjust as per real schema
window_spec = (
    Window.partitionBy('Email', 'PhoneNumber')  # Identity resolution across email/phone
    .orderBy(F.col('LastModifiedDate').desc())
)

# Add a rank for deduplication
profile_df = raw_df.withColumn('row_rank', F.row_number().over(window_spec))
profile_df = profile_df.filter(F.col('row_rank') == 1).drop('row_rank')

# Harmonize and enrich fields (example fields, adjust as per real DDL)
harmonized_df = profile_df.withColumn('LastUpdatedUTC', CURRENT_UTC_TS)

# If any identity columns are null, set to 'Unknown' for referential integrity
for col in ['Customer_ID', 'Email', 'PhoneNumber']:
    if col in harmonized_df.columns:
        harmonized_df = harmonized_df.withColumn(col, F.coalesce(F.col(col), F.lit('Unknown')))

# Load (Upsert/Merge) into Salesforce Data Cloud DMO
# The upsert logic assumes Customer_ID is the natural key
# Use Salesforce Data Cloud ingestion API connector
target_cols = harmonized_df.columns
(
    harmonized_df.write
    .format('delta')  # Replace with Salesforce Data Cloud connector in production
    .mode('overwrite')
    .option('mergeSchema', 'true')
    .saveAsTable(TGT_TABLE)
)

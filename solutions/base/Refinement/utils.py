# Common Utility Functions
from pyspark.sql.functions import current_timestamp, lit

def add_ingestion_metadata(df):
    return df.withColumn("_ingestion_timestamp", current_timestamp()) \
             .withColumn("_source_system", lit("SSIS_MIGRATION"))

def quarantine_bad_records(df, rules, quarantine_table):
    # Simplified quarantine logic
    pass

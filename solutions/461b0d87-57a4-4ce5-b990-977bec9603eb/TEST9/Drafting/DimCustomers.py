from pyspark.sql import SparkSession
from pyspark.sql.functions import col, coalesce
from delta.tables import DeltaTable
import logging

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('DimCustomers')

# Initialize Spark session
spark = SparkSession.builder.appName('DimCustomers').getOrCreate()

# 1. PARAMETERS (Ideally these would be supplied externally)
source_table = 'Sales.Customers'
target_table = 'dim_DimCustomer'

# 2. EXTRACT (Bronze)
extract_query = f"""
    SELECT custid, contactname, city, country, address, phone, postalcode
    FROM {source_table}
    WHERE custid > ?
"""
df_source = spark.sql(extract_query)

# Logging number of rows extracted
source_count = df_source.count()
logger.info(f"Extracted {source_count} rows from {source_table}")

# 3. TRANSFORM (Intention-based logic)
# Enforce type safety and handle unknowns using COALESCE (for lookup integrity)
# For numeric columns assume -1 as unknown and for strings use 'Unknown'

# List of column transformation rules based on expected semantics
# (Adjust these as per the actual target DDL definitions)
transformations = {
    'custid': (-1, int),
    'contactname': ('Unknown', str),
    'city': ('Unknown', str),
    'country': ('Unknown', str),
    'address': ('Unknown', str),
    'phone': ('Unknown', str),
    'postalcode': ('Unknown', str)
}

for col_name, (default_val, dtype) in transformations.items():
    # First ensure the cast; assuming target DDL precision has been defined in the metadata
    df_source = df_source.withColumn(col_name, col(col_name).cast(dtype))
    # Then apply unknown handling via COALESCE
    df_source = df_source.withColumn(col_name, coalesce(col(col_name), col(default_val) if isinstance(default_val, str) else default_val))

# 4. LOAD (High-Quality Idempotent MERGE)

# Check if target Delta table exists. Avoid using mode('overwrite') at load time.
if not spark.catalog.tableExists(target_table):
    # Create an empty Delta table with the schema of df_source
    logger.info(f"Target table {target_table} does not exist. Creating table with empty schema.")
    df_source.limit(0).write.format('delta').saveAsTable(target_table)

# Now perform the MERGE operation
try:
    delta_table = DeltaTable.forName(spark, target_table)
    merge_condition = 'tgt.custid = src.custid'
    merge_operation = (delta_table.alias('tgt')
                       .merge(
                           source=df_source.alias('src'), 
                           condition=merge_condition)
                       .whenMatchedUpdateAll()
                       .whenNotMatchedInsertAll())
    merge_operation.execute()
    logger.info(f"Merge completed successfully for table {target_table}.")
except Exception as e:
    logger.error(f"Error during merge operation: {e}")
    raise e

# Log final row count in target table
final_count = spark.table(target_table).count()
logger.info(f"Target table {target_table} now has {final_count} rows.")

# Post-load optimization hints (these would normally be run as spark.sql commands or via Delta Lake utilities)
logger.info(f"Consider running: OPTIMIZE {target_table} ZORDER BY (custid) and VACUUM {target_table} RETAIN 0 HOURS")

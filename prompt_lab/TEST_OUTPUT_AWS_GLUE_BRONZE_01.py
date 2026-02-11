# L2L MODERNIZATION TRACE
# Source: bronze_customers_glue
# Component: PySpark Notebook
# Logic: Ingest Parquet from S3 to Bronze Glue Table with audit columns and partitioning
# Generated At: 2025-02-12T00:00:00Z

import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql import functions as F
from pyspark.sql.types import StringType

# [PARAMETERS]
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'S3_BUCKET', 'SOURCE_PATH'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# [EXTRACT] - Read Parquet from raw S3 location (enforce schema on read if schema evolves or add later)
df_source = spark.read.parquet(args['SOURCE_PATH'])
print(f"[EXTRACT] Rows read from source: {df_source.count()}")

# [TRANSFORM] - Select only required columns and add audit columns
df_selected = df_source.select(
    'customer_key',
    'customer_id',
    'name',
    'email',
    'region'
)
df_bronze = (
    df_selected
    .withColumn('_glue_job_name', F.lit(args['JOB_NAME']).cast(StringType()))
    .withColumn('_ingestion_timestamp', F.current_timestamp())
    .withColumn('_ingestion_date', F.current_date())
    .withColumn('_source_system', F.lit('S3_RAW').cast(StringType()))
    .withColumn('_source_file', F.input_file_name().cast(StringType()))
)
print(f"[TRANSFORM] Rows after adding audit columns: {df_bronze.count()}")

# [LOAD] - Write to S3 Bronze (Parquet/partitioned by date)
df_bronze.write \
    .mode('append') \
    .format('parquet') \
    .option('compression', 'snappy') \
    .option('mergeSchema', 'true') \
    .partitionBy('_ingestion_date') \
    .save(f"s3://{args['S3_BUCKET']}/bronze/customers/")

job.commit()
print(f"\u2705 Bronze ingestion completed: s3://{args['S3_BUCKET']}/bronze/customers/")
# OPTIMIZATION: Consider Glue Crawler for schema update and Athena partition repair.

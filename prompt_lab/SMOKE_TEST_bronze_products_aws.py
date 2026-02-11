import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql import functions as F

# Parse job parameters
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'S3_BUCKET', 'SOURCE_PATH'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Configuration
S3_BUCKET = args['S3_BUCKET']
SOURCE_PATH = args['SOURCE_PATH']
TARGET_PATH = f"s3://{S3_BUCKET}/bronze/products/"

# Read raw data (assuming CSV for Bronze ingestion)
df_source = spark.read \
    .option("header", "true") \
    .option("inferSchema", "true") \
    .csv(SOURCE_PATH)

# Add Bronze audit columns
df_bronze = df_source \
    .withColumn("_glue_job_name", F.lit(args['JOB_NAME'])) \
    .withColumn("_ingestion_timestamp", F.current_timestamp()) \
    .withColumn("_ingestion_date", F.current_date()) \
    .withColumn("_source_system", F.lit("MSSQL")) \
    .withColumn("_source_file", F.input_file_name())

# Write to S3 Bronze (Parquet with partitioning)
df_bronze.write \
    .mode("append") \
    .format("parquet") \
    .option("compression", "snappy") \
    .option("mergeSchema", "true") \
    .partitionBy("_ingestion_date") \
    .save(TARGET_PATH)

job.commit()
print(f"\u2705 Bronze ingestion completed: {TARGET_PATH}")
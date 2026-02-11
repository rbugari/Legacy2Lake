import sys
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql import functions as F
from pyspark.sql.window import Window
import traceback

args = getResolvedOptions(sys.argv, ['JOB_NAME', 'S3_BUCKET'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

S3_BUCKET = args['S3_BUCKET']
BRONZE_PATH = f"s3://{S3_BUCKET}/bronze/orders/"
SILVER_PATH = f"s3://{S3_BUCKET}/silver/orders/"
QUARANTINE_PATH = f"s3://{S3_BUCKET}/quarantine/orders/"
REJECT_REASON_COL = "_rejection_reason"

try:
    # Read Bronze data
    df_bronze = spark.read.parquet(BRONZE_PATH)

    # Deduplication by primary keys (order_id, customer_id)
    window_spec = Window.partitionBy("order_id", "customer_id").orderBy(F.col("_ingestion_timestamp").desc())
    df_deduped = df_bronze.withColumn("_row_num", F.row_number().over(window_spec)).filter(F.col("_row_num") == 1).drop("_row_num")

    # Data Quality Checks
    df_rejects = df_deduped \
        .withColumn(REJECT_REASON_COL,
            F.when(F.col("order_id").isNull(), "order_id is NULL")
            .when(F.col("amount").isNull(), "amount is NULL")
            .when(F.col("amount") <= 0, "amount <= 0")
            .when(F.col("order_date").isNull(), "order_date is NULL")
            .when(F.year(F.col("order_date")) < 2020, "order_date before 2020")
            .otherwise(None)
        )
    df_clean = df_rejects.filter(F.col(REJECT_REASON_COL).isNull()).drop(REJECT_REASON_COL)
    df_quarantine = df_rejects.filter(F.col(REJECT_REASON_COL).isNotNull())

    # Write rejects to quarantine
    if df_quarantine.count() > 0:
        df_quarantine.withColumn("_processed_timestamp", F.current_timestamp()) \
            .write.mode("append") \
            .format("parquet") \
            .option("compression", "snappy") \
            .save(QUARANTINE_PATH)

    # Type Standardization & Audit
    df_silver = df_clean \
        .withColumn("amount", F.col("amount").cast("decimal(18,2)")) \
        .withColumn("order_date", F.to_date(F.col("order_date"))) \
        .withColumn("_processed_timestamp", F.current_timestamp()) \
        .withColumn("_silver_job_name", F.lit(args['JOB_NAME'])) \
        .withColumn("_quality_score", F.lit(100))

    # Write to S3 Silver
    df_silver.coalesce(10).write \
        .mode("overwrite") \
        .format("parquet") \
        .option("compression", "snappy") \
        .partitionBy("order_date") \
        .save(SILVER_PATH)

    print(f"✅ Silver transformation completed: {SILVER_PATH}")
except Exception as e:
    print("❌ Error in Silver job:", e)
    traceback.print_exc()
    raise e
finally:
    job.commit()
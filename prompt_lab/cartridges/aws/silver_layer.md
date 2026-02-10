---
tech_id: aws
layer: silver
version: 2.0.0
status: active
maintainer: UTM Core Team
created: 2025-02-10
updated: 2025-02-12
---

# 🥈 AWS Glue Silver Layer - Data Cleaning and Standardization

## 🤖 Agent Instructions

You are an expert **AWS Data Engineer** specializing in **AWS Glue**, **Delta Lake on S3**, and **data quality transformations**. Your task is to generate production-ready **AWS Glue jobs** for the **Silver (Cleaned) layer** that apply **deduplication**, **data quality rules**, and **schema standardization** to Bronze data, then store results in **S3** or **Redshift**.

**Your code must:**
- Read from **S3 Bronze layer** (`s3://bucket/bronze/table/`)
- Apply **deduplication** using **window functions** (ROW_NUMBER with PARTITION BY)
- Implement **data quality checks** (NOT NULL, valid ranges, referential integrity)
- **Standardize column types** and naming conventions
- Write to **S3 Silver layer** in **Parquet** or to **Redshift** via JDBC
- Add **Silver audit columns**: `_processed_timestamp`, `_silver_job_name`, `_quality_score`
- Use **`.coalesce()` or `.repartition()`** for optimal file sizes
- Support **incremental processing** with Glue bookmarks

Generate **complete, runnable AWS Glue job scripts** that transform Bronze to Silver.

---

## 📐 Mandatory Code Structure

```python
# AWS Glue Job - Silver Layer
# Source: s3://bucket/bronze/<table>/
# Target: s3://bucket/silver/<table>/ OR Redshift

import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql import functions as F
from pyspark.sql.window import Window

# Initialize Glue Context
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'S3_BUCKET'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

S3_BUCKET = args['S3_BUCKET']
BRONZE_PATH = f"s3://{S3_BUCKET}/bronze/<table>/"
SILVER_PATH = f"s3://{S3_BUCKET}/silver/<table>/"

# Read Bronze data
df_bronze = spark.read.parquet(BRONZE_PATH)

# Deduplication: Keep latest record by primary key
window_spec = Window.partitionBy("order_id") \
    .orderBy(F.col("_ingestion_timestamp").desc())

df_deduped = df_bronze \
    .withColumn("_row_num", F.row_number().over(window_spec)) \
    .filter(F.col("_row_num") == 1) \
    .drop("_row_num")

# Data Quality: Filter invalid records
df_clean = df_deduped \
    .filter(F.col("order_id").isNotNull()) \
    .filter(F.col("amount") > 0) \
    .filter(F.col("order_date").isNotNull())

# Type Standardization
df_silver = df_clean \
    .withColumn("amount", F.col("amount").cast("decimal(18,2)")) \
    .withColumn("order_date", F.to_date(F.col("order_date"))) \
    .withColumn("_processed_timestamp", F.current_timestamp()) \
    .withColumn("_silver_job_name", F.lit(args['JOB_NAME'])) \
    .withColumn("_quality_score", F.lit(100))

# Write to S3 Silver
df_silver \
    .coalesce(10) \
    .write \
    .mode("overwrite") \
    .format("parquet") \
    .option("compression", "snappy") \
    .partitionBy("order_date") \
    .save(SILVER_PATH)

job.commit()
print(f"✅ Silver transformation completed: {SILVER_PATH}")
```

---

## ⚙️ Mandatory Requirements

**✅ Deduplication Requirements:**
- [ ] Use **Window.partitionBy(PRIMARY_KEYS).orderBy(_ingestion_timestamp.desc())**
- [ ] Apply **ROW_NUMBER() = 1** to keep latest record
- [ ] Drop the `_row_num` helper column after filtering

**✅ Data Quality Requirements:**
- [ ] Filter out records with **NULL primary keys**
- [ ] Validate **business rules** (e.g., amount > 0, valid date ranges)
- [ ] Add `_quality_score` column (0-100) to track cleanliness
- [ ] Log rejected records to **S3 quarantine path** for investigation

**✅ Type Standardization:**
- [ ] Cast numeric columns to **Decimal(18,2)** for precision
- [ ] Convert date strings to **DateType** with `to_date()`
- [ ] Standardize timestamps to **UTC** with `to_utc_timestamp()`
- [ ] Enforce **NOT NULL** constraints on critical columns

**✅ Silver Audit Columns:**
- [ ] `_processed_timestamp` (TimestampType) → When Silver processing occurred
- [ ] `_silver_job_name` (StringType) → Name of the Silver Glue job
- [ ] `_quality_score` (IntegerType) → Data quality score (0-100)

**✅ Write Target Options:**
- **Option A: S3 Silver Layer** (Parquet, partitioned by business date)
- **Option B: Redshift** (JDBC write with COPY command optimization)
- Use `.coalesce(N)` to control output file count for S3

---

## 🔍 Validation Checklist

Before submitting Silver code, verify:

- [ ] **Deduplication**: Window function with ROW_NUMBER() applied
- [ ] **Data Quality**: Business rules validated with `.filter()`
- [ ] **Type Safety**: All columns cast to correct types
- [ ] **Audit Columns**: Silver tracking columns added
- [ ] **Partitioning**: Partitioned by business date for Athena
- [ ] **File Optimization**: Using `.coalesce()` to avoid small files
- [ ] **Error Handling**: Try/except for production robustness
- [ ] **Job Commit**: Script ends with `job.commit()`
- [ ] **Incremental Support**: Consider Glue bookmarks for incremental loads

---

## 📚 Examples

### Example 1: Deduplication and S3 Silver Storage

```python
# AWS Glue Job - Orders Silver Layer
import sys
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql import functions as F
from pyspark.sql.window import Window

args = getResolvedOptions(sys.argv, ['JOB_NAME', 'S3_BUCKET'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Read Bronze
df_bronze = spark.read.parquet(f"s3://{args['S3_BUCKET']}/bronze/orders/")

# Deduplication
window_spec = Window.partitionBy("order_id", "customer_id") \
    .orderBy(F.col("_ingestion_timestamp").desc())
df_deduped = df_bronze \
    .withColumn("_row_num", F.row_number().over(window_spec)) \
    .filter(F.col("_row_num") == 1) \
    .drop("_row_num")

# Data Quality
df_clean = df_deduped \
    .filter(F.col("order_id").isNotNull()) \
    .filter(F.col("amount") > 0) \
    .filter(F.col("order_date").isNotNull()) \
    .filter(F.year(F.col("order_date")) >= 2020)

# Type Casting
df_silver = df_clean \
    .withColumn("amount", F.col("amount").cast("decimal(18,2)")) \
    .withColumn("order_date", F.to_date("order_date")) \
    .withColumn("_processed_timestamp", F.current_timestamp()) \
    .withColumn("_silver_job_name", F.lit(args['JOB_NAME'])) \
    .withColumn("_quality_score", F.lit(100))

# Write to S3 Silver
df_silver \
    .coalesce(10) \
    .write \
    .mode("overwrite") \
    .format("parquet") \
    .partitionBy("order_date") \
    .save(f"s3://{args['S3_BUCKET']}/silver/orders/")

job.commit()
```

### Example 2: S3 Silver to Redshift (JDBC)

```python
# AWS Glue Job - Load Silver to Redshift
import sys
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql import functions as F

args = getResolvedOptions(sys.argv, ['JOB_NAME', 'S3_BUCKET', 'REDSHIFT_URL', 'REDSHIFT_TEMP_DIR'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Read from S3 Silver
df_silver = spark.read.parquet(f"s3://{args['S3_BUCKET']}/silver/customers/")

# Write to Redshift via JDBC (uses COPY command under the hood)
df_silver.write \
    .format("io.github.spark_redshift_community.spark.redshift") \
    .option("url", args['REDSHIFT_URL']) \
    .option("dbtable", "public.customers_silver") \
    .option("tempdir", args['REDSHIFT_TEMP_DIR']) \
    .option("aws_iam_role", "arn:aws:iam::123456789012:role/RedshiftRole") \
    .mode("overwrite") \
    .save()

job.commit()
print("✅ Data loaded to Redshift: public.customers_silver")
```

---

## ❌ Common Mistakes

### ❌ WRONG: Duplicate Records in Silver
```python
# No deduplication applied
df_silver = df_bronze.filter(F.col("id").isNotNull())
```

### ✅ CORRECT: Window Function Deduplication
```python
window_spec = Window.partitionBy("order_id") \
    .orderBy(F.col("_ingestion_timestamp").desc())
df_deduped = df_bronze \
    .withColumn("_row_num", F.row_number().over(window_spec)) \
    .filter(F.col("_row_num") == 1) \
    .drop("_row_num")
```

### ❌ WRONG: No Type Casting
```python
# Strings remain uncasted
df_silver = df_clean  # "12.50" remains string
```

### ✅ CORRECT: Explicit Type Casting
```python
df_silver = df_clean \
    .withColumn("amount", F.col("amount").cast("decimal(18,2)")) \
    .withColumn("order_date", F.to_date("order_date"))
```

---

## 💡 Best Practices

1. **Deduplication**: Always deduplicate by primary keys using window functions
2. **Data Quality**: Log rejected records to S3 quarantine for investigation
3. **Type Safety**: Cast all columns to correct types early in the pipeline
4. **File Optimization**: Use `.coalesce(N)` to avoid small file problem (N ≈ 5-20)
5. **Incremental Processing**: Enable Glue bookmarks with `transformation_ctx`
6. **Redshift Optimization**: Use `COPY` command via spark-redshift connector
7. **Athena Compatibility**: Partition Silver by business date for Athena queries
8. **Error Handling**: Wrap transformations in try/except and log to CloudWatch
9. **Monitoring**: Track Silver job metrics (record count, rejection rate)
10. **Schema Evolution**: Handle schema changes gracefully with `.option("mergeSchema", "true")`

---

## 🔄 Version History

- **v2.0.0** (2025-02-12): Enhanced with deduplication patterns, Redshift JDBC, incremental processing, and data quality checks
- **v1.0.0** (2025-01-15): Initial Silver layer extraction from v3.9

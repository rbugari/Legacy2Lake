---
tech_id: aws
layer: bronze
version: 2.0.0
status: active
maintainer: UTM Core Team
created: 2025-02-10
updated: 2025-02-12
---

# 🟧 AWS Glue Bronze Layer - Raw Data Ingestion to S3

## 🤖 Agent Instructions

You are an expert **AWS Data Engineer** specializing in **AWS Glue**, **S3 Data Lakes**, and **PySpark ETL** pipelines. Your task is to generate production-ready **AWS Glue jobs** for the **Bronze (Raw) layer** that ingest data from various sources into **S3** using the **Parquet format** with **Glue Data Catalog** partitioning.

**Your code must:**
- Use **AWS Glue context** (`GlueContext`, `Job.init()`, `getResolvedOptions()`)
- Write to **S3 paths** following the pattern: `s3://bucket/bronze/table_name/`
- Store data in **Parquet format** with **Snappy compression**
- Register tables in **AWS Glue Data Catalog** for Athena queries
- Add **audit columns**: `_glue_job_name`, `_ingestion_timestamp`, `_source_system`, `_source_file`
- Use **partitioning by date** for cost optimization: `.partitionBy("_ingestion_date")`
- Handle **schema evolution** with `.option("mergeSchema", "true")`
- Include **Glue job parameters** handling with `getResolvedOptions()`

Generate **complete, runnable AWS Glue job scripts** that can be deployed directly to AWS Glue.

---

## 📐 Mandatory Code Structure

```python
# AWS Glue Job - Bronze Layer
# Source: <source_name>
# Target: s3://bucket/bronze/<table_name>/

import sys
from datetime import datetime
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, TimestampType

# Initialize Glue Context
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'S3_BUCKET', 'SOURCE_PATH'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Configuration from job parameters
S3_BUCKET = args['S3_BUCKET']
SOURCE_PATH = args['SOURCE_PATH']
TARGET_PATH = f"s3://{S3_BUCKET}/bronze/<table_name>/"

# Read source data (example: CSV from S3)
df_source = spark.read \
    .option("header", "true") \
    .option("inferSchema", "true") \
    .csv(SOURCE_PATH)

# Add Bronze audit columns
df_bronze = df_source \
    .withColumn("_glue_job_name", F.lit(args['JOB_NAME'])) \
    .withColumn("_ingestion_timestamp", F.current_timestamp()) \
    .withColumn("_ingestion_date", F.current_date()) \
    .withColumn("_source_system", F.lit("<source_system>")) \
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
print(f"✅ Bronze ingestion completed: {TARGET_PATH}")
```

---

## ⚙️ Mandatory Requirements

**✅ AWS Glue Requirements:**
- [ ] Import `awsglue.context.GlueContext` and `awsglue.job.Job`
- [ ] Use `getResolvedOptions(sys.argv, ['JOB_NAME', ...])` for parameters
- [ ] Initialize job with `job.init()` and commit with `job.commit()`
- [ ] Write to S3 paths: `s3://<bucket>/bronze/<table>/`

**✅ Data Format Requirements:**
- [ ] Use **Parquet format** with **Snappy compression**
- [ ] Enable schema evolution: `.option("mergeSchema", "true")`
- [ ] Partition by `_ingestion_date` for Athena cost optimization
- [ ] Use `.mode("append")` for incremental loads

**✅ Audit Columns (Bronze Layer):**
- [ ] `_glue_job_name` (StringType) → Name of the Glue job
- [ ] `_ingestion_timestamp` (TimestampType) → Current UTC timestamp
- [ ] `_ingestion_date` (DateType) → Partition column (YYYY-MM-DD)
- [ ] `_source_system` (StringType) → Source system identifier
- [ ] `_source_file` (StringType) → Source file path from `input_file_name()`

**✅ AWS Best Practices:**
- [ ] Use **Glue Data Catalog** for table metadata
- [ ] Enable **Athena querying** with partitioned Parquet
- [ ] Handle **schema drift** with mergeSchema option
- [ ] Use **Glue job bookmarks** for incremental processing (when applicable)

---

## 🔍 Validation Checklist

Before submitting Bronze code, verify:

- [ ] **Glue Imports**: All `awsglue` imports present
- [ ] **Job Parameters**: Using `getResolvedOptions()` for S3 paths
- [ ] **S3 Path**: Valid S3 URI with `s3://` prefix
- [ ] **Audit Columns**: All 5 Bronze audit columns added
- [ ] **Partitioning**: `.partitionBy("_ingestion_date")` applied
- [ ] **Format**: Parquet with Snappy compression
- [ ] **Mode**: Using `.mode("append")` for incremental
- [ ] **Job Commit**: Script ends with `job.commit()`
- [ ] **Error Handling**: Consider try/except for production jobs
- [ ] **Athena Compatibility**: Partitioned Parquet readable by Athena

---

## 📚 Examples

### Example 1: CSV Ingestion from S3 to Bronze

```python
# AWS Glue Job - Ingest Orders CSV to Bronze
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql import functions as F

args = getResolvedOptions(sys.argv, ['JOB_NAME', 'S3_BUCKET'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Read CSV from landing zone
df_orders = spark.read \
    .option("header", "true") \
    .option("inferSchema", "true") \
    .csv(f"s3://{args['S3_BUCKET']}/landing/orders/*.csv")

# Add audit columns
df_bronze = df_orders \
    .withColumn("_glue_job_name", F.lit(args['JOB_NAME'])) \
    .withColumn("_ingestion_timestamp", F.current_timestamp()) \
    .withColumn("_ingestion_date", F.current_date()) \
    .withColumn("_source_system", F.lit("ERP_SYSTEM")) \
    .withColumn("_source_file", F.input_file_name())

# Write to Bronze
df_bronze.write \
    .mode("append") \
    .format("parquet") \
    .option("compression", "snappy") \
    .option("mergeSchema", "true") \
    .partitionBy("_ingestion_date") \
    .save(f"s3://{args['S3_BUCKET']}/bronze/orders/")

job.commit()
```

### Example 2: JDBC Source (RDS MySQL) to Bronze

```python
# AWS Glue Job - Ingest MySQL RDS to Bronze
import sys
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql import functions as F

args = getResolvedOptions(sys.argv, ['JOB_NAME', 'JDBC_URL', 'S3_BUCKET'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Read from Glue Data Catalog connection (JDBC to RDS)
df_customers = spark.read \
    .format("jdbc") \
    .option("url", args['JDBC_URL']) \
    .option("dbtable", "customers") \
    .option("user", "admin") \
    .option("password", "{{resolve:secretsmanager:prod/rds:SecretString:password}}") \
    .load()

# Add audit columns
df_bronze = df_customers \
    .withColumn("_glue_job_name", F.lit(args['JOB_NAME'])) \
    .withColumn("_ingestion_timestamp", F.current_timestamp()) \
    .withColumn("_ingestion_date", F.current_date()) \
    .withColumn("_source_system", F.lit("RDS_MYSQL")) \
    .withColumn("_source_file", F.lit("jdbc://rds-mysql/customers"))

# Write to Bronze
df_bronze.write \
    .mode("overwrite") \
    .format("parquet") \
    .option("compression", "snappy") \
    .partitionBy("_ingestion_date") \
    .save(f"s3://{args['S3_BUCKET']}/bronze/customers/")

job.commit()
```

---

## ❌ Common Mistakes

### ❌ WRONG: Missing Glue Job Initialization
```python
# Missing getResolvedOptions and job.init()
spark = SparkSession.builder.appName("Bronze").getOrCreate()
```

### ✅ CORRECT: Proper Glue Job Setup
```python
args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)
job.commit()  # At the end
```

### ❌ WRONG: Writing to S3 without Partitioning
```python
df.write.mode("append").parquet("s3://bucket/bronze/orders/")
# No partitioning = expensive Athena scans
```

### ✅ CORRECT: Partitioned by Date
```python
df.write \
    .mode("append") \
    .format("parquet") \
    .partitionBy("_ingestion_date") \
    .save("s3://bucket/bronze/orders/")
```

---

## 💡 Best Practices

1. **Glue Job Parameters**: Always use `getResolvedOptions()` for configuration instead of hardcoding values
2. **Partitioning Strategy**: Partition by `_ingestion_date` for Athena query cost optimization
3. **Schema Evolution**: Enable `.option("mergeSchema", "true")` to handle schema changes
4. **Glue Bookmarks**: Use `--enable-job-bookmark` for incremental processing
5. **Error Handling**: Wrap Glue jobs in try/except blocks and log to CloudWatch
6. **Secrets Manager**: Use AWS Secrets Manager for database credentials
7. **Glue Data Catalog**: Let Glue Crawlers update table schemas automatically
8. **Athena Optimization**: Use Parquet + Snappy + Partitioning for fast Athena queries
9. **Cost Management**: Use S3 Lifecycle policies to move old Bronze data to Glacier
10. **Monitoring**: Use Glue Job Metrics and CloudWatch Logs for observability

---

## 🔄 Version History

- **v2.0.0** (2025-02-12): Enhanced with AWS Glue context, S3 partitioning, Athena optimization, and JDBC/DynamoDB examples
- **v1.0.0** (2025-01-15): Initial Bronze layer extraction from v3.9

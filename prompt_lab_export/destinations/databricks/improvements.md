# Databricks PySpark Best Practices (v3.5)

> **Last Updated**: 2026-02-01  
> **Source**: 2024 Databricks and Delta Lake optimization research

## File Sizing and Compaction

**Target File Size**: 100MB - 1GB per file

Files outside this range cause performance issues:
- **Too small** (< 100MB): Excessive I/O overhead, slow list operations
- **Too large** (> 1GB): Limits data skipping effectiveness, hard to parallelize

**OPTIMIZE Command**:
```python
# Compact small files into optimal sizes
OPTIMIZE catalog.schema.table_name
```

**When to run**:
- After bulk inserts (> 1GB added)
- When small file count > 100
- Weekly for high-write tables

**Best Practice**: Run OPTIMIZE on separate job cluster with compute-optimized instances.

---

## Liquid Clustering (Recommended 2024+)

**What is it**: Modern alternative to Z-ORDER with incremental optimization.

**Why use it**:
- ✅ More flexible than Z-ORDER (can change clustering keys without full rewrite)
- ✅ Incremental optimization (only unclustered data is reorganized)
- ✅ Automatically clusters new data on write
- ✅ Better for evolving query patterns and schemas

**Syntax**:
```python
# Create table with Liquid Clustering
CREATE OR REPLACE TABLE catalog.schema.customers
CLUSTER BY (customer_id, transaction_date, region)
AS SELECT * FROM source_table
```

**Column Selection Rules**:
- Use frequently filtered/joined columns
- High cardinality columns (customer_id, product_id)
- Maximum 4 columns
- Order doesn't matter (unlike Z-ORDER)

**Use Cases**:
- Tables with skewed data distribution
- Frequent data ingestion
- Evolving query patterns
- Alternative to traditional partitioning

---

## Z-ORDER (Read-Heavy Workloads)

**When to use**: Read-heavy workloads where comprehensive data reorganization yields strong initial performance.

**Syntax**:
```python
OPTIMIZE catalog.schema.table_name
ZORDER BY (customer_id, product_id)
```

**Column Selection Rules**:
- **Do**: High-cardinality columns (customer_id, order_id)
- **Don't**: Low-cardinality columns (use partitioning instead)
- **Don't**: Partition keys (already organized)
- **Limit**: Maximum 4 columns

**Frequency**: Run after large data loads or weekly for active tables.

**Combination with Partitioning**:
```python
# Partition by date, Z-ORDER within partitions by customer_id
CREATE TABLE sales
PARTITIONED BY (transaction_date)
AS SELECT * FROM source

OPTIMIZE sales
ZORDER BY (customer_id, product_id)
```

---

## Partitioning Strategy

**When to partition**:
- ✅ Time-series data (partition by date/month)
- ✅ Tables > 1TB
- ✅ Range-based queries (WHERE date BETWEEN...)

**When NOT to partition**:
- ❌ Tables < 1TB (use Liquid Clustering instead)
- ❌ Partition size would be < 1GB
- ❌ High number of partitions (> 10,000)

**Syntax**:
```python
CREATE TABLE events
PARTITIONED BY (event_date)
AS SELECT * FROM source
```

**Dual Optimization**:
```python
# Partition + Z-ORDER for best performance
CREATE TABLE sales
PARTITIONED BY (year, month)
AS SELECT * FROM source

OPTIMIZE sales PARTITION (year=2024)
ZORDER BY (customer_id)
```

---

## Idempotent Operations (Critical!)

**Always use MERGE** (not APPEND) for data updates to ensure idempotency.

### ✅ GOOD: Idempotent MERGE
```python
from delta.tables import DeltaTable

target = DeltaTable.forName(spark, "catalog.schema.target_table")

target.alias("t").merge(
    source_df.alias("s"),
    "t.id = s.id"  # Match condition
).whenMatchedUpdateAll(
    condition="s.updated_at > t.updated_at"  # Optional: only update if newer
).whenNotMatchedInsertAll().execute()
```

### ❌ BAD: Non-Idempotent APPEND
```python
# NEVER DO THIS! Creates duplicates on re-run
source_df.write.mode("append").saveAsTable("target_table")
```

### Slowly Changing Dimension (SCD Type 2)
```python
# Step 1: Expire old versions
target.alias("t").merge(
    changed_records.alias("s"),
    "t.customer_id = s.customer_id AND t.is_current = true"
).whenMatchedUpdate(
    set={
        "is_current": "false",
        "end_date": "current_timestamp()"
    }
).execute()

# Step 2: Insert new versions
new_versions.write.mode("append").saveAsTable("dim_customer")
```

---

## PySpark Code Optimization

### 1. Enable Adaptive Query Execution (AQE)
```python
# ALWAYS enable AQE (enabled by default in Databricks Runtime 13+)
spark.conf.set("spark.sql.adaptive.enabled", "true")
```

**Benefits**:
- Dynamic partition coalescing
- Dynamic join strategy switching
- Dynamic skew join handling

### 2. Avoid Python UDFs
Python UDFs are slow due to serialization between Python ↔ JVM.

**Alternatives**:
```python
# BAD: Python UDF
from pyspark.sql.functions import udf
@udf("string")
def clean_email(email):
    return email.lower().strip()

# GOOD: Native Spark function
from pyspark.sql.functions import lower, trim
df = df.withColumn("email", trim(lower(col("email"))))

# ACCEPTABLE: Pandas UDF (vectorized, faster than Python UDF)
from pyspark.sql.functions import pandas_udf
@pandas_udf("string")
def advanced_transform(series: pd.Series) -> pd.Series:
    return series.apply(complex_logic)
```

### 3. Broadcast Small Tables
```python
from pyspark.sql.functions import broadcast

# Broadcast dimension tables < 1GB
fact_df.join(
    broadcast(dim_customer),  # Prevents shuffle
    "customer_id"
)
```

### 4. Maintain Table Statistics
```python
# Update statistics after bulk changes
ANALYZE TABLE catalog.schema.table_name COMPUTE STATISTICS
```

Benefits: Better query plans, optimal join strategies, accurate cost estimation.

### 5. Never Cache Delta Tables
```python
# NEVER DO THIS with Delta Lake!
df = spark.read.table("delta_table")
df.cache()  # ❌ Breaks data skipping, causes stale reads
```

Delta Lake has built-in caching and data skipping. External caching negates these benefits.

---

## Schema Evolution

### Automatic Schema Evolution
```python
# Allow new columns to be added automatically
source_df.write \
    .format("delta") \
    .mode("append") \
    .option("mergeSchema", "true") \
    .saveAsTable("target_table")
```

### Schema Override (Careful!)
```python
# Completely replace schema (deletes columns not in source)
.option("overwriteSchema", "true")
```

---

## Vacuum and Time Travel

### Vacuum Old Files
```python
# Remove files older than retention period (default: 7 days)
VACUUM catalog.schema.table_name RETAIN 168 HOURS  -- 7 days
```

**Important**: Vacuum deletes historical versions. Configure retention based on time-travel needs.

### Time Travel
```python
# Query historical version
df = spark.read.format("delta") \
    .option("versionAsOf", 5) \
    .table("catalog.schema.table_name")

# Or by timestamp
df = spark.read.format("delta") \
    .option("timestampAsOf", "2024-01-15") \
    .table("catalog.schema.table_name")
```

---

## Performance Checklist

When generating PySpark code, ensure:
- [ ] MERGE used for updates (not append)
- [ ] Liquid Clustering applied on high-cardinality columns (tables > 100GB)
- [ ] Files sized 100MB-1GB (run OPTIMIZE regularly)
- [ ] AQE enabled
- [ ] No Python UDFs (use native functions or Pandas UDFs)
- [ ] Broadcast hints on small dimension tables
- [ ] Never cache Delta tables
- [ ] Table statistics maintained
- [ ] Schema evolution enabled with mergeSchema=true
- [ ] Appropriate partitioning (if table > 1TB)

---

## Code Generation Templates

### Bronze Layer (Raw Ingestion)
```python
# Read from source (Parquet, JSON, CSV, JDBC)
source_df = spark.read.format("parquet").load("s3://bucket/path")

# Write to Bronze (no transformation, schema evolution enabled)
source_df.write \
    .format("delta") \
    .mode("append") \
    .option("mergeSchema", "true") \
    .partitionBy("ingestion_date") \
    .saveAsTable("bronze.raw_events")
```

### Silver Layer (Cleaned/Conformed)
```python
# Read from Bronze
bronze_df = spark.read.table("bronze.raw_events")

# Clean and conform
silver_df = (bronze_df
    .filter(col("event_type").isNotNull())  # Remove nulls
    .withColumn("event_ts", to_timestamp(col("timestamp")))  # Parse dates
    .withColumn("email", lower(trim(col("email"))))  # Standardize
    .dropDuplicates(["event_id"])  # Dedup
)

# MERGE to Silver (idempotent)
from delta.tables import DeltaTable
target = DeltaTable.forName(spark, "silver.events")

target.alias("t").merge(
    silver_df.alias("s"),
    "t.event_id = s.event_id"
).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
```

### Gold Layer (Business Aggregates)
```python
# Read from Silver
silver_df = spark.read.table("silver.sales")

# Aggregate for business reporting
gold_df = (silver_df
    .groupBy("customer_id", "transaction_date")
    .agg(
        sum("amount").alias("total_sales"),
        count("*").alias("transaction_count"),
        avg("amount").alias("avg_transaction_size")
    )
)

# Write to Gold
gold_df.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("gold.customer_daily_sales")

# Optimize for query performance
OPTIMIZE gold.customer_daily_sales
ZORDER BY (customer_id)
```

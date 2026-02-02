# SSIS Migration Patterns (v3.5)

> **Last Updated**: 2026-02-01  
> **Purpose**: Translate SSIS packages to modern cloud-native data platforms

## Component Translation Matrix

| SSIS Component | Databricks (PySpark) | Snowflake SQL |
|----------------|---------------------|---------------|
| **Data Flow Task** | DataFrame transformations | `INSERT INTO ... SELECT` |
| **OLE DB Source** | `spark.read.format("jdbc")` | External Stage + `COPY INTO` |
| **Flat File Source** | `spark.read.csv()` | `CREATE STAGE` + `COPY INTO` |
| **Derived Column** | `.withColumn()` | `SELECT ..., expr AS new_col` |
| **Lookup Transform** | `.join()` with broadcast | `LEFT JOIN` |
| **Conditional Split** | `.filter()` or `.where()` | `CASE WHEN` in WHERE |
| **Aggregate** | `.groupBy().agg()` | `GROUP BY` with aggregates |
| **Merge Join** | `.join()` | `JOIN` (type auto-optimized) |
| **Sort** | `.orderBy()` (avoid in ETL) | `ORDER BY` (avoid in ETL) |
| **Union All** | `.union()` | `UNION ALL` |
| **Multicast** | Cache df, multiple writes | Multiple CTEs |
| **Slowly Changing Dimension** | Delta MERGE (SCD Type 2) | MERGE with windowing |
| **Execute SQL Task** | `spark.sql()` | Execute as SQL statement |
| **Script Component** | Python UDF or native functions | JavaScript UDF (avoid) |
| **Fuzzy Lookup** | MLlib approxSimilarityJoin | N/A (pre-process with external tool) |

---

## Common SSIS Patterns → Modern Equivalent

### 1. Slowly Changing Dimension (SCD Type 2)

#### SSIS Approach
- Lookup existing records
- Conditional split (new vs changed)
- Update old versions (set `is_current = false`)
- Insert new versions

#### Databricks (PySpark)
```python
from delta.tables import DeltaTable
from pyspark.sql.functions import col, current_timestamp, lit

# Step 1: Identify changed records
changed_records = source_df.alias("s").join(
    target_df.filter("is_current = true").alias("t"),
    "customer_id"
).where(
    "(s.name != t.name) OR (s.email != t.email)"  # Detect changes
).select("s.*")

# Step 2: Expire old versions
target_table = DeltaTable.forName(spark, "dim_customer")
target_table.alias("t").merge(
    changed_records.alias("s"),
    "t.customer_id = s.customer_id AND t.is_current = true"
).whenMatchedUpdate(
    set={
        "is_current": lit(False),
        "end_date": current_timestamp()
    }
).execute()

# Step 3: Insert new versions (for changed + new records)
new_and_changed = source_df.join(
    target_df.filter("is_current = true"),
    "customer_id",
    "left_anti"  # New records
).unionAll(changed_records)  # + Changed records

new_and_changed.withColumn("is_current", lit(True)) \
    .withColumn("start_date", current_timestamp()) \
    .withColumn("end_date", lit(None)) \
    .write.mode("append").saveAsTable("dim_customer")
```

#### Snowflake
```sql
-- Step 1: Expire old versions
UPDATE dim_customer AS t
SET 
    is_current = FALSE,
    end_date = CURRENT_TIMESTAMP
FROM staging_customer AS s
WHERE t.customer_id = s.customer_id
  AND t.is_current = TRUE
  AND (t.name != s.name OR t.email != s.email);

-- Step 2: Insert new versions
INSERT INTO dim_customer (customer_id, name, email, is_current, start_date)
SELECT 
    s.customer_id,
    s.name,
    s.email,
    TRUE,
    CURRENT_TIMESTAMP
FROM staging_customer s
LEFT JOIN dim_customer t 
    ON s.customer_id = t.customer_id AND t.is_current = TRUE
WHERE t.customer_id IS NULL  -- New
   OR (t.name != s.name OR t.email != s.email);  -- Changed
```

### 2. Incremental Load (Watermark Pattern)

#### SSIS Approach
- Execute SQL Task: Get max timestamp from target
- Store in package variable
- OLE DB Source: `WHERE modified_date > ?` (parameter)

#### Databricks
```python
# Get last watermark
last_watermark = spark.sql("""
    SELECT COALESCE(MAX(modified_date), '1900-01-01') 
    FROM target_table
""").collect()[0][0]

# Read only new/changed records
incremental_df = (spark.read
    .format("jdbc")
    .option("url", "jdbc:sqlserver://...")
    .option("dbtable", "source_table")
    .option("query", f"""
        SELECT * FROM source_table 
        WHERE modified_date > '{last_watermark}'
    """)
    .load()
)

# MERGE into target (idempotent)
from delta.tables import DeltaTable
target = DeltaTable.forName(spark, "target_table")
target.alias("t").merge(
    incremental_df.alias("s"),
    "t.id = s.id"
).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
```

#### Snowflake
```sql
-- Create watermark table
CREATE TABLE IF NOT EXISTS watermark (
    table_name VARCHAR,
    last_loaded_timestamp TIMESTAMP_NTZ
);

-- Incremental MERGE
MERGE INTO target_table t
USING (
    SELECT * FROM source_table
    WHERE modified_date > (
        SELECT COALESCE(MAX(last_loaded_timestamp), '1900-01-01'::TIMESTAMP)
        FROM watermark WHERE table_name = 'target_table'
    )
) s
ON t.id = s.id
WHEN MATCHED THEN UPDATE SET t.value = s.value, t.modified_date = s.modified_date
WHEN NOT MATCHED THEN INSERT (id, value, modified_date) 
    VALUES (s.id, s.value, s.modified_date);

-- Update watermark
MERGE INTO watermark w
USING (SELECT 'target_table' AS tn, CURRENT_TIMESTAMP AS ts) s
ON w.table_name = s.tn
WHEN MATCHED THEN UPDATE SET last_loaded_timestamp = s.ts
WHEN NOT MATCHED THEN INSERT (table_name, last_loaded_timestamp) 
    VALUES (s.tn, s.ts);
```

### 3. Lookup Transform

#### SSIS Approach
- Lookup component with cache mode
- Match on key columns
- Add columns from reference table

#### Databricks
```python
from pyspark.sql.functions import broadcast

# For small dimension tables (< 1GB), broadcast to avoid shuffle
fact_df = spark.read.table("fact_sales")
dim_customer = spark.read.table("dim_customer").filter("is_current = true")

enriched_df = fact_df.join(
    broadcast(dim_customer),  # Broadcast small table
    fact_df.customer_id == dim_customer.customer_id,
    "left"  # LEFT JOIN preserves all fact rows
).select(
    fact_df["*"],
    dim_customer.customer_name,
    dim_customer.customer_segment
)
```

#### Snowflake
```sql
-- Standard LEFT JOIN (optimizer handles strategy)
SELECT 
    f.*,
    d.customer_name,
    d.customer_segment
FROM fact_sales f
LEFT JOIN dim_customer d
    ON f.customer_id = d.customer_id
    AND d.is_current = TRUE;
```

### 4. Conditional Split

#### SSIS Approach
- Conditional split component
- Multiple outputs based on expressions

#### Databricks
```python
from pyspark.sql.functions import when, col

# Approach 1: Separate DataFrames
valid_df = source_df.filter(col("amount") > 0)
invalid_df = source_df.filter(col("amount") <= 0)

# Approach 2: Add routing column
routed_df = source_df.withColumn(
    "route",
    when(col("amount") > 1000, "high_value")
    .when(col("amount") > 100, "medium_value")
    .otherwise("low_value")
)
```

#### Snowflake
```sql
-- Approach 1: Multiple INSERTs with WHERE
INSERT INTO high_value_sales
SELECT * FROM staging WHERE amount > 1000;

INSERT INTO medium_value_sales
SELECT * FROM staging WHERE amount BETWEEN 100 AND 1000;

-- Approach 2: CASE WHEN in single query
INSERT INTO categorized_sales
SELECT 
    *,
    CASE 
        WHEN amount > 1000 THEN 'high_value'
        WHEN amount > 100 THEN 'medium_value'
        ELSE 'low_value'
    END AS category
FROM staging;
```

### 5. Aggregate Transform

#### SSIS Approach
- Aggregate component
- Group by dimensions
- Apply aggregate functions (SUM, COUNT, AVG)

#### Databricks
```python
from pyspark.sql.functions import sum, count, avg, max, min

aggregated_df = (source_df
    .groupBy("customer_id", "transaction_date")
    .agg(
        sum("amount").alias("total_sales"),
        count("*").alias("transaction_count"),
        avg("amount").alias("avg_transaction"),
        max("amount").alias("max_transaction"),
        min("amount").alias("min_transaction")
    )
)
```

#### Snowflake
```sql
SELECT 
    customer_id,
    transaction_date,
    SUM(amount) AS total_sales,
    COUNT(*) AS transaction_count,
    AVG(amount) AS avg_transaction,
    MAX(amount) AS max_transaction,
    MIN(amount) AS min_transaction
FROM source_table
GROUP BY 1, 2;
```

---

## Variable Handling

### SSIS Variables (Project/Package)
```
Package::FilePath = "C:\\Data\\input.csv"
Project::EnvironmentName = "Production"
```

### Databricks Equivalent
```python
# Option 1: Widgets (notebook parameters)
dbutils.widgets.text("file_path", "/mnt/data/input.csv")
file_path = dbutils.widgets.get("file_path")

# Option 2: Job parameters (passed at runtime)
# Accessed via spark.conf or sys.argv

# Option 3: Spark Config
spark.conf.set("app.environment", "production")
environment = spark.conf.get("app.environment")
```

### Snowflake Equivalent
```sql
-- Session variables
SET file_path = 's3://bucket/data/input.csv';
SET environment = 'production';

-- Use in queries
COPY INTO target_table
FROM $file_path
FILE_FORMAT = (TYPE = 'CSV');
```

---

## Error Handling

### SSIS Error Outputs
- Redirect rows on error
- Log error details
- Continue processing

### Databricks Equivalent
```python
from pyspark.sql.functions import col, when, lit

# Add error handling column
processed_df = source_df.withColumn(
    "is_valid",
    when(col("amount").isNotNull() & (col("amount") > 0), True)
    .otherwise(False)
)

# Write valid records to target
processed_df.filter("is_valid = true").write.saveAsTable("target_table")

# Write invalid records to quarantine
processed_df.filter("is_valid = false") \
    .withColumn("error_reason", lit("Invalid amount")) \
    .withColumn("error_timestamp", current_timestamp()) \
    .write.mode("append").saveAsTable("quarantine_table")
```

### Snowflake Equivalent
```sql
-- COPY INTO with error handling
COPY INTO target_table
FROM @my_stage/data/
FILE_FORMAT = (TYPE = 'CSV')
ON_ERROR = 'CONTINUE'  -- Skip bad records
VALIDATION_MODE = 'RETURN_ERRORS';  -- Show errors

-- Query errors
SELECT * FROM TABLE(VALIDATE(target_table, JOB_ID => '_last'));
```

---

## Performance Optimization

### SSIS Buffer Tuning
SSIS uses in-memory buffers (DefaultBufferSize, DefaultBufferMaxRows).

### Modern Equivalent

**Databricks**:
- Partition data appropriately: `.repartition(100)` or `.coalesce(10)`
- Broadcast small tables: `broadcast(dim_table)`
- Persist intermediate results: `.cache()` (for reused DataFrames only)

**Snowflake**:
- Right-size warehouse (SMALL, MEDIUM, LARGE)
- Use CLUSTER BY on large filtered tables
- Materialized views for frequent aggregations

---

## Testing Strategy

### Unit Testing SSIS → Modern

| SSIS Test | Modern Equivalent |
|-----------|------------------|
| Data Viewer (breakpoint) | `.show()` or `.display()` in notebook |
| Row Count validation | `df.count()` or `SELECT COUNT(*) FROM...` |
| Data profiling | `df.describe()` or Snowflake `DESCRIBE TABLE` |
| Execute with sample data | Filter to subset: `.limit(1000)` or `LIMIT 1000` |

---

## Migration Checklist

When translating SSIS packages:
- [ ] Identify all Data Flow Tasks (core transformations)
- [ ] Map each SSIS component to modern equivalent
- [ ] Extract variables → Convert to parameters/config
- [ ] Identify error handling → Implement quarantine tables
- [ ] Detect SCD patterns → Use MERGE with proper logic
- [ ] Check for performance bottlenecks → Apply optimization (clustering, partitioning)
- [ ] Validate idempotency → Ensure all loads use MERGE (not INSERT/APPEND)
- [ ] Test with sample data → Verify output matches SSIS
- [ ] Document dependencies → Ensure execution order preserved

---

## Common Pitfalls

### ❌ SSIS ForEach Loop → Don't replicate in modern platforms
```python
# BAD: Loop over files individually (slow)
for file in file_list:
    df = spark.read.csv(file)
    process(df)

# GOOD: Read all files at once (parallelized)
df = spark.read.csv("s3://bucket/data/*.csv")
process(df)
```

### ❌ SSIS Recordset Destination → Use proper sink
Modern platforms don't have "recordsets". Write to:
- Delta tables (Databricks)
- Snowflake tables
- Parquet files (for staging)

### ❌ Row-by-Row Processing
SSIS sometimes processes row-by-row (Script Component loops).

**Modern approach**: Always use set-based operations (DataFrames, SQL).

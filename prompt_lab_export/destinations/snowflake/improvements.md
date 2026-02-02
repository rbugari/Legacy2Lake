# Snowflake SQL Best Practices (v3.5)

> **Last Updated**: 2026-02-01  
> **Source**: 2024 Snowflake optimization and performance research

## Clustering vs Partitioning

**CRITICAL**: Snowflake uses **automatic micro-partitioning** (50-500MB), NOT manual `PARTITION BY`.

Use **CLUSTER BY** to organize data within micro-partitions for better pruning.

### Automatic Micro-Partitioning

Snowflake automatically divides tables into immutable, compressed micro-partitions:
- **Size**: 50MB - 500MB uncompressed
- **Metadata**: Stores min/max values for each column
- **Pruning**: Query optimizer skips irrelevant micro-partitions automatically

**No manual intervention needed** for basic partitioning.

### Clustering Keys (Explicit Optimization)

Use clustering for large tables (> 1TB) with frequent filtering:

```sql
-- Define clustering keys (3-4 columns maximum)
ALTER TABLE database.schema.sales_fact
CLUSTER BY (transaction_date, customer_id, region);
```

**Column Selection Rules**:
- ✅ Frequently filtered columns (WHERE, JOIN, GROUP BY)
- ✅ Medium to high cardinality
- ✅ Even distribution of values
- ❌ Extremely high cardinality (UUID, timestamps to seconds)
- ❌ Extremely low cardinality (boolean, status flags)

**Column Ordering**:
- Order from **lowest** to **highest** cardinality
- Example: `CLUSTER BY (region, customer_id, order_id)` ✅
- Not: `CLUSTER BY (order_id, customer_id, region)` ❌

**Automatic Clustering (2024 Improvements)**:
- Snowflake automatically maintains clustering in the background
- Significant performance and cost efficiency improvements in 2024
- Monitor clustering depth: `SYSTEM$CLUSTERING_INFORMATION('table_name')`

---

## Query Optimization

### Selective Column Retrieval

**Always specify columns** instead of `SELECT *`:

```sql
-- ✅ GOOD: Selective columns
SELECT customer_id, order_amount, transaction_date
FROM sales
WHERE transaction_date >= CURRENT_DATE - 30;

-- ❌ BAD: SELECT *
SELECT * FROM sales WHERE region = 'US';
```

**Impact**: Reduces data scanning, improves performance, lowers costs.

### Optimized WHERE Clauses

Filter early to reduce micro-partitions scanned:

```sql
-- ✅ GOOD: Filter on clustered column
SELECT * FROM sales
WHERE transaction_date BETWEEN '2024-01-01' AND '2024-01-31'
  AND region = 'US';

-- ❌ BAD: Complex function in WHERE (prevents pruning)
SELECT * FROM sales
WHERE DATE_TRUNC('MONTH', transaction_date) = '2024-01-01';

-- ✅ BETTER: Use range filter instead
SELECT * FROM sales
WHERE transaction_date >= '2024-01-01' 
  AND transaction_date < '2024-02-01';
```

**Rules**:
- Equality filters (`=`) perform best
- Avoid UDFs and complex functions in WHERE
- Use frequently filtered columns in CLUSTER BY

### Efficient JOIN Operations

```sql
-- ✅ GOOD: INNER JOIN with matching data types
SELECT f.*, d.customer_name
FROM fact_sales f
INNER JOIN dim_customer d
    ON f.customer_id = d.customer_id  -- Same data type
WHERE f.transaction_date >= CURRENT_DATE - 30;

-- ❌ BAD: Implicit type conversion
ON f.customer_id::VARCHAR = d.customer_id::NUMBER  -- Slow!

-- ❌ BAD: OR conditions in join
ON (f.customer_id = d.id OR f.alternate_id = d.id)
```

**Best Practices**:
- Use `INNER JOIN` when possible (faster than `OUTER JOIN`)
- Join on matching data types (avoid conversions)
- Filter datasets before joining
- Avoid OR conditions in JOIN predicates

### Window Functions Over Self-Joins

```sql
-- ✅ GOOD: Window function
SELECT 
    customer_id,
    order_date,
    amount,
    SUM(amount) OVER (PARTITION BY customer_id ORDER BY order_date) AS running_total
FROM orders;

-- ❌ BAD: Self-join for running total
SELECT 
    o1.customer_id,
    o1.order_date,
    SUM(o2.amount) AS running_total
FROM orders o1
JOIN orders o2 
    ON o1.customer_id = o2.customer_id 
    AND o2.order_date <= o1.order_date
GROUP BY o1.customer_id, o1.order_date;
```

**Impact**: Window functions are optimized internally, self-joins create unnecessary shuffles.

---

## Materialized Views

Use for frequently executed aggregations:

```sql
CREATE MATERIALIZED VIEW sales_monthly AS
SELECT 
    DATE_TRUNC('MONTH', transaction_date) AS month,
    region,
    SUM(amount) AS total_sales,
    COUNT(*) AS transaction_count,
    AVG(amount) AS avg_transaction
FROM sales
GROUP BY 1, 2;
```

**Benefits**:
- Stores precomputed results
- Auto-refreshes (Snowflake Enterprise+)
- Reduces query cost for repeated aggregations

**When to use**:
- Complex aggregations run frequently (daily reports)
- JOIN-heavy queries with static dimension data
- Dashboard queries

---

## Idempotent Operations (MERGE)

**Always use MERGE** for data loading to ensure idempotency:

```sql
MERGE INTO target_table AS t
USING source_table AS s
ON t.unique_id = s.unique_id
WHEN MATCHED THEN
    UPDATE SET 
        t.value = s.value,
        t.updated_at = CURRENT_TIMESTAMP
WHEN NOT MATCHED THEN
    INSERT (unique_id, value, created_at)
    VALUES (s.unique_id, s.value, CURRENT_TIMESTAMP);
```

### Slowly Changing Dimension (SCD Type 2)

```sql
-- Step 1: Expire old versions
UPDATE dim_customer AS t
SET 
    is_current = FALSE,
    end_date = CURRENT_TIMESTAMP
FROM staging_customer AS s
WHERE t.customer_id = s.customer_id
  AND t.is_current = TRUE
  AND (t.name != s.name OR t.email != s.email);  -- Detect changes

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
WHERE t.customer_id IS NULL  -- New records
   OR t.name != s.name OR t.email != s.email;  -- Changed records
```

---

## Warehouse Management

Right-size warehouses for workload:

```sql
-- ETL Warehouse (large, auto-suspend)
CREATE WAREHOUSE etl_wh WITH
    WAREHOUSE_SIZE = 'LARGE'
    AUTO_SUSPEND = 60  -- Seconds of inactivity
    AUTO_RESUME = TRUE;

-- BI/Reporting Warehouse (medium, faster suspend)
CREATE WAREHOUSE reporting_wh WITH
    WAREHOUSE_SIZE = 'MEDIUM'
    AUTO_SUSPEND = 300
    AUTO_RESUME = TRUE;
```

**Best Practices**:
- Separate warehouses for ETL vs reporting
- Auto-suspend for cost control
- Scale up for performance, scale out for concurrency
- Monitor warehouse usage: `WAREHOUSE_METERING_HISTORY`

---

## Data Loading Best Practices

### COPY INTO (Bulk Loading)

```sql
-- Load from S3 with error handling
COPY INTO database.schema.target_table
FROM @my_s3_stage/path/to/files/
FILE_FORMAT = (TYPE = 'PARQUET')
ON_ERROR = 'CONTINUE'  -- Skip bad files, continue loading
FORCE = FALSE;  -- Skip already loaded files
```

**Error Handling Options**:
- `ON_ERROR = 'CONTINUE'`: Skip bad records, log errors
- `ON_ERROR = 'SKIP_FILE'`: Skip entire file on first error
- `ON_ERROR = 'ABORT_STATEMENT'`: Stop on first error (default)

### Incremental Loading

```sql
-- Track last watermark
CREATE TABLE IF NOT EXISTS watermark (
    table_name VARCHAR,
    last_loaded_timestamp TIMESTAMP_NTZ
);

-- Load only new records
INSERT INTO target_table
SELECT *
FROM source_table
WHERE modified_date > (
    SELECT COALESCE(MAX(last_loaded_timestamp), '1900-01-01')
    FROM watermark
    WHERE table_name = 'target_table'
);

-- Update watermark
MERGE INTO watermark w
USING (SELECT 'target_table' AS table_name, CURRENT_TIMESTAMP AS ts) s
ON w.table_name = s.table_name
WHEN MATCHED THEN UPDATE SET last_loaded_timestamp = s.ts
WHEN NOT MATCHED THEN INSERT (table_name, last_loaded_timestamp) VALUES (s.table_name, s.ts);
```

---

## Caching Strategy

Snowflake has three layers of caching:

1. **Result Cache** (24 hours):
   - Caches exact query results
   - Shared across users
   - Invalidated on data changes

2. **Metadata Cache**:
   - Stores table metadata, statistics
   - Enables micro-partition pruning

3. **Virtual Warehouse Cache**:
   - Local SSD cache of data blocks
   - Persists while warehouse is active
   - Lost on suspend

**Best Practice**: Use consistent warehouses for similar queries to maximize cache hits.

---

## Performance Checklist

When generating Snowflake SQL, ensure:
- [ ] No `SELECT *` (specify columns)
- [ ] Early filtering with optimized WHERE clauses
- [ ] CLUSTER BY on large tables (> 1TB) with frequent filters
- [ ] INNER JOIN preferred over OUTER JOIN
- [ ] No complex functions/UDFs in WHERE (breaks pruning)
- [ ] Window functions instead of self-joins
- [ ] MERGE for idempotent loads (not INSERT)
- [ ] Materialized views for frequent aggregations
- [ ] Appropriate warehouse size (separate ETL/reporting)
- [ ] Auto-suspend enabled on warehouses

---

## Code Generation Templates

### Bronze Layer (Raw Ingestion)

```sql
-- Create stage for S3/Azure
CREATE OR REPLACE STAGE bronze.raw_stage
URL = 's3://bucket/path/'
CREDENTIALS = (AWS_KEY_ID='xxx' AWS_SECRET_KEY='xxx');

-- Load raw data
COPY INTO bronze.raw_events
FROM @bronze.raw_stage
FILE_FORMAT = (TYPE = 'PARQUET')
ON_ERROR = 'CONTINUE';
```

### Silver Layer (Cleaned/Conformed)

```sql
-- MERGE for idempotent processing
MERGE INTO silver.events AS t
USING (
    SELECT 
        event_id,
        LOWER(TRIM(email)) AS email,
        TO_TIMESTAMP(event_timestamp) AS event_ts,
        -- Clean and conform
        CASE 
            WHEN event_type IN ('CLICK', 'VIEW') THEN event_type
            ELSE 'OTHER'
        END AS event_type_clean
    FROM bronze.raw_events
    WHERE event_id IS NOT NULL
    QUALIFY ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY ingestion_time DESC) = 1  -- Dedup
) AS s
ON t.event_id = s.event_id
WHEN MATCHED THEN
    UPDATE SET 
        t.email = s.email,
        t.event_ts = s.event_ts,
        t.updated_at = CURRENT_TIMESTAMP
WHEN NOT MATCHED THEN
    INSERT (event_id, email, event_ts, event_type, created_at)
    VALUES (s.event_id, s.email, s.event_ts, s.event_type_clean, CURRENT_TIMESTAMP);
```

### Gold Layer (Business Aggregates)

```sql
-- Create aggregated reporting table
CREATE OR REPLACE TABLE gold.customer_daily_sales AS
SELECT 
    customer_id,
    transaction_date,
    SUM(amount) AS total_sales,
    COUNT(*) AS transaction_count,
    AVG(amount) AS avg_transaction_size
FROM silver.sales
GROUP BY 1, 2;

-- Cluster for query performance
ALTER TABLE gold.customer_daily_sales
CLUSTER BY (transaction_date, customer_id);

-- Optional: Create materialized view for real-time aggregates
CREATE MATERIALIZED VIEW gold.customer_monthly_mv AS
SELECT 
    customer_id,
    DATE_TRUNC('MONTH', transaction_date) AS month,
    SUM(total_sales) AS monthly_total
FROM gold.customer_daily_sales
GROUP BY 1, 2;
```

---

## Common Anti-Patterns to Avoid

### ❌ Manual Partitioning
```sql
-- WRONG: Snowflake does NOT support manual PARTITION BY
CREATE TABLE sales (
    id NUMBER,
    date DATE
) PARTITION BY (date);  -- ❌ Syntax error!
```

### ❌ Using UNION instead of UNION ALL
```sql
-- SLOW: UNION deduplicates (expensive sort)
SELECT * FROM table1
UNION
SELECT * FROM table2;

-- FAST: UNION ALL (no deduplication)
SELECT * FROM table1
UNION ALL
SELECT * FROM table2;
```

### ❌ ORDER BY in Subqueries/CTEs
```sql
-- WASTEFUL: ORDER BY in CTE (discarded)
WITH sorted_data AS (
    SELECT * FROM sales ORDER BY date  -- ❌ Wasted effort
)
SELECT * FROM sorted_data WHERE region = 'US';

-- CORRECT: ORDER BY only in final SELECT
SELECT * FROM sales 
WHERE region = 'US'
ORDER BY date;  -- ✅ Only when needed
```

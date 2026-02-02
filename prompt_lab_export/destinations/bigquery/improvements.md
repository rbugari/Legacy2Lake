# Google BigQuery Best Practices (v3.5)

> **Last Updated**: 2026-02-01  
> **Source**: Google Cloud BigQuery optimization patterns

## Partitioning and Clustering

### Partitioning (Date-Based Pattern)

BigQuery excels at partitioned tables for time-series data:

```sql
-- Create partitioned table (by ingestion time)
CREATE TABLE dataset.events
PARTITION BY DATE(_PARTITIONTIME)
AS SELECT * FROM source_table;

-- Or partition by explicit column
CREATE TABLE dataset.sales
PARTITION BY DATE(transaction_date)
AS SELECT * FROM source_data;

-- Range partitioning (for non-date columns)
CREATE TABLE dataset.customers
PARTITION BY RANGE_BUCKET(customer_id, GENERATE_ARRAY(0, 100000, 1000))
AS SELECT * FROM source;
```

**Best Practices**:
- Partition on **date/timestamp** columns for time-series data
- Use `_PARTITIONTIME` for ingestion-time partitioning
- Limit: 40,000 partitions per table
- Always filter on partition column to reduce costs

### Clustering (Multi-Column Ordering)

Cluster tables to improve query performance on frequently filtered columns:

```sql
CREATE TABLE dataset.events
PARTITION BY DATE(event_date)
CLUSTER BY user_id, event_type
AS SELECT * FROM source_table;
```

**Column Selection Rules**:
- Maximum 4 clustering columns
- Order by cardinality: high → low (opposite of Snowflake!)
- Use for columns in `WHERE`, `JOIN`, `GROUP BY`

**Benefits**:
- Automatic data organization (no manual OPTIMIZE needed)
- Reduced data scanning → lower costs
- Better with partitioning for dual optimization

---

## Query Optimization

### Avoid SELECT *
```sql
-- ❌ BAD: Scans all columns (expensive!)
SELECT * FROM `project.dataset.large_table`
WHERE date = '2024-01-01';

-- ✅ GOOD: Select only needed columns
SELECT user_id, event_type, timestamp
FROM `project.dataset.large_table`
WHERE date = '2024-01-01';
```

### Filter Early (Partition Pruning)
```sql
-- ✅ GOOD: Filter on partition column
SELECT *
FROM `project.dataset.events`
WHERE DATE(event_timestamp) BETWEEN '2024-01-01' AND '2024-01-31'
  AND event_type = 'purchase';

-- ❌ BAD: No partition filter (scans entire table!)
SELECT *
FROM `project.dataset.events`
WHERE event_type = 'purchase';
```

### Use Approximate Aggregates
```sql
-- ✅ FAST: Approximate count distinct (±1% accuracy)
SELECT APPROX_COUNT_DISTINCT(user_id) AS unique_users
FROM `project.dataset.events`;

-- ❌ SLOW: Exact count distinct (expensive for large datasets)
SELECT COUNT(DISTINCT user_id) AS unique_users
FROM `project.dataset.events`;
```

### Denormalize for Performance
BigQuery is columnar → denormalization is often better than joins:

```sql
-- ✅ GOOD: Denormalized table (pre-joined)
CREATE TABLE dataset.sales_denormalized AS
SELECT 
    s.*,
    c.customer_name,
    c.customer_segment,
    p.product_name,
    p.product_category
FROM sales s
JOIN customers c ON s.customer_id = c.customer_id
JOIN products p ON s.product_id = p.product_id;

-- Query is simple and fast
SELECT product_category, SUM(amount)
FROM dataset.sales_denormalized
GROUP BY 1;
```

---

## DML Operations (INSERT, UPDATE, DELETE)

### MERGE for Idempotency
```sql
MERGE `project.dataset.target_table` T
USING `project.dataset.source_table` S
ON T.id = S.id
WHEN MATCHED THEN
    UPDATE SET 
        T.value = S.value,
        T.updated_at = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN
    INSERT (id, value, created_at)
    VALUES (S.id, S.value, CURRENT_TIMESTAMP());
```

### Avoid Small, Frequent DML Operations
BigQuery is optimized for batch operations:

```sql
-- ❌ BAD: Many small INSERTs (slow, expensive)
FOR record IN records:
    INSERT INTO table VALUES (record);

-- ✅ GOOD: Single batch INSERT
INSERT INTO `project.dataset.table`
SELECT * FROM `project.dataset.staging_table`;
```

**Best Practices**:
- Batch DML operations (hourly/daily, not per-row)
- Use streaming inserts for real-time (<1,000 rows/sec)
- Limit DELETE/UPDATE to specific partitions

---

## Cost Optimization

### Use Materialized Views
```sql
CREATE MATERIALIZED VIEW dataset.sales_summary AS
SELECT 
    DATE(transaction_date) AS date,
    product_category,
    SUM(amount) AS total_sales
FROM dataset.sales
GROUP BY 1, 2;
```

**Benefits**:
- Auto-refreshed incrementally
- Queries against MV read precomputed results
- Significantly lower costs for frequent queries

### Partition Expiration (Auto-Cleanup)
```sql
-- Automatically delete partitions older than 90 days
ALTER TABLE dataset.events
SET OPTIONS (
    partition_expiration_days = 90
);
```

### Query Cost Estimation
```sql
-- Dry run to estimate cost (no data processed)
SELECT *
FROM `project.dataset.large_table`
WHERE date = '2024-01-01';
-- Check "Estimated bytes processed" in query details
```

---

## Data Loading

### Batch Loading (Preferred)
```sql
-- Load from Cloud Storage
LOAD DATA INTO dataset.target_table
FROM FILES (
    format = 'PARQUET',
    uris = ['gs://bucket/path/*.parquet']
);

-- Or using SQL
CREATE OR REPLACE TABLE dataset.target_table AS
SELECT * FROM EXTERNAL_QUERY(
    "projects/my-project/locations/us/connections/my-connection",
    "SELECT * FROM source_table"
);
```

### Streaming Inserts (Real-Time)
Use BigQuery Streaming API for real-time data (<1,000 rows/sec):
- Best for event tracking, IoT data
- Higher cost than batch loading
- Data available immediately

---

## Code Generation Templates

### Bronze Layer (Raw Ingestion)
```sql
-- Create partitioned raw table
CREATE TABLE bronze.raw_events
PARTITION BY DATE(ingestion_timestamp)
CLUSTER BY event_type, user_id
AS SELECT 
    *,
    CURRENT_TIMESTAMP() AS ingestion_timestamp
FROM `source_project.source_dataset.events`;
```

### Silver Layer (Cleaned)
```sql
-- MERGE for idempotent processing
MERGE bronze.cleaned_events T
USING (
    SELECT 
        event_id,
        LOWER(TRIM(email)) AS email,
        TIMESTAMP(event_time) AS event_timestamp,
        event_type,
        ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY ingestion_timestamp DESC) AS rn
    FROM bronze.raw_events
    WHERE event_id IS NOT NULL
    QUALIFY rn = 1  -- Dedup
) S
ON T.event_id = S.event_id
WHEN MATCHED THEN
    UPDATE SET 
        T.email = S.email,
        T.event_timestamp = S.event_timestamp
WHEN NOT MATCHED THEN
    INSERT (event_id, email, event_timestamp, event_type)
    VALUES (S.event_id, S.email, S.event_timestamp, S.event_type);
```

### Gold Layer (Aggregates)
```sql
-- Create materialized view for fast aggregates
CREATE MATERIALIZED VIEW gold.daily_sales_summary AS
SELECT 
    DATE(transaction_timestamp) AS date,
    customer_segment,
    product_category,
    SUM(amount) AS total_sales,
    COUNT(*) AS transaction_count,
    AVG(amount) AS avg_transaction
FROM silver.sales
GROUP BY 1, 2, 3;
```

---

## Performance Checklist

- [ ] Partition tables by date/timestamp
- [ ] Cluster on frequently filtered columns (max 4)
- [ ] Always filter on partition column
- [ ] SELECT specific columns (never `*`)
- [ ] Use APPROX functions for estimates
- [ ] Denormalize for query performance
- [ ] Batch DML operations (avoid row-by-row)
- [ ] MERGE for idempotent loads
- [ ] Set partition expiration for cleanup
- [ ] Use materialized views for frequent queries
- [ ] Dry run queries to estimate costs

---

## Common Anti-Patterns

### ❌ Self-Join for Running Total
```sql
-- BAD: Expensive self-join
SELECT 
    a.date,
    SUM(b.amount) AS running_total
FROM sales a
JOIN sales b ON b.date <= a.date
GROUP BY a.date;

-- GOOD: Window function
SELECT 
    date,
    SUM(amount) OVER (ORDER BY date 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total
FROM sales;
```

### ❌ NOT IN with NULLs
```sql
-- BAD: Can return unexpected results if subquery has NULLs
SELECT * FROM table1
WHERE id NOT IN (SELECT id FROM table2);

-- GOOD: Use NOT EXISTS or LEFT JOIN
SELECT t1.*
FROM table1 t1
LEFT JOIN table2 t2 ON t1.id = t2.id
WHERE t2.id IS NULL;
```

### ❌ Unpartitioned Large Tables
```sql
-- BAD: Scans entire table every time
SELECT * FROM huge_events_table
WHERE date = '2024-01-01';  -- Still scans all data!

-- GOOD: Partitioned table
CREATE TABLE huge_events_table
PARTITION BY DATE(event_date)
AS SELECT * FROM source;

-- Query only scans 1 day's partition
SELECT * FROM huge_events_table
WHERE DATE(event_date) = '2024-01-01';  -- Efficient!
```

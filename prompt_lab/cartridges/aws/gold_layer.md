---
tech_id: aws
layer: gold
version: 2.0.0
status: active
maintainer: UTM Core Team
created: 2025-02-10
updated: 2025-02-12
---

# 🏆 AWS Gold Layer - Business Analytics & QuickSight Integration

## 🤖 Agent Instructions

You are an expert **AWS Analytics Engineer** specializing in **Redshift**, **AWS Glue**, **QuickSight**, and **dimensional modeling**. Your task is to generate production-ready **Gold layer** code that creates **business-ready analytics tables** optimized for **AWS QuickSight dashboards** and **Athena ad-hoc queries**.

**Your code must:**
- Read from **S3 Silver layer** or **Redshift Silver tables**
- Implement **dimensional modeling** (Star Schema: FACT tables + DIMENSION tables)
- Create **aggregated views** for QuickSight (pre-calculated metrics)
- Store in **Redshift** (for BI tools) or **S3 Gold Parquet** (for Athena)
- Use **Redshift distribution keys** (DISTKEY) and **sort keys** (SORTKEY) for optimization
- Add **Gold audit columns**: `_gold_created_at`, `_grain_level`, `_last_updated`
- Support **incremental aggregations** for large fact tables
- Include **QuickSight dataset definitions** (JSON format) for auto-deployment

Generate **complete SQL for Redshift** or **PySpark for Glue** depending on the target.

---

## 📐 Mandatory Code Structure (Redshift SQL)

```sql
-- AWS Redshift Gold Layer - Dimensional Model
-- Target: Redshift Schema "gold"
-- BI Tool: AWS QuickSight

-- DIMENSION TABLE: dim_customers
DROP TABLE IF EXISTS gold.dim_customers;

CREATE TABLE gold.dim_customers (
    customer_key        BIGINT IDENTITY(1,1) PRIMARY KEY,
    customer_id         VARCHAR(50) NOT NULL,
    customer_name       VARCHAR(255),
    customer_email      VARCHAR(255),
    customer_segment    VARCHAR(50),
    customer_tier       VARCHAR(20),
    country             VARCHAR(100),
    _gold_created_at    TIMESTAMP DEFAULT GETDATE(),
    _grain_level        VARCHAR(50) DEFAULT 'customer',
    _last_updated       TIMESTAMP DEFAULT GETDATE()
)
DISTKEY(customer_id)
SORTKEY(customer_id);

INSERT INTO gold.dim_customers (
    customer_id, customer_name, customer_email, customer_segment, customer_tier, country
)
SELECT DISTINCT
    customer_id,
    customer_name,
    customer_email,
    customer_segment,
    CASE 
        WHEN total_lifetime_value > 10000 THEN 'Gold'
        WHEN total_lifetime_value > 5000 THEN 'Silver'
        ELSE 'Bronze'
    END AS customer_tier,
    country
FROM silver.customers;

-- FACT TABLE: fact_orders
DROP TABLE IF EXISTS gold.fact_orders;

CREATE TABLE gold.fact_orders (
    order_key           BIGINT IDENTITY(1,1) PRIMARY KEY,
    order_id            VARCHAR(50) NOT NULL,
    customer_key        BIGINT REFERENCES gold.dim_customers(customer_key),
    order_date          DATE NOT NULL,
    order_amount        DECIMAL(18,2),
    quantity            INTEGER,
    discount_amount     DECIMAL(18,2),
    tax_amount          DECIMAL(18,2),
    net_amount          DECIMAL(18,2),
    _gold_created_at    TIMESTAMP DEFAULT GETDATE(),
    _grain_level        VARCHAR(50) DEFAULT 'order',
    _last_updated       TIMESTAMP DEFAULT GETDATE()
)
DISTKEY(customer_key)
SORTKEY(order_date);

INSERT INTO gold.fact_orders (
    order_id, customer_key, order_date, order_amount, quantity, discount_amount, tax_amount, net_amount
)
SELECT 
    o.order_id,
    c.customer_key,
    o.order_date,
    o.amount AS order_amount,
    o.quantity,
    o.discount AS discount_amount,
    o.tax AS tax_amount,
    (o.amount - o.discount + o.tax) AS net_amount
FROM silver.orders o
INNER JOIN gold.dim_customers c ON o.customer_id = c.customer_id;

-- AGGREGATE VIEW: Daily Sales Summary for QuickSight
DROP VIEW IF EXISTS gold.vw_daily_sales;

CREATE VIEW gold.vw_daily_sales AS
SELECT 
    f.order_date,
    d.customer_segment,
    d.country,
    COUNT(DISTINCT f.order_id) AS total_orders,
    SUM(f.order_amount) AS gross_sales,
    SUM(f.discount_amount) AS total_discounts,
    SUM(f.net_amount) AS net_sales,
    AVG(f.net_amount) AS avg_order_value
FROM gold.fact_orders f
INNER JOIN gold.dim_customers d ON f.customer_key = d.customer_key
GROUP BY 1, 2, 3;

COMMIT;
```

---

## ⚙️ Mandatory Requirements

**✅ Dimensional Modeling Requirements:**
- [ ] Create **DIMENSION tables** (dim_*) for reference entities (customers, products, dates)
- [ ] Create **FACT tables** (fact_*) for transactional/measurable events (orders, payments)
- [ ] Use **surrogate keys** (customer_key, product_key) with IDENTITY(1,1)
- [ ] Implement **foreign key relationships** between FACT and DIMENSION

**✅ Redshift Optimization Requirements:**
- [ ] Use **DISTKEY** on dimension keys for co-located JOINs
- [ ] Use **SORTKEY** on date columns for time-series queries
- [ ] Create **aggregate views** for QuickSight pre-computation
- [ ] Use **VACUUM** and **ANALYZE** commands after large loads

**✅ Gold Audit Columns:**
- [ ] `_gold_created_at` (TIMESTAMP) → When Gold record was created
- [ ] `_grain_level` (VARCHAR) → Granularity level (e.g., "order", "customer", "daily")
- [ ] `_last_updated` (TIMESTAMP) → Last update time (for incremental refresh)

**✅ QuickSight Integration:**
- [ ] Create **materialized views** or tables (not complex queries) for QuickSight datasets
- [ ] Use **consistent naming** (dim_*, fact_*, vw_*) for easy discovery
- [ ] Include **calculated metrics** (net_sales, avg_order_value) in views
- [ ] Provide **QuickSight dataset JSON** definitions for auto-deployment

---

## 🔍 Validation Checklist

Before submitting Gold code, verify:

- [ ] **Dimensional Model**: Star Schema with FACT and DIMENSION tables
- [ ] **Surrogate Keys**: Using IDENTITY(1,1) for dimension keys
- [ ] **Foreign Keys**: Proper REFERENCES between FACT and DIMENSION
- [ ] **DISTKEY/SORTKEY**: Applied for Redshift query optimization
- [ ] **Aggregate Views**: Pre-calculated metrics for QuickSight
- [ ] **Audit Columns**: Gold tracking columns included
- [ ] **Naming Convention**: dim_*, fact_*, vw_* prefixes
- [ ] **QuickSight Compatibility**: Simple queries without complex CTEs
- [ ] **Data Validation**: Check row counts and metric totals

---

## 📚 Examples

### Example 1: Star Schema - Orders (Redshift SQL)

```sql
-- AWS Redshift Gold Layer - Orders Star Schema

-- DIMENSION: Products
DROP TABLE IF EXISTS gold.dim_products CASCADE;

CREATE TABLE gold.dim_products (
    product_key         BIGINT IDENTITY(1,1) PRIMARY KEY,
    product_id          VARCHAR(50) NOT NULL,
    product_name        VARCHAR(255),
    category            VARCHAR(100),
    subcategory         VARCHAR(100),
    unit_price          DECIMAL(18,2),
    _gold_created_at    TIMESTAMP DEFAULT GETDATE(),
    _grain_level        VARCHAR(50) DEFAULT 'product',
    _last_updated       TIMESTAMP DEFAULT GETDATE()
)
DISTKEY(product_id)
SORTKEY(category, subcategory);

INSERT INTO gold.dim_products (product_id, product_name, category, subcategory, unit_price)
SELECT DISTINCT
    product_id,
    product_name,
    category,
    subcategory,
    unit_price
FROM silver.products;

-- DIMENSION: Date (for time intelligence)
DROP TABLE IF EXISTS gold.dim_date CASCADE;

CREATE TABLE gold.dim_date (
    date_key            INTEGER PRIMARY KEY,  -- YYYYMMDD format
    date                DATE NOT NULL,
    year                INTEGER,
    quarter             INTEGER,
    month               INTEGER,
    month_name          VARCHAR(20),
    week                INTEGER,
    day_of_week         INTEGER,
    day_name            VARCHAR(20),
    is_weekend          BOOLEAN,
    _gold_created_at    TIMESTAMP DEFAULT GETDATE()
)
SORTKEY(date);

-- Populate date dimension (2020-2030)
INSERT INTO gold.dim_date
SELECT 
    TO_CHAR(d, 'YYYYMMDD')::INTEGER AS date_key,
    d AS date,
    EXTRACT(YEAR FROM d) AS year,
    EXTRACT(QUARTER FROM d) AS quarter,
    EXTRACT(MONTH FROM d) AS month,
    TO_CHAR(d, 'Month') AS month_name,
    EXTRACT(WEEK FROM d) AS week,
    EXTRACT(DOW FROM d) AS day_of_week,
    TO_CHAR(d, 'Day') AS day_name,
    CASE WHEN EXTRACT(DOW FROM d) IN (0, 6) THEN TRUE ELSE FALSE END AS is_weekend,
    GETDATE() AS _gold_created_at
FROM (
    SELECT '2020-01-01'::DATE + GENERATE_SERIES AS d
    FROM GENERATE_SERIES(0, 3650)
) dates;

-- FACT: Order Line Items (grain: product per order)
DROP TABLE IF EXISTS gold.fact_order_items;

CREATE TABLE gold.fact_order_items (
    order_item_key      BIGINT IDENTITY(1,1) PRIMARY KEY,
    order_id            VARCHAR(50) NOT NULL,
    customer_key        BIGINT REFERENCES gold.dim_customers(customer_key),
    product_key         BIGINT REFERENCES gold.dim_products(product_key),
    date_key            INTEGER REFERENCES gold.dim_date(date_key),
    quantity            INTEGER,
    unit_price          DECIMAL(18,2),
    discount_percent    DECIMAL(5,2),
    tax_rate            DECIMAL(5,2),
    line_total          DECIMAL(18,2),
    _gold_created_at    TIMESTAMP DEFAULT GETDATE(),
    _grain_level        VARCHAR(50) DEFAULT 'order_item'
)
DISTKEY(customer_key)
SORTKEY(date_key);

INSERT INTO gold.fact_order_items (
    order_id, customer_key, product_key, date_key, quantity, unit_price, discount_percent, tax_rate, line_total
)
SELECT 
    oi.order_id,
    c.customer_key,
    p.product_key,
    TO_CHAR(o.order_date, 'YYYYMMDD')::INTEGER AS date_key,
    oi.quantity,
    oi.unit_price,
    oi.discount_percent,
    oi.tax_rate,
    (oi.quantity * oi.unit_price * (1 - oi.discount_percent/100) * (1 + oi.tax_rate/100)) AS line_total
FROM silver.order_items oi
INNER JOIN silver.orders o ON oi.order_id = o.order_id
INNER JOIN gold.dim_customers c ON o.customer_id = c.customer_id
INNER JOIN gold.dim_products p ON oi.product_id = p.product_id;

-- QuickSight View: Monthly Sales by Category
CREATE VIEW gold.vw_monthly_sales_by_category AS
SELECT 
    d.year,
    d.month,
    d.month_name,
    p.category,
    COUNT(DISTINCT f.order_id) AS total_orders,
    SUM(f.quantity) AS total_quantity,
    SUM(f.line_total) AS total_revenue
FROM gold.fact_order_items f
INNER JOIN gold.dim_date d ON f.date_key = d.date_key
INNER JOIN gold.dim_products p ON f.product_key = p.product_key
GROUP BY 1, 2, 3, 4;

COMMIT;
```

### Example 2: Incremental Aggregation (PySpark Glue to S3 Gold)

```python
# AWS Glue Job - Incremental Gold Aggregation to S3
import sys
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

# Read Silver data
df_orders = spark.read.parquet(f"s3://{args['S3_BUCKET']}/silver/orders/")
df_customers = spark.read.parquet(f"s3://{args['S3_BUCKET']}/silver/customers/")

# Join and Aggregate
df_gold = df_orders \
    .join(df_customers, "customer_id") \
    .groupBy(
        F.to_date("order_date").alias("date"),
        "customer_segment",
        "country"
    ) \
    .agg(
        F.count("order_id").alias("total_orders"),
        F.sum("amount").alias("gross_sales"),
        F.avg("amount").alias("avg_order_value"),
        F.countDistinct("customer_id").alias("unique_customers")
    ) \
    .withColumn("_gold_created_at", F.current_timestamp()) \
    .withColumn("_grain_level", F.lit("daily_segment"))

# Write to S3 Gold (partitioned by date)
df_gold \
    .coalesce(5) \
    .write \
    .mode("overwrite") \
    .format("parquet") \
    .partitionBy("date") \
    .save(f"s3://{args['S3_BUCKET']}/gold/daily_sales_summary/")

job.commit()
print("✅ Gold aggregation completed for Athena/QuickSight")
```

---

## ❌ Common Mistakes

### ❌ WRONG: No DISTKEY/SORTKEY Optimization
```sql
CREATE TABLE gold.fact_orders (
    order_id VARCHAR(50),
    customer_id VARCHAR(50)
);  -- Missing Redshift optimization
```

### ✅ CORRECT: Optimized for JOINs
```sql
CREATE TABLE gold.fact_orders (
    order_key BIGINT IDENTITY(1,1),
    customer_key BIGINT REFERENCES gold.dim_customers(customer_key)
)
DISTKEY(customer_key)
SORTKEY(order_date);
```

### ❌ WRONG: Complex Queries in QuickSight
```sql
-- QuickSight can't optimize recursive CTEs
WITH RECURSIVE hierarchy AS (...)
SELECT * FROM hierarchy;
```

### ✅ CORRECT: Pre-Aggregated Views
```sql
CREATE VIEW gold.vw_sales_summary AS
SELECT order_date, SUM(amount) AS total_sales
FROM gold.fact_orders
GROUP BY 1;
```

---

## 💡 Best Practices

1. **Star Schema**: Use dimensional modeling (FACT + DIMENSION) for BI tools
2. **Surrogate Keys**: IDENTITY(1,1) keys are faster than natural keys
3. **DISTKEY Strategy**: Co-locate FACT and DIMENSION on join keys
4. **SORTKEY Strategy**: Use date columns for time-series queries
5. **Aggregate Views**: Pre-calculate metrics for QuickSight performance
6. **Date Dimension**: Create dim_date for time intelligence (YTD, QTD)
7. **Incremental Refresh**: Use `_last_updated` for incremental Gold loads
8. **QuickSight Optimization**: Use DIRECT_QUERY mode for large datasets
9. **Naming Convention**: dim_*, fact_*, vw_* for consistency
10. **Athena Alternative**: Store Gold in S3 Parquet for cost-effective Athena queries

---

## 🔄 Version History

- **v2.0.0** (2025-02-12): Enhanced with Star Schema patterns, Redshift optimization (DISTKEY/SORTKEY), QuickSight integration, and incremental aggregation
- **v1.0.0** (2025-01-15): Initial Gold layer extraction from v3.9

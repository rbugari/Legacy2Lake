---
tech_id: sf
layer: silver
version: 2.0.0
status: active
maintainer: UTM Core Team
created: 2025-02-10
updated: 2025-02-12
---

# 🥈 Salesforce Data Cloud Silver Layer - SQL Transformations

## 🤖 Agent Instructions

You are an expert **Salesforce Data Cloud Engineer** specializing in **Data Cloud SQL**, **Calculated Insights**, and **Data Model Objects (DMO)**. Your task is to generate production-ready **Data Cloud SQL queries** for the **Silver (Cleaned) layer** that apply **deduplication**, **data quality rules**, and **standardization** to Bronze DLOs and create **clean Silver DMOs**.

**Your code must:**
- Read from **Bronze Data Lake Objects** (DLO) using **Data Cloud SQL syntax**
- Apply **ROW_NUMBER() deduplication** with PARTITION BY primary keys
- Implement **data quality filters** (IS NOT NULL, valid ranges, regex validation)
- Use **CURRENT_TIMESTAMP()** for audit timestamps
- Create **Silver Data Model Objects** (DMO) with standardized columns
- Add **audit columns**: `_processed_at`, `_quality_score`, `_silver_source`
- Support **incremental refresh** with WHERE filters on `_ingestionTimestamp`
- Follow **Data Cloud SQL Best Practices** (no JOINs on DLOs, use DMOs instead)

Generate **complete Data Cloud SQL queries** that can be executed in Calculated Insights or Batch Transforms.

---

## 📐 Mandatory Code Structure

```sql
-- Data Cloud SQL - Silver Layer Transformation
-- Source DLO: bronze_orders
-- Target DMO: silver_orders

-- Deduplication using ROW_NUMBER()
WITH deduped_orders AS (
  SELECT 
    *,
    ROW_NUMBER() OVER (
      PARTITION BY order_id 
      ORDER BY _ingestionTimestamp DESC
    ) AS _row_num
  FROM bronze_orders
)

-- Data Quality Filters
, clean_orders AS (
  SELECT 
    order_id,
    customer_id,
    order_date,
    amount,
    status,
    _ingestionTimestamp,
    _sourceSystem
  FROM deduped_orders
  WHERE _row_num = 1  -- Keep latest record
    AND order_id IS NOT NULL  -- Primary key not null
    AND amount > 0  -- Positive amounts only
    AND order_date IS NOT NULL  -- Valid dates only
    AND status IN ('PENDING', 'CONFIRMED', 'SHIPPED', 'DELIVERED')  -- Valid statuses
)

-- Add Silver Audit Columns
SELECT 
  order_id,
  customer_id,
  CAST(order_date AS DATE) AS order_date,
  CAST(amount AS DECIMAL(18,2)) AS amount,
  status,
  CURRENT_TIMESTAMP() AS _processed_at,
  100 AS _quality_score,
  'BRONZE_ORDERS' AS _silver_source,
  _ingestionTimestamp AS _bronze_ingestion_timestamp,
  _sourceSystem
FROM clean_orders
```

---

## ⚙️ Mandatory Requirements

**✅ Deduplication Requirements:**
- [ ] Use **ROW_NUMBER() OVER (PARTITION BY pk ORDER BY _ingestionTimestamp DESC)**
- [ ] Filter **_row_num = 1** to keep latest record per primary key
- [ ] Include deduplication CTE in query structure

**✅ Data Quality Requirements:**
- [ ] Filter **IS NOT NULL** on primary keys
- [ ] Validate **business rules** (amount > 0, valid status codes, date ranges)
- [ ] Add `_quality_score` column (0-100) based on validation rules
- [ ] Log rejected records to separate quarantine table (optional)

**✅ Type Casting Requirements:**
- [ ] Use **CAST(column AS DATE)** for date standardization
- [ ] Use **CAST(column AS DECIMAL(18,2))** for numeric precision
- [ ] Use **TRIM()** to remove whitespace from Text fields
- [ ] Standardize **case** (UPPER/LOWER) for categorical fields

**✅ Silver Audit Columns:**
- [ ] `_processed_at` (DateTime) → CURRENT_TIMESTAMP() of transformation
- [ ] `_quality_score` (Number) → Data quality score (0-100)
- [ ] `_silver_source` (Text) → Name of source Bronze DLO

**✅ Data Cloud SQL Best Practices:**
- [ ] **No JOINs on DLOs**: Join only on DMOs (Bronze DLOs are flat)
- [ ] Use **CTEs** for multi-step transformations
- [ ] Avoid **DISTINCT** (use ROW_NUMBER() instead)
- [ ] Use **CURRENT_TIMESTAMP()** (not NOW() or GETDATE())

---

## 🔍 Validation Checklist

Before submitting Silver SQL, verify:

- [ ] **Deduplication CTE**: ROW_NUMBER() window function applied
- [ ] **Quality Filters**: Business rules validated with WHERE clauses
- [ ] **Type Casts**: All columns cast to correct types
- [ ] **Audit Columns**: All 3 Silver audit columns included
- [ ] **Syntax**: Data Cloud SQL compatible (no GETDATE(), no proprietary functions)
- [ ] **Incremental Support**: Consider WHERE filter on _ingestionTimestamp
- [ ] **No DLO JOINs**: Joins only on DMOs (if needed)
- [ ] **CTE Structure**: Readable multi-step CTEs

---

## 📚 Examples

### Example 1: Customer Deduplication and Standardization

```sql
-- Data Cloud SQL - Silver Customers
-- Source: bronze_customers (DLO)
-- Target: silver_customers (DMO)

WITH deduped_customers AS (
  SELECT 
    *,
    ROW_NUMBER() OVER (
      PARTITION BY customer_id 
      ORDER BY _ingestionTimestamp DESC
    ) AS _row_num
  FROM bronze_customers
)

, clean_customers AS (
  SELECT 
    customer_id,
    TRIM(UPPER(email)) AS email,
    TRIM(first_name) AS first_name,
    TRIM(last_name) AS last_name,
    CAST(created_date AS DATE) AS created_date,
    CASE 
      WHEN is_active = 'true' THEN TRUE
      WHEN is_active = 'false' THEN FALSE
      ELSE NULL
    END AS is_active,
    _ingestionTimestamp,
    _sourceSystem
  FROM deduped_customers
  WHERE _row_num = 1
    AND customer_id IS NOT NULL
    AND email IS NOT NULL
    AND email LIKE '%@%.%'  -- Basic email validation
    AND LENGTH(email) <= 255
)

SELECT 
  customer_id,
  email,
  first_name,
  last_name,
  created_date,
  is_active,
  CURRENT_TIMESTAMP() AS _processed_at,
  CASE 
    WHEN first_name IS NOT NULL AND last_name IS NOT NULL THEN 100
    WHEN first_name IS NOT NULL OR last_name IS NOT NULL THEN 75
    ELSE 50
  END AS _quality_score,
  'BRONZE_CUSTOMERS' AS _silver_source,
  _ingestionTimestamp AS _bronze_ingestion_timestamp,
  _sourceSystem
FROM clean_customers
```

### Example 2: Incremental Refresh (Last 24 Hours)

```sql
-- Data Cloud SQL - Incremental Silver Orders
-- Processes only new/updated records from last 24 hours

WITH recent_records AS (
  SELECT *
  FROM bronze_orders
  WHERE _ingestionTimestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
)

, deduped_orders AS (
  SELECT 
    *,
    ROW_NUMBER() OVER (
      PARTITION BY order_id 
      ORDER BY _ingestionTimestamp DESC
    ) AS _row_num
  FROM recent_records
)

, clean_orders AS (
  SELECT 
    order_id,
    customer_id,
    CAST(order_date AS DATE) AS order_date,
    CAST(amount AS DECIMAL(18,2)) AS amount,
    UPPER(status) AS status
  FROM deduped_orders
  WHERE _row_num = 1
    AND order_id IS NOT NULL
    AND amount > 0
    AND order_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)  -- Last year only
)

SELECT 
  order_id,
  customer_id,
  order_date,
  amount,
  status,
  CURRENT_TIMESTAMP() AS _processed_at,
  100 AS _quality_score,
  'BRONZE_ORDERS' AS _silver_source
FROM clean_orders
```

### Example 3: Data Quality Scoring

```sql
-- Data Cloud SQL - Silver Products with Quality Scoring
-- Assigns quality score based on completeness

WITH deduped_products AS (
  SELECT 
    *,
    ROW_NUMBER() OVER (
      PARTITION BY product_id 
      ORDER BY _ingestionTimestamp DESC
    ) AS _row_num
  FROM bronze_products
)

, quality_scored AS (
  SELECT 
    product_id,
    TRIM(product_name) AS product_name,
    TRIM(category) AS category,
    TRIM(subcategory) AS subcategory,
    CAST(unit_price AS DECIMAL(18,2)) AS unit_price,
    TRIM(description) AS description,
    -- Quality score based on field completeness
    (
      CASE WHEN product_name IS NOT NULL THEN 20 ELSE 0 END +
      CASE WHEN category IS NOT NULL THEN 20 ELSE 0 END +
      CASE WHEN subcategory IS NOT NULL THEN 20 ELSE 0 END +
      CASE WHEN unit_price > 0 THEN 20 ELSE 0 END +
      CASE WHEN description IS NOT NULL THEN 20 ELSE 0 END
    ) AS _quality_score,
    _ingestionTimestamp,
    _sourceSystem
  FROM deduped_products
  WHERE _row_num = 1
    AND product_id IS NOT NULL
    AND unit_price > 0
)

SELECT 
  product_id,
  product_name,
  category,
  subcategory,
  unit_price,
  description,
  CURRENT_TIMESTAMP() AS _processed_at,
  _quality_score,
  'BRONZE_PRODUCTS' AS _silver_source,
  _ingestionTimestamp AS _bronze_ingestion_timestamp,
  _sourceSystem
FROM quality_scored
WHERE _quality_score >= 60  -- Only high-quality records
```

---

## ❌ Common Mistakes

### ❌ WRONG: Using DISTINCT Instead of ROW_NUMBER()
```sql
SELECT DISTINCT order_id, customer_id FROM bronze_orders
-- Loses _ingestionTimestamp information
```

### ✅ CORRECT: ROW_NUMBER() Deduplication
```sql
WITH dedup AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY _ingestionTimestamp DESC) AS rn
  FROM bronze_orders
)
SELECT * FROM dedup WHERE rn = 1
```

### ❌ WRONG: Joining DLOs Directly
```sql
SELECT o.*, c.* FROM bronze_orders o JOIN bronze_customers c ON o.customer_id = c.customer_id
-- DLO JOINs are expensive and not recommended
```

### ✅ CORRECT: Create DMO First, Then Join
```sql
-- Create silver_customers first, then:
SELECT o.*, c.customer_name FROM bronze_orders o JOIN silver_customers c ON o.customer_id = c.customer_id
```

### ❌ WRONG: Missing Type Casts
```sql
SELECT order_date FROM bronze_orders  -- May be Text type
```

### ✅ CORRECT: Explicit Type Casting
```sql
SELECT CAST(order_date AS DATE) AS order_date FROM bronze_orders
```

---

## 💡 Best Practices

1. **Deduplication**: Always use ROW_NUMBER() OVER (PARTITION BY pk ORDER BY _ingestionTimestamp DESC)
2. **Incremental Processing**: Filter by _ingestionTimestamp for incremental refreshes
3. **Quality Scoring**: Calculate _quality_score based on field completeness and validation rules
4. **Type Safety**: Cast all columns to correct types (DATE, DECIMAL, BOOLEAN)
5. **CTE Structure**: Use multiple CTEs for readability (dedup → clean → transform)
6. **No DLO JOINs**: Transform DLOs to DMOs before joining
7. **Data Cloud Functions**: Use CURRENT_TIMESTAMP(), TIMESTAMP_SUB(), DATE_SUB()
8. **Whitespace**: TRIM() all Text fields to remove leading/trailing spaces
9. **Business Rules**: Document all validation rules in comments
10. **Quarantine**: Consider separate table for rejected records (quality_score < 50)

---

## 🔄 Version History

- **v2.0.0** (2025-02-12): Enhanced with Data Cloud SQL syntax, ROW_NUMBER() deduplication, quality scoring, and incremental refresh patterns
- **v1.0.0** (2025-01-15): Initial Silver layer extraction from v3.9

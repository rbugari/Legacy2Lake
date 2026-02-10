---
tech_id: sf
layer: gold
version: 2.0.0
status: active
maintainer: UTM Core Team
created: 2025-02-10
updated: 2025-02-12
---

# 🏆 Salesforce Gold Layer - Business Insights & Tableau Integration

## 🤖 Agent Instructions

You are an expert **Salesforce Data Cloud Engineer** specializing in **Calculated Insights**, **Data Model Objects (DMO)**, and **Tableau CRM** integration. Your task is to generate production-ready **Data Cloud SQL queries** for the **Gold (Business) layer** that create **aggregated insights**, **KPIs**, and **Tableau-ready datasets** from Silver DMOs.

**Your code must:**
- Read from **Silver Data Model Objects** (DMO) - NOT Bronze DLOs
- Implement **aggregations** (SUM, AVG, COUNT DISTINCT, MAX, MIN)
- Use **GROUP BY** for dimensional aggregations (date, customer_segment, region)
- Create **business metrics** (total_revenue, avg_order_value, customer_lifetime_value)
- Add **Gold audit columns**: `_gold_created_at`, `_grain_level`, `_refresh_time`
- Support **Tableau CRM** visualization requirements
- Use **window functions** for advanced analytics (running totals, rankings)
- Follow **Data Cloud SQL Best Practices** for performance

Generate **complete Data Cloud SQL queries** that can be executed as Calculated Insights and consumed by Tableau CRM.

---

## 📐 Mandatory Code Structure

```sql
-- Data Cloud SQL - Gold Layer Business Insight
-- Source DMO: silver_orders, silver_customers
-- Target Insight: gold_daily_sales_summary
-- Grain: daily_by_segment
-- BI Tool: Tableau CRM

WITH daily_aggregates AS (
  SELECT 
    CAST(o.order_date AS DATE) AS sales_date,
    c.customer_segment,
    c.country,
    COUNT(DISTINCT o.order_id) AS total_orders,
    COUNT(DISTINCT o.customer_id) AS unique_customers,
    SUM(o.amount) AS gross_sales,
    AVG(o.amount) AS avg_order_value,
    MAX(o.amount) AS max_order_value,
    MIN(o.amount) AS min_order_value
  FROM silver_orders o
  INNER JOIN silver_customers c ON o.customer_id = c.customer_id
  WHERE o.order_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)  -- Last year
  GROUP BY 1, 2, 3
)

SELECT 
  sales_date,
  customer_segment,
  country,
  total_orders,
  unique_customers,
  gross_sales,
  avg_order_value,
  max_order_value,
  min_order_value,
  ROUND(gross_sales / total_orders, 2) AS revenue_per_order,
  ROUND(total_orders * 100.0 / SUM(total_orders) OVER (PARTITION BY sales_date), 2) AS pct_of_daily_orders,
  CURRENT_TIMESTAMP() AS _gold_created_at,
  'daily_by_segment' AS _grain_level,
  CURRENT_TIMESTAMP() AS _refresh_time
FROM daily_aggregates
ORDER BY sales_date DESC, gross_sales DESC
```

---

## ⚙️ Mandatory Requirements

**✅ Aggregation Requirements:**
- [ ] Use **SUM()** for revenue totals
- [ ] Use **COUNT(DISTINCT)** for unique counts (customers, products)
- [ ] Use **AVG()** for averages (order value, rating)
- [ ] Use **MAX()/MIN()** for extremes (highest/lowest values)
- [ ] Apply **GROUP BY** to all non-aggregated columns

**✅ Dimensional Analysis Requirements:**
- [ ] Group by **time dimensions** (date, month, year)
- [ ] Group by **customer dimensions** (segment, tier, country)
- [ ] Group by **product dimensions** (category, brand)
- [ ] Include **grain documentation** in `_grain_level` column

**✅ Gold Audit Columns:**
- [ ] `_gold_created_at` (DateTime) → CURRENT_TIMESTAMP() of insight creation
- [ ] `_grain_level` (Text) → Granularity description (e.g., "daily_by_segment")
- [ ] `_refresh_time` (DateTime) → Last refresh timestamp

**✅ Tableau CRM Requirements:**
- [ ] Use **simple aggregations** (Tableau CRM limitations)
- [ ] Include **calculated metrics** (revenue_per_order, conversion_rate)
- [ ] Avoid **too many dimensions** (max 5-7 for performance)
- [ ] Use **DATE dimensions** for time-series charts

**✅ Performance Optimization:**
- [ ] Filter by **date ranges** to limit data volume
- [ ] Use **pre-aggregated CTEs** for complex calculations
- [ ] Avoid **nested subqueries** (use CTEs instead)
- [ ] Limit **window functions** to final SELECT (not in CTEs)

---

## 🔍 Validation Checklist

Before submitting Gold SQL, verify:

- [ ] **Aggregations**: All aggregate functions (SUM, COUNT, AVG) present
- [ ] **GROUP BY**: Matches all non-aggregated columns
- [ ] **Audit Columns**: All 3 Gold audit columns included
- [ ] **Grain Documentation**: `_grain_level` clearly stated
- [ ] **Date Filters**: Limiting data to relevant time period
- [ ] **JOIN on DMOs**: Joining Silver DMOs (not Bronze DLOs)
- [ ] **Tableau Compatible**: No complex CTEs or recursive queries
- [ ] **Syntax**: Data Cloud SQL compatible
- [ ] **Metric Validation**: Business metrics make sense (no negative sums, etc.)

---

## 📚 Examples

### Example 1: Monthly Customer Lifetime Value

```sql
-- Data Cloud SQL - Customer LTV by Month
-- Source: silver_orders, silver_customers
-- Grain: monthly_by_customer
-- BI Tool: Tableau CRM

WITH customer_monthly_revenue AS (
  SELECT 
    c.customer_id,
    c.customer_segment,
    DATE_TRUNC('MONTH', o.order_date) AS month,
    SUM(o.amount) AS monthly_revenue,
    COUNT(DISTINCT o.order_id) AS monthly_orders
  FROM silver_orders o
  INNER JOIN silver_customers c ON o.customer_id = c.customer_id
  WHERE o.order_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 730 DAY)  -- Last 2 years
  GROUP BY 1, 2, 3
)

, customer_ltv AS (
  SELECT 
    customer_id,
    customer_segment,
    SUM(monthly_revenue) AS total_lifetime_value,
    SUM(monthly_orders) AS total_orders,
    COUNT(DISTINCT month) AS active_months,
    AVG(monthly_revenue) AS avg_monthly_revenue
  FROM customer_monthly_revenue
  GROUP BY 1, 2
)

SELECT 
  customer_id,
  customer_segment,
  total_lifetime_value,
  total_orders,
  active_months,
  avg_monthly_revenue,
  ROUND(total_lifetime_value / total_orders, 2) AS avg_order_value,
  ROUND(total_lifetime_value / active_months, 2) AS revenue_per_active_month,
  CURRENT_TIMESTAMP() AS _gold_created_at,
  'customer_lifetime' AS _grain_level,
  CURRENT_TIMESTAMP() AS _refresh_time
FROM customer_ltv
WHERE total_lifetime_value > 100  -- Filter low-value customers
ORDER BY total_lifetime_value DESC
```

### Example 2: Product Category Performance

```sql
-- Data Cloud SQL - Product Category Sales Performance
-- Source: silver_order_items, silver_products
-- Grain: category_by_quarter
-- BI Tool: Tableau CRM

WITH quarterly_sales AS (
  SELECT 
    p.category,
    p.subcategory,
    DATE_TRUNC('QUARTER', oi.order_date) AS quarter,
    COUNT(DISTINCT oi.order_id) AS total_orders,
    SUM(oi.quantity) AS total_units_sold,
    SUM(oi.line_total) AS gross_revenue,
    SUM(oi.quantity * oi.unit_price * oi.discount_percent / 100) AS total_discounts,
    SUM(oi.line_total) - SUM(oi.quantity * oi.unit_price * oi.discount_percent / 100) AS net_revenue
  FROM silver_order_items oi
  INNER JOIN silver_products p ON oi.product_id = p.product_id
  WHERE oi.order_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 730 DAY)  -- Last 2 years
  GROUP BY 1, 2, 3
)

SELECT 
  category,
  subcategory,
  quarter,
  total_orders,
  total_units_sold,
  gross_revenue,
  total_discounts,
  net_revenue,
  ROUND(net_revenue / total_orders, 2) AS revenue_per_order,
  ROUND(total_discounts * 100.0 / gross_revenue, 2) AS discount_rate_pct,
  ROUND(net_revenue * 100.0 / SUM(net_revenue) OVER (PARTITION BY quarter), 2) AS pct_of_quarterly_revenue,
  CURRENT_TIMESTAMP() AS _gold_created_at,
  'category_quarterly' AS _grain_level,
  CURRENT_TIMESTAMP() AS _refresh_time
FROM quarterly_sales
ORDER BY quarter DESC, net_revenue DESC
```

### Example 3: Customer Cohort Analysis

```sql
-- Data Cloud SQL - Customer Cohort Retention Analysis
-- Source: silver_customers, silver_orders
-- Grain: cohort_by_month
-- BI Tool: Tableau CRM

WITH customer_cohorts AS (
  SELECT 
    customer_id,
    DATE_TRUNC('MONTH', MIN(created_date)) AS cohort_month
  FROM silver_customers
  GROUP BY 1
)

, cohort_orders AS (
  SELECT 
    c.customer_id,
    cc.cohort_month,
    DATE_TRUNC('MONTH', o.order_date) AS order_month,
    SUM(o.amount) AS cohort_revenue
  FROM silver_orders o
  INNER JOIN customer_cohorts cc ON o.customer_id = cc.customer_id
  GROUP BY 1, 2, 3
)

, cohort_summary AS (
  SELECT 
    cohort_month,
    order_month,
    COUNT(DISTINCT customer_id) AS active_customers,
    SUM(cohort_revenue) AS total_revenue,
    AVG(cohort_revenue) AS avg_revenue_per_customer
  FROM cohort_orders
  GROUP BY 1, 2
)

SELECT 
  cohort_month,
  order_month,
  active_customers,
  total_revenue,
  avg_revenue_per_customer,
  ROUND(active_customers * 100.0 / FIRST_VALUE(active_customers) OVER (PARTITION BY cohort_month ORDER BY order_month), 2) AS retention_rate_pct,
  CURRENT_TIMESTAMP() AS _gold_created_at,
  'cohort_monthly' AS _grain_level,
  CURRENT_TIMESTAMP() AS _refresh_time
FROM cohort_summary
ORDER BY cohort_month DESC, order_month ASC
```

---

## ❌ Common Mistakes

### ❌ WRONG: Joining Bronze DLOs Instead of Silver DMOs
```sql
SELECT * FROM bronze_orders o JOIN bronze_customers c ON o.customer_id = c.customer_id
-- Use Silver DMOs for Gold layer
```

### ✅ CORRECT: Join Silver DMOs
```sql
SELECT * FROM silver_orders o JOIN silver_customers c ON o.customer_id = c.customer_id
```

### ❌ WRONG: Missing GROUP BY Columns
```sql
SELECT customer_segment, SUM(amount) FROM silver_orders
-- Missing GROUP BY customer_segment
```

### ✅ CORRECT: Complete GROUP BY
```sql
SELECT customer_segment, SUM(amount) AS total_sales FROM silver_orders GROUP BY 1
```

### ❌ WRONG: No Date Filtering (Full Table Scan)
```sql
SELECT * FROM silver_orders  -- Scans entire table
```

### ✅ CORRECT: Date Range Filter
```sql
SELECT * FROM silver_orders WHERE order_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
```

---

## 💡 Best Practices

1. **Join DMOs Only**: Always join Silver DMOs, never Bronze DLOs in Gold layer
2. **Date Filters**: Always filter by date ranges to limit data volume
3. **Grain Documentation**: Document granularity level in `_grain_level` column
4. **Window Functions**: Use for advanced analytics (running totals, rankings)
5. **CTEs for Readability**: Use multiple CTEs for complex calculations
6. **Tableau Compatibility**: Keep queries simple for Tableau CRM consumption
7. **Business Metrics**: Calculate derived metrics (revenue_per_order, conversion_rate)
8. **Percentages**: Use ROUND() with 2 decimals for percentage calculations
9. **Distinct Counts**: Use COUNT(DISTINCT) for unique customer/product counts
10. **Incremental Refresh**: Consider incremental refresh for large datasets

---

## 🔄 Version History

- **v2.0.0** (2025-02-12): Enhanced with Data Cloud SQL aggregations, window functions, Tableau CRM integration, and cohort analysis examples
- **v1.0.0** (2025-01-15): Initial Gold layer extraction from v3.9

# 🧪 Sprint 0 Day 4 - Agent C Testing Plan

**Date:** 2026-02-10 (Day 4 of 7)  
**Status:** READY TO EXECUTE  
**Objective:** Validate all 24 enhanced prompts (v2.0.0) with Agent C code generation

---

## 🎯 Testing Objectives

1. **Code Quality**: Verify generated code matches mandatory requirements
2. **Completeness**: Ensure all sections (audit columns, examples, etc.) are used
3. **Accuracy**: Check technology-specific patterns are correct
4. **Usability**: Identify prompt ambiguities or missing context
5. **Consistency**: Validate similar patterns across cartridges

---

## 📋 Test Matrix (24 Scenarios)

### Priority Levels
- 🔴 **P0 (Critical)**: Must work - blocking issues
- 🟡 **P1 (High)**: Should work - major improvements needed
- 🟢 **P2 (Medium)**: Nice to have - minor refinements

---

## 🧪 Test Scenarios by Cartridge

### 1. PySpark (3 tests)

#### Test 1.1: Bronze - CSV Ingestion 🔴 P0
```yaml
Test ID: PYSPARK-BRONZE-01
Prompt to Agent C: |
  "Using PySpark, create a Bronze layer ingestion job that reads CSV files 
  from /landing/customers/ and writes to Delta table bronze.customers.
  Include all mandatory audit columns."

Expected Output:
  - spark.read.csv() with inferSchema
  - .withColumn("_ingestion_timestamp", current_timestamp())
  - .withColumn("_source_system", lit("csv_landing"))
  - .write.format("delta").mode("append").saveAsTable("bronze.customers")
  - partitionBy("_ingestion_date")

Validation Checklist:
  ✅ Uses Delta Lake format
  ✅ Includes 4 mandatory audit columns
  ✅ Uses .saveAsTable() not .save()
  ✅ Partition by _ingestion_date
  ✅ Append mode (not overwrite)
  ✅ Complete runnable code (no placeholders)
```

#### Test 1.2: Silver - Deduplication 🔴 P0
```yaml
Test ID: PYSPARK-SILVER-01
Prompt to Agent C: |
  "Create a PySpark Silver layer job that deduplicates bronze.orders 
  using order_id as primary key. Keep the latest record based on 
  _ingestion_timestamp. Write to silver.orders."

Expected Output:
  - Window.partitionBy("order_id").orderBy(col("_ingestion_timestamp").desc())
  - .withColumn("_row_num", row_number().over(window_spec))
  - .filter(col("_row_num") == 1)
  - DeltaTable.forName("silver.orders").merge() for incremental

Validation Checklist:
  ✅ Window function with ROW_NUMBER()
  ✅ Filters _row_num = 1
  ✅ Uses MERGE for incremental (not full overwrite)
  ✅ Preserves bronze audit columns
```

#### Test 1.3: Gold - Star Schema 🟡 P1
```yaml
Test ID: PYSPARK-GOLD-01
Prompt to Agent C: |
  "Build a Gold layer Star Schema with fact_orders and dim_customers.
  Aggregate daily sales by customer segment. Use PySpark."

Expected Output:
  - DIMENSION table: dim_customers with surrogate key customer_key
  - FACT table: fact_orders with foreign key to dim_customers
  - .groupBy("order_date", "customer_segment").agg(sum("amount"))
  - SCD Type 2 logic for dimensions (effective_start/end_date)

Validation Checklist:
  ✅ Surrogate keys (auto-increment or hash)
  ✅ Foreign key relationships documented
  ✅ Aggregations with GROUP BY
  ✅ SCD Type 2 columns if dimension changes
```

---

### 2. Snowflake (3 tests)

#### Test 2.1: Bronze - Snowpark Python 🔴 P0
```yaml
Test ID: SNOWFLAKE-BRONZE-01
Prompt to Agent C: |
  "Using Snowpark Python, ingest JSON files from @MY_STAGE/landing/ 
  into BRONZE.CUSTOMERS table in Snowflake."

Expected Output:
  - session.read.json("@MY_STAGE/landing/")
  - .with_column("_INGESTION_TIMESTAMP", F.current_timestamp())
  - .save_as_table("BRONZE.CUSTOMERS", mode="append")
  - UPPERCASE table/column names
  - NO partitionBy() (Snowflake doesn't partition)

Validation Checklist:
  ✅ Snowpark Python syntax (not PySpark)
  ✅ UPPERCASE naming convention
  ✅ .save_as_table() not .saveAsTable()
  ✅ No Delta Lake references
```

#### Test 2.2: Silver - MERGE Statement 🔴 P0
```yaml
Test ID: SNOWFLAKE-SILVER-01
Prompt to Agent C: |
  "Create Snowpark job to deduplicate BRONZE.ORDERS into SILVER.ORDERS.
  Use QUALIFY with ROW_NUMBER() for deduplication."

Expected Output:
  - QUALIFY ROW_NUMBER() OVER (PARTITION BY ORDER_ID ORDER BY _INGESTION_TIMESTAMP DESC) = 1
  - session.table("BRONZE.ORDERS").filter(...)
  - MERGE INTO SILVER.ORDERS for incremental updates

Validation Checklist:
  ✅ Uses QUALIFY (Snowflake-specific)
  ✅ ROW_NUMBER() window function
  ✅ MERGE statement syntax
```

#### Test 2.3: Gold - Warehouse Optimization 🟡 P1
```yaml
Test ID: SNOWFLAKE-GOLD-01
Prompt to Agent C: |
  "Build Gold aggregation table AGG_DAILY_SALES in Snowflake.
  Optimize for BI queries with clustering."

Expected Output:
  - CREATE TABLE with CLUSTER BY (ORDER_DATE, CUSTOMER_SEGMENT)
  - GROUP BY with SUM(), AVG(), COUNT()
  - Warehouse optimization comments (SMALL vs MEDIUM)

Validation Checklist:
  ✅ CLUSTER BY clause
  ✅ Warehouse sizing recommendations
  ✅ Pre-aggregated metrics
```

---

### 3. dbt (3 tests)

#### Test 3.1: Bronze - Source Definition 🔴 P0
```yaml
Test ID: DBT-BRONZE-01
Prompt to Agent C: |
  "Create dbt model for Bronze layer that references raw schema.
  Source: raw.customers, Target: bronze.customers"

Expected Output:
  - models/bronze/customers.sql
  - {{ source('raw', 'customers') }}
  - {{ config(materialized='incremental') }}
  - Audit columns: _dbt_ingestion_timestamp etc.

Validation Checklist:
  ✅ Uses {{ source() }} not raw table names
  ✅ config(materialized='incremental')
  ✅ CTE pattern (WITH source_data AS...)
```

#### Test 3.2: Silver - Incremental Model 🔴 P0
```yaml
Test ID: DBT-SILVER-01
Prompt to Agent C: |
  "Create dbt Silver model that deduplicates {{ ref('bronze__orders') }}.
  Use incremental materialization."

Expected Output:
  - {{ ref('bronze__orders') }}
  - {% if is_incremental() %} WHERE clause
  - ROW_NUMBER() in CTE for deduplication
  - dbt_utils.surrogate_key() for composite keys

Validation Checklist:
  ✅ {{ ref() }} for upstream dependencies
  ✅ {% if is_incremental() %} logic
  ✅ CTE-based deduplication
  ✅ dbt_utils functions
```

#### Test 3.3: Gold - Semantic Layer 🟡 P1
```yaml
Test ID: DBT-GOLD-01
Prompt to Agent C: |
  "Build dbt Gold model with metrics and semantic layer.
  Define total_revenue metric."

Expected Output:
  - models/gold/fct_orders.sql
  - metrics/revenue_metrics.yml with {{ metric() }}
  - semantic_models/orders.yml
  - Dimensions and measures defined

Validation Checklist:
  ✅ metrics/*.yml files
  ✅ semantic_models/*.yml files
  ✅ {{ metric() }} references in models
```

---

### 4. MS Fabric (3 tests)

#### Test 4.1: Bronze - Lakehouse Ingestion 🔴 P0
```yaml
Test ID: FABRIC-BRONZE-01
Prompt to Agent C: |
  "Create Fabric notebook to ingest Parquet files from OneLake 
  Files/Landing/ into Bronze Lakehouse table Customers."

Expected Output:
  - spark.read.parquet("Files/Landing/customers/")
  - PascalCase: BronzeCustomers
  - V-Order optimization: .option("spark.sql.parquet.vorder.enabled", "true")
  - .saveAsTable("BronzeCustomers")

Validation Checklist:
  ✅ Files/ path (OneLake convention)
  ✅ PascalCase naming
  ✅ V-Order option
  ✅ Lakehouse table format
```

#### Test 4.2: Silver - Window Deduplication + MERGE 🔴 P0
```yaml
Test ID: FABRIC-SILVER-01
Prompt to Agent C: |
  "Deduplicate BronzeOrders into SilverOrders in Fabric Lakehouse.
  Use window functions and MERGE for incremental."

Expected Output:
  - Window.partitionBy("OrderId").orderBy(...)
  - DeltaTable.forName("SilverOrders").merge()
  - V-Order optimization after MERGE
  - df.write.mode("overwrite").option("vorder.enabled", "true")

Validation Checklist:
  ✅ Window function deduplication
  ✅ MERGE statement
  ✅ V-Order after MERGE (critical for Direct Lake)
```

#### Test 4.3: Gold - Power BI Direct Lake 🟡 P1
```yaml
Test ID: FABRIC-GOLD-01
Prompt to Agent C: |
  "Create Gold aggregation FactOrders optimized for Power BI Direct Lake."

Expected Output:
  - PascalCase: FactOrders, DimCustomers
  - Pre-aggregated to grain (daily_by_customer)
  - V-Order enabled
  - Surrogate keys: CustomerKey (BIGINT)
  - Comments: "Optimized for Direct Lake - 5-7 dimensions max"

Validation Checklist:
  ✅ Star Schema (FACT + DIMENSION)
  ✅ 5-7 dimensions max (Direct Lake limit)
  ✅ V-Order optimization
  ✅ Integer surrogate keys
```

---

### 5. GCP BigQuery (3 tests)

#### Test 5.1: Bronze - Standard SQL 🔴 P0
```yaml
Test ID: BIGQUERY-BRONZE-01
Prompt to Agent C: |
  "Create BigQuery Bronze table from GCS CSV files.
  Project: my-project, Dataset: bronze, Table: customers"

Expected Output:
  - CREATE OR REPLACE TABLE `my-project.bronze.customers`
  - PARTITION BY DATE(_ingestion_date)
  - CLUSTER BY customer_id, region
  - OPTIONS(description="Bronze raw customers")

Validation Checklist:
  ✅ Backticks for three-part naming
  ✅ PARTITION BY DATE()
  ✅ CLUSTER BY (2-4 columns)
  ✅ Table OPTIONS
```

#### Test 5.2: Silver - MERGE USING 🔴 P0
```yaml
Test ID: BIGQUERY-SILVER-01
Prompt to Agent C: |
  "Deduplicate bronze.orders into silver.orders using MERGE in BigQuery."

Expected Output:
  - MERGE `project.silver.orders` AS target
  - USING (subquery with ROW_NUMBER()) AS source
  - ON target.order_id = source.order_id
  - WHEN MATCHED THEN UPDATE, WHEN NOT MATCHED THEN INSERT

Validation Checklist:
  ✅ MERGE...USING syntax
  ✅ ROW_NUMBER() in USING clause
  ✅ MATCHED/NOT MATCHED clauses
```

#### Test 5.3: Gold - Looker Integration 🟡 P1
```yaml
Test ID: BIGQUERY-GOLD-01
Prompt to Agent C: |
  "Create Gold aggregation view for Looker dashboard.
  Metric: daily_revenue by customer_segment."

Expected Output:
  - CREATE MATERIALIZED VIEW (not regular VIEW)
  - SAFE_DIVIDE() for calculated metrics
  - Pre-aggregated with GROUP BY
  - Comments for Looker LookML mapping

Validation Checklist:
  ✅ MATERIALIZED VIEW
  ✅ SAFE_DIVIDE() for safe calculations
  ✅ Group by dimensions
```

---

### 6. AWS Glue (3 tests)

#### Test 6.1: Bronze - S3 Parquet Ingestion 🔴 P0
```yaml
Test ID: AWS-BRONZE-01
Prompt to Agent C: |
  "Create AWS Glue job to ingest CSV from s3://bucket/landing/ 
  to s3://bucket/bronze/customers/ in Parquet format."

Expected Output:
  - from awsglue.context import GlueContext
  - args = getResolvedOptions(sys.argv, ['JOB_NAME', 'S3_BUCKET'])
  - glueContext = GlueContext(SparkContext.getOrCreate())
  - job = Job(glueContext)
  - job.init(args['JOB_NAME'], args)
  - df.write.format("parquet").option("compression", "snappy").partitionBy("_ingestion_date").save("s3://...")
  - job.commit()

Validation Checklist:
  ✅ GlueContext initialization
  ✅ getResolvedOptions()
  ✅ job.init() and job.commit()
  ✅ S3 paths
  ✅ Parquet + Snappy compression
```

#### Test 6.2: Silver - Redshift JDBC 🔴 P0
```yaml
Test ID: AWS-SILVER-01
Prompt to Agent C: |
  "Load cleaned data from S3 Silver into Redshift table using Glue job."

Expected Output:
  - spark-redshift connector
  - .write.format("io.github.spark_redshift_community.spark.redshift")
  - .option("url", "jdbc:redshift://...")
  - .option("tempdir", "s3://bucket/temp/")
  - .option("dbtable", "public.silver_orders")
  - COPY command optimization

Validation Checklist:
  ✅ spark-redshift connector
  ✅ JDBC URL with Secrets Manager
  ✅ tempdir for COPY optimization
  ✅ COPY command (not INSERT)
```

#### Test 6.3: Gold - QuickSight Dataset 🟡 P1
```yaml
Test ID: AWS-GOLD-01
Prompt to Agent C: |
  "Create Redshift Star Schema with DISTKEY/SORTKEY optimization 
  for QuickSight dashboard."

Expected Output:
  - CREATE TABLE fact_orders (DISTKEY(customer_key), SORTKEY(order_date))
  - CREATE TABLE dim_customers (DISTKEY(customer_key))
  - Pre-aggregated view: vw_daily_sales
  - QuickSight dataset JSON definition

Validation Checklist:
  ✅ DISTKEY for co-located JOINs
  ✅ SORTKEY for time-series
  ✅ IDENTITY(1,1) for surrogate keys
  ✅ QuickSight dataset JSON
```

---

### 7. Salesforce Data Cloud (3 tests)

#### Test 7.1: Bronze - Ingestion API Schema 🔴 P0
```yaml
Test ID: SALESFORCE-BRONZE-01
Prompt to Agent C: |
  "Create Data Cloud Ingestion API JSON schema for customers DLO.
  Fields: customer_id (PK), email, created_date."

Expected Output:
  - {
      "name": "customers_dlo",
      "sourceObject": "customers",
      "fields": [
        {"name": "customer_id", "type": "Text", "isPrimaryKey": true},
        {"name": "email", "type": "Text"},
        {"name": "created_date", "type": "DateTime"}
      ],
      "config": {"ingestionMode": "upsert", "matchFields": ["customer_id"]}
    }

Validation Checklist:
  ✅ Valid JSON structure
  ✅ isPrimaryKey: true
  ✅ ingestionMode: upsert/insert/delete
  ✅ matchFields for upsert
```

#### Test 7.2: Silver - Data Cloud SQL 🔴 P0
```yaml
Test ID: SALESFORCE-SILVER-01
Prompt to Agent C: |
  "Transform customers DLO into customers DMO using Data Cloud SQL.
  Deduplicate by customer_id, keep latest by _ingestionTimestamp."

Expected Output:
  - WITH deduped AS (
      SELECT *, ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY _ingestionTimestamp DESC) AS _row_num
      FROM customers_dlo
    )
  - SELECT * FROM deduped WHERE _row_num = 1
  - CURRENT_TIMESTAMP() (not NOW() or GETDATE())

Validation Checklist:
  ✅ CTE pattern (WITH...AS)
  ✅ ROW_NUMBER() OVER
  ✅ CURRENT_TIMESTAMP() function
  ✅ No JOINs on DLOs (only DMOs)
```

#### Test 7.3: Gold - Calculated Insight 🟡 P1
```yaml
Test ID: SALESFORCE-GOLD-01
Prompt to Agent C: |
  "Create Calculated Insight for customer lifetime value (LTV) 
  aggregated monthly by segment."

Expected Output:
  - SELECT 
      DATE_TRUNC('month', order_date) AS month,
      customer_segment,
      SUM(order_amount) AS total_ltv,
      COUNT(DISTINCT customer_id) AS unique_customers
    FROM orders_dmo
    GROUP BY month, customer_segment
  - _grain_level column: "monthly_by_segment"

Validation Checklist:
  ✅ DATE_TRUNC for time grouping
  ✅ SUM, COUNT DISTINCT, AVG
  ✅ GROUP BY dimensions
  ✅ _grain_level metadata
```

---

### 8. Base Generic (3 tests)

#### Test 8.1: Bronze - Pseudocode Pattern 🟢 P2
```yaml
Test ID: BASE-BRONZE-01
Prompt to Agent C: |
  "Using generic pseudocode, describe Bronze layer ingestion from REST API."

Expected Output:
  - FUNCTION ingest_api_data()
  - HTTP_GET with pagination (offset/limit)
  - RETRY logic (3 attempts)
  - WRITE to EXTERNAL_TABLE or FILE
  - Audit columns: _ingestion_timestamp, _source_system

Validation Checklist:
  ✅ Technology-agnostic pseudocode
  ✅ Pagination pattern
  ✅ Retry logic
  ✅ Audit columns
```

#### Test 8.2: Silver - Quality Scoring 🟢 P2
```yaml
Test ID: BASE-SILVER-01
Prompt to Agent C: |
  "Create generic quality scoring algorithm for Silver layer (0-100 score)."

Expected Output:
  - FUNCTION calculate_quality_score(record)
  - 20 points per critical field (5 fields = 100)
  - IF field IS NULL THEN score -= 20
  - RETURN score

Validation Checklist:
  ✅ 0-100 scale
  ✅ Weighted by field importance
  ✅ Deduction logic
```

#### Test 8.3: Gold - Cohort Analysis 🟢 P2
```yaml
Test ID: BASE-GOLD-01
Prompt to Agent C: |
  "Describe cohort retention analysis pattern in generic pseudocode."

Expected Output:
  - GROUP_BY(cohort_month, months_since_first_order)
  - RETENTION_RATE = COUNT(returning_customers) / COUNT(cohort_customers)
  - Grain: "cohort_monthly"

Validation Checklist:
  ✅ Cohort definition
  ✅ Retention calculation
  ✅ Grain documentation
```

---

## 📊 Success Criteria

### Per-Test Metrics
- ✅ **Code Compiles**: No syntax errors (auto-check if possible)
- ✅ **Requirements Met**: 80%+ checklist items passed
- ✅ **Complete**: No placeholders like `# TODO` or `...your code...`
- ✅ **Runable**: Can execute with minimal setup (env vars only)

### Overall Sprint Goals
- 🎯 **P0 Tests**: 100% pass rate (16 tests)
- 🎯 **P1 Tests**: 75%+ pass rate (6 tests)
- 🎯 **P2 Tests**: 50%+ pass rate (2 tests)
- 🎯 **Prompt Refinements**: Document 5-10 improvements needed

---

## 🔄 Testing Workflow

### Step 1: Prepare Agent C Environment
```bash
# Ensure Agent C has access to all 24 prompts
ls -la prompt_lab/cartridges/*/

# Expected output:
# pyspark/*.md (3 files)
# snowflake/*.md (3 files)
# dbt/*.md (3 files)
# fabric/*.md (3 files)
# bigquery/*.md (3 files)
# aws/*.md (3 files)
# sf/*.md (3 files)
# base/*.md (3 files)
```

### Step 2: Execute Tests (Choose Method)

#### Option A: Manual Testing (Recommended for Sprint 0)
1. Open Agent C chat interface
2. Copy prompt from test scenario
3. Attach relevant cartridge prompt (e.g., `pyspark/bronze_layer.md`)
4. Review generated code
5. Score against validation checklist
6. Document issues in results spreadsheet

#### Option B: Automated Testing (Future - Sprint 1)
```python
# test_agent_c.py (future implementation)
for test in test_matrix:
    response = agent_c.generate(
        user_prompt=test.prompt,
        system_prompt=test.cartridge_prompt
    )
    
    score = validate_checklist(response, test.validation_checklist)
    
    results.append({
        "test_id": test.id,
        "pass": score >= 0.8,
        "score": score,
        "issues": extract_issues(response)
    })

generate_report(results)
```

### Step 3: Track Results
Use this spreadsheet template:

| Test ID | Cartridge | Layer | Pass/Fail | Score | Issues Found | Notes |
|---------|-----------|-------|-----------|-------|--------------|-------|
| PYSPARK-BRONZE-01 | PySpark | Bronze | ✅ | 95% | Missing .coalesce() | Add file optimization guidance |
| SNOWFLAKE-BRONZE-01 | Snowflake | Bronze | ❌ | 60% | Used Delta Lake syntax | Clarify Snowflake-only patterns |
| ... | ... | ... | ... | ... | ... | ... |

### Step 4: Analyze Patterns
After all tests:
1. **Group issues by category**:
   - Syntax errors
   - Missing audit columns
   - Wrong technology patterns
   - Incomplete examples
   - Ambiguous instructions

2. **Prioritize fixes**:
   - P0 issues: Fix immediately (blocking)
   - P1 issues: Fix in Sprint 1
   - P2 issues: Backlog for v3.0

3. **Update prompts**:
   - Refine unclear sections
   - Add missing examples
   - Strengthen validation checklists

---

## 📈 Expected Outcomes

### Immediate (End of Day 4)
- ✅ 24 Agent C responses collected
- ✅ Issue tracker populated (5-10 issues expected)
- ✅ Pass rate calculated (target: 85%+ overall)

### Short-Term (Sprint 0 Day 5-7)
- ✅ P0 prompt fixes applied (v2.0.1)
- ✅ Testing report published
- ✅ Sprint 0 retrospective completed

### Long-Term (Sprint 1+)
- ✅ Automated testing framework built
- ✅ CI/CD integration for prompt validation
- ✅ Regression test suite established

---

## 🚨 Known Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Agent C generates incorrect patterns | HIGH | Manual code review required; update prompts with counter-examples |
| Prompts too long (token limit) | MEDIUM | Split into focused sections; use prompt compression techniques |
| Technology drift (e.g., new Fabric features) | LOW | Version prompts; quarterly tech review cycle |
| Ambiguous requirements | HIGH | Add explicit negative examples ("Don't do X, do Y instead") |

---

## 📝 Test Execution Checklist

- [ ] All 24 prompts accessible in `prompt_lab/cartridges/`
- [ ] Agent C environment configured
- [ ] Results tracking spreadsheet created
- [ ] 16 P0 tests executed (critical path)
- [ ] 6 P1 tests executed
- [ ] 2 P2 tests executed (bonus)
- [ ] Issues documented with screenshots
- [ ] Pass rate calculated
- [ ] Prompt refinement backlog created
- [ ] Sprint 0 Day 4 report published

---

## 🎯 Next Steps After Testing

1. **Triage Issues** (Day 5):
   - P0 failures → immediate prompt fixes
   - P1 failures → Sprint 1 backlog
   - P2 failures → v3.0 roadmap

2. **Refine Prompts** (Day 5-6):
   - Update unclear sections
   - Add missing examples
   - Strengthen validation rules

3. **Re-test** (Day 6):
   - Re-run failed tests with updated prompts
   - Confirm fixes resolve issues

4. **Sprint 0 Wrap-Up** (Day 7):
   - Final report
   - Retrospective
   - Sprint 1 planning

---

**Ready to start testing?** Pick a cartridge and begin with P0 Bronze tests! 🚀

---

**Last Updated:** 2026-02-10  
**Status:** Ready for execution  
**Owner:** UTM Core Team

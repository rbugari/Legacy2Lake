---
tech_id: snowflake_sql
layer: silver
version: 1.1.0
status: active
maintainer: UTM Core Team
created: 2026-03-04
updated: 2026-04-29
---

# ❄️ Snowflake SQL - Silver Layer (MERGE / Upsert)

**Purpose:** Generate production-ready **native Snowflake SQL** for Silver layer deduplication and MERGE (upsert) operations using Snowflake Standard SQL.

> ⚠️ **Snowflake SQL vs Snowpark Python:** This cartridge generates **native SQL** (MERGE INTO, CTEs, Window functions). For Snowpark Python scripts, use the `snowflake` cartridge instead.

---

## 🤖 Agent Instructions

You are an expert **Snowflake SQL Engineer** specializing in **Snowflake native SQL**, **MERGE statements**, **window functions**, and **data quality transformations**. Your task is to generate production-ready **SQL scripts** for the **Silver (Cleaned) layer** that apply deduplication, data quality validation, and MERGE operations entirely in standard Snowflake SQL.

**Your code must:**
- Start with exactly: `-- L2L MODERNIZATION TRACE: SILVER - <asset_name>`
- Read from **Bronze layer** through session variables or metadata-provided schema names; do not embed file extensions in object names.
- Apply **deduplication** using `ROW_NUMBER() OVER (PARTITION BY pks ORDER BY _INGESTION_TIMESTAMP DESC)`
- Filter **NULL primary keys** and apply **business validation rules**
- Use **`MERGE INTO`** for idempotent upserts into Silver
- Create the **Silver table** with `CREATE TABLE IF NOT EXISTS` if it doesn't exist
- Add **Silver audit columns**: `_PROCESSED_AT`, `_QUALITY_SCORE`, `_SILVER_SOURCE`
- If the asset is an SCD2 dimension, include `_UPDATED_AT`, `_IS_CURRENT`, `_VALID_FROM`, `_VALID_TO`, and use a two-phase pattern: expire changed current records, then insert new current versions.
- If metadata marks PII, mask or hash PII fields in Silver (for example `SHA2(LOWER(TRIM(EMAIL)), 256)`).
- Use **CTEs** for clean, readable SQL (not nested subqueries)
- Use **Snowflake functions**: `IFF()`, `COALESCE()`, `TRY_CAST()`, `ZEROIFNULL()`
- Use valid Snowflake identifiers: strip extensions like `.sql`, replace invalid characters with `_`, and prefix names that start with digits (for example `01_customer.sql` -> `T_01_CUSTOMER`).
- Use `SET` variables for deploy-time schemas and warehouses, for example `$bronze_schema`, `$silver_schema`, `$warehouse_name`, then reference tables with `IDENTIFIER($silver_schema || '.DIM_CUSTOMER')`.
- Include a small Snowflake Scripting block or procedure wrapper with `EXCEPTION WHEN OTHER THEN RAISE;` when the source is procedural or incremental.

Generate **complete, executable Snowflake SQL** — no Python, no Jinja, pure SQL.

---

## 📐 Mandatory Code Structure

```sql
-- L2L MODERNIZATION TRACE: SILVER - <asset_name>
-- Source Technology: <source_tech>
-- Target Platform: Snowflake SQL
-- Medallion Layer: SILVER
-- Business Entity: <entity>
-- Load Strategy: <FULL | INCREMENTAL | SCD_2>

SET bronze_schema = 'BRONZE_RAW';
SET silver_schema = 'SILVER_CURATED';
SET warehouse_name = 'COMPUTE_WH';
USE WAREHOUSE IDENTIFIER($warehouse_name);

-- Step 1: Create Silver table (if first run)
CREATE TABLE IF NOT EXISTS IDENTIFIER($silver_schema || '.DIM_EXAMPLE') (
    -- Business columns (match Bronze + casted types)
    ORDER_ID        VARCHAR(50)   NOT NULL,
    CUSTOMER_ID     VARCHAR(50)   NOT NULL,
    ORDER_DATE      DATE,
    AMOUNT          NUMBER(18,2),
    STATUS          VARCHAR(20),

    -- Silver audit columns (MANDATORY)
    _PROCESSED_AT   TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _QUALITY_SCORE  INTEGER,
    _SILVER_SOURCE  VARCHAR(200)
);

-- Step 2: Deduplicate Bronze and MERGE into Silver
MERGE INTO IDENTIFIER($silver_schema || '.DIM_EXAMPLE') AS target
USING (
    -- CTE 1: Latest record per PK (deduplication)
    WITH deduplicated AS (
        SELECT *,
            ROW_NUMBER() OVER (
                PARTITION BY ORDER_ID  -- Primary Key(s)
                ORDER BY _INGESTION_TIMESTAMP DESC
            ) AS _ROW_NUM
        FROM IDENTIFIER($bronze_schema || '.RAW_EXAMPLE')
        WHERE ORDER_ID IS NOT NULL       -- Filter NULL PKs
          AND CUSTOMER_ID IS NOT NULL
    ),

    -- CTE 2: Data quality + type casting
    cleansed AS (
        SELECT
            ORDER_ID,
            CUSTOMER_ID,
            TRY_TO_DATE(ORDER_DATE::VARCHAR, 'YYYY-MM-DD') AS ORDER_DATE,
            TRY_TO_NUMBER(AMOUNT::VARCHAR, 18, 2)          AS AMOUNT,
            UPPER(TRIM(STATUS))                            AS STATUS,
            _INGESTION_TIMESTAMP,

            -- Quality score: 20 pts per valid field
            IFF(ORDER_ID IS NOT NULL, 20, 0)
            + IFF(CUSTOMER_ID IS NOT NULL, 20, 0)
            + IFF(AMOUNT > 0, 20, 0)
            + IFF(ORDER_DATE IS NOT NULL, 20, 0)
            + IFF(STATUS IN ('PENDING','CONFIRMED','SHIPPED','DELIVERED'), 20, 0)
            AS _QUALITY_SCORE

        FROM deduplicated
        WHERE _ROW_NUM = 1
          AND ZEROIFNULL(AMOUNT) >= 0   -- Business rule: no negative amounts
          AND STATUS IN ('PENDING','CONFIRMED','SHIPPED','DELIVERED')
    )

    SELECT *,
        CURRENT_TIMESTAMP()            AS _PROCESSED_AT,
        $bronze_schema || '.RAW_EXAMPLE' AS _SILVER_SOURCE
    FROM cleansed

) AS source
ON target.ORDER_ID = source.ORDER_ID   -- Match on Primary Key(s)

-- Update existing records
WHEN MATCHED THEN UPDATE SET
    target.CUSTOMER_ID    = source.CUSTOMER_ID,
    target.ORDER_DATE     = source.ORDER_DATE,
    target.AMOUNT         = source.AMOUNT,
    target.STATUS         = source.STATUS,
    target._PROCESSED_AT  = source._PROCESSED_AT,
    target._QUALITY_SCORE = source._QUALITY_SCORE,
    target._SILVER_SOURCE = source._SILVER_SOURCE

-- Insert new records
WHEN NOT MATCHED THEN INSERT (
    ORDER_ID, CUSTOMER_ID, ORDER_DATE, AMOUNT, STATUS,
    _PROCESSED_AT, _QUALITY_SCORE, _SILVER_SOURCE
)
VALUES (
    source.ORDER_ID, source.CUSTOMER_ID, source.ORDER_DATE,
    source.AMOUNT, source.STATUS,
    source._PROCESSED_AT, source._QUALITY_SCORE, source._SILVER_SOURCE
);

-- Step 3: Verify MERGE results
SELECT
    COUNT(*)                            AS total_records,
    AVG(_QUALITY_SCORE)                 AS avg_quality_score,
    MAX(_PROCESSED_AT)                  AS last_processed_at
FROM SILVER.{TABLE_NAME};
```

---

## ⚙️ Mandatory Requirements

### ✅ Deduplication (ALWAYS required):
- `ROW_NUMBER() OVER (PARTITION BY {PKs} ORDER BY _INGESTION_TIMESTAMP DESC)`
- Filter `_ROW_NUM = 1` (keep latest per PK)
- Filter NULL PKs **before** deduplication (inside the first CTE)

### ✅ MERGE Pattern:
- **`MERGE INTO target USING source ON condition`**
- **`WHEN MATCHED THEN UPDATE SET`**: Update all non-PK columns
- **`WHEN NOT MATCHED THEN INSERT`**: Insert full row
- NEVER use `DELETE` in Bronze→Silver merge

### ✅ Snowflake-specific Functions:
- `TRY_TO_NUMBER()` / `TRY_TO_DATE()` — safe casting (returns NULL on failure, no error)
- `ZEROIFNULL()` / `COALESCE()` — null-safe arithmetic
- `IFF(condition, true_val, false_val)` — concise conditional
- `UPPER(TRIM())` — text standardization

### ✅ Silver Audit Columns:
- `_PROCESSED_AT` → `CURRENT_TIMESTAMP()`
- `_QUALITY_SCORE` → Integer 0-100 (calculated per record)
- `_SILVER_SOURCE` → Source table name string

### ✅ PII Masking (if is_pii=true in metadata):
```sql
SHA2(EMAIL, 256) AS EMAIL,        -- Hash PII
'REDACTED'       AS PHONE_NUMBER  -- Or redact
```

---

## 🔍 Validation Checklist

- [ ] `CREATE TABLE IF NOT EXISTS` for idempotency
- [ ] CTEs used (not nested subqueries)
- [ ] `ROW_NUMBER() OVER (PARTITION BY PKs)` for deduplication
- [ ] NULL PKs filtered in first CTE
- [ ] Business rules applied in `cleansed` CTE
- [ ] `TRY_TO_*` safe casting functions used
- [ ] `MERGE INTO` with both MATCHED + NOT MATCHED clauses
- [ ] Silver audit columns present
- [ ] Verification SELECT at the end
- [ ] First line exactly `-- L2L MODERNIZATION TRACE: SILVER - <asset_name>`
- [ ] No object identifier contains `.SQL` as a table-name segment
- [ ] PII fields masked/hashed when `is_pii=true`
- [ ] SCD2 assets expire old versions and insert new current versions

---

## 🔄 Version History

- **v1.1.0** (2026-04-29): Added trace header, deploy-time variables, identifier sanitation, SCD2, and PII requirements.
- **v1.0.0** (2026-03-04): Initial Snowflake SQL Silver cartridge (native SQL MERGE pattern)

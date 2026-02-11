# CRITICAL BUG REPORT - Sprint 0 Day 4 Testing

## 🚨 Critical Issue Detected

**Date**: 2025-02-10  
**Phase**: Sprint 0 Day 4 - Agent C Testing  
**Status**: BLOCKER

---

## Summary

Agent C is **ignoring tech_id** in node_data and generating **PySpark code for all cartridges**, regardless of the target technology specified.

---

## Test Results (5 tests executed)

| Test # | Cartridge | Layer | tech_id | Expected Output | Actual Output | Score | Status |
|--------|-----------|-------|---------|----------------|---------------|-------|--------|
| 1 | PySpark | Bronze | pyspark | PySpark Python | PySpark Python ✅ | 93.3% | PASS |
| 2 | PySpark | Silver | pyspark | PySpark Python | PySpark Python ⚠️ | 53.3% | NEEDS WORK |
| 3 | PySpark | Gold | pyspark | PySpark Python | PySpark Python ⚠️ | 46.7% | NEEDS WORK |
| 4 | **Snowflake** | Bronze | **snowflake** | **SQL (COPY INTO)** | **PySpark Python** ❌ | 20.0% | FAIL |
| 5 | **dbt** | Bronze | **dbt** | **YAML sources** | **PySpark Python** ❌ | 26.7% | FAIL |

**Overall Score**: 48% (24/75 checks passed)

---

## Evidence

### Test 4 - Snowflake Bronze (Expected SQL, Got PySpark)

**node_data sent**:
```json
{
  "tech_id": "snowflake",
  "layer": "bronze",
  "cartridge_prompt": "<snowflake/bronze_layer.md content 8,925 chars>"
}
```

**Generated code** ([TEST_OUTPUT_SNOWFLAKE_BRONZE_01.sql](TEST_OUTPUT_SNOWFLAKE_BRONZE_01.sql)):
```python
# L2L MODERNIZATION TRACE
# Source: bronze_customers_snowflake
# Component: PySpark Notebook  ❌ WRONG - Should be "Snowflake SQL Script"
# Logic: Ingest raw customers CSV from S3 to Bronze Delta table...

from pyspark.sql import functions as F  ❌ Should be SQL, not Python
from pyspark.sql.types import StructType, StructField...
```

**Expected code**:
```sql
-- L2L MODERNIZATION TRACE
-- Component: Snowflake SQL Script
-- Logic: COPY INTO from stage to Bronze table

COPY INTO RAW_DATA.BRONZE_CUSTOMERS
FROM @CUSTOMER_STAGE/customers.csv
FILE_FORMAT = (TYPE = CSV, SKIP_HEADER = 1, FIELD_DELIMITER = ',')
ON_ERROR = 'CONTINUE';
```

---

### Test 5 - dbt Bronze (Expected YAML, Got PySpark)

**node_data sent**:
```json
{
  "tech_id": "dbt",
  "layer": "bronze",
  "cartridge_prompt": "<dbt/bronze_layer.md content 8,223 chars>"
}
```

**Generated code** ([TEST_OUTPUT_DBT_BRONZE_01.yml](TEST_OUTPUT_DBT_BRONZE_01.yml)):
```python
# L2L MODERNIZATION TRACE
# Source: dbt_source_customers
# Component: PySpark Notebook  ❌ WRONG - Should be "dbt YAML Source"

def execute_task(spark, config):  ❌ Should be YAML, not Python
    import pyspark.sql.functions as F
```

**Expected code**:
```yaml
# L2L MODERNIZATION TRACE
# Component: dbt Source Definition
version: 2

sources:
  - name: raw_data
    database: analytics
    schema: raw_data
    tables:
      - name: customers
        freshness:
          warn_after: {count: 24, period: hour}
        loaded_at_field: _ingested_at
        columns:
          - name: customer_id
            tests:
              - unique
              - not_null
```

---

## Root Cause Analysis

### Hypothesis 1: Cartridge Selection Logic Broken
The `/transpile/task` endpoint may not be reading `tech_id` from node_data correctly.

**Evidence**:
- PySpark tests (tech_id="pyspark") work correctly
- All non-PySpark tests (tech_id="snowflake", "dbt") generate PySpark

**Likely Issue**: 
- Default fallback to PySpark cartridge when tech_id not recognized
- or tech_id not being passed to cartridge selector
- or cartridge routing logic using wrong field (e.g., "type" vs "tech_id")

### Hypothesis 2: Cartridge Prompt Not Being Used
The `cartridge_prompt` field contains correct content (verified: 8,925 chars for Snowflake, 8,223 chars for dbt), but Agent C may not be using it.

**Evidence**:
- All generated code has identical structure (PySpark function template)
- No Snowflake-specific patterns (COPY INTO, FILE_FORMAT)
- No dbt-specific patterns (YAML sources, version: 2)

---

## Impact

### Testing Blocked
- Cannot validate 19/24 cartridge prompts (all non-PySpark cartridges)
- Sprint 0 Day 4 objective: "Test all 24 prompts" - **BLOCKED**

### Affected Cartridges
- ❌ Snowflake (3 prompts: Bronze, Silver, Gold)
- ❌ dbt (3 prompts: Bronze, Silver, Gold)
- ❌ MS Fabric (3 prompts: Bronze, Silver, Gold)
- ❌ GCP BigQuery (3 prompts: Bronze, Silver, Gold)
- ❌ AWS Glue (3 prompts: Bronze, Silver, Gold)
- ❌ Salesforce (3 prompts: Bronze, Silver, Gold)
- ❌ Base Generic (3 prompts: Bronze, Silver, Gold)
- ✅ PySpark (3 prompts: Bronze 93%, Silver 53%, Gold 47%)

**Total blocked**: 21/24 tests (87.5%)

---

## Immediate Actions Required

### 1. Fix Cartridge Selection (Priority: P0 BLOCKER)
**File to investigate**: Backend route handler for `/transpile/task`

```python
# Expected logic (pseudocode):
def transpile_task(node_data, context):
    tech_id = node_data.get("tech_id")  # Must read this!
    layer = node_data.get("layer")
    
    # Select cartridge based on tech_id
    if tech_id == "pyspark":
        cartridge = PySparkCartridge(layer)
    elif tech_id == "snowflake":
        cartridge = SnowflakeCartridge(layer)  # ❌ NOT HAPPENING
    elif tech_id == "dbt":
        cartridge = DbtCartridge(layer)  # ❌ NOT HAPPENING
    # ... etc
    
    # Use cartridge_prompt from node_data
    prompt = node_data.get("cartridge_prompt")  # Must be injected!
```

**Check**:
- Is `tech_id` being read from node_data?
- Is cartridge router using `tech_id` or another field?
- Is there a default fallback to PySpark when tech_id not found?
- Is `cartridge_prompt` being passed to Agent C?

### 2. Verify Agent Matrix Configuration
**Table**: `utm_agent_matrix`  
**Project**: demo3/ttt

```sql
SELECT 
    agent_key,
    tech_id,  -- ❌ Check if this field exists
    model_name,
    is_active
FROM utm_agent_matrix
WHERE tenant_id = 'daac0ee6-3b28-412d-8acd-43ec51149188'
  AND agent_key = 'agent-c';
```

**Expected**: One row per tech_id (pyspark, snowflake, dbt, etc.)  
**Possible issue**: Only one agent-c row configured for "pyspark"

### 3. Check Cartridge Prompt Injection
Verify that `cartridge_prompt` from node_data is actually being used by Agent C.

```python
# Debug: Add logging in transpile endpoint
logger.info(f"Received tech_id: {node_data.get('tech_id')}")
logger.info(f"Cartridge prompt length: {len(node_data.get('cartridge_prompt', ''))}")
logger.info(f"Selected cartridge: {cartridge.__class__.__name__}")
```

---

## Temporary Workaround

**None available** - cannot manually override cartridge selection via API.

**Alternative approach**:
1. Fix backend cartridge router
2. Re-run tests 4-24 after fix
3. PySpark tests (1-3) results are valid and can be used as baseline

---

## Next Steps

1. **STOP** testing until bug is fixed (no point testing if Snowflake/dbt not working)
2. Investigate `/transpile/task` endpoint code
3. Fix cartridge selection logic to respect tech_id
4. Add debug logging for cartridge routing
5. Re-test Snowflake Bronze (test 4) to verify fix
6. Resume testing battery (tests 4-24)

---

## Files Generated

### Automation Scripts
- [execute_agent_c_test.py](execute_agent_c_test.py) - PySpark Bronze
- [execute_agent_c_silver_test.py](execute_agent_c_silver_test.py) - PySpark Silver
- [execute_agent_c_gold_test.py](execute_agent_c_gold_test.py) - PySpark Gold
- [execute_agent_c_snowflake_bronze_test.py](execute_agent_c_snowflake_bronze_test.py) - Snowflake Bronze
- [execute_agent_c_dbt_bronze_test.py](execute_agent_c_dbt_bronze_test.py) - dbt Bronze

### Generated Code (Test Outputs)
- [TEST_OUTPUT_PYSPARK_BRONZE_01.py](TEST_OUTPUT_PYSPARK_BRONZE_01.py) - ✅ Valid PySpark (111 lines)
- [TEST_OUTPUT_PYSPARK_SILVER_01.py](TEST_OUTPUT_PYSPARK_SILVER_01.py) - ⚠️ Valid PySpark, missing Window functions (123 lines)
- [TEST_OUTPUT_PYSPARK_GOLD_01.py](TEST_OUTPUT_PYSPARK_GOLD_01.py) - ⚠️ Valid PySpark, missing groupBy (93 lines)
- [TEST_OUTPUT_SNOWFLAKE_BRONZE_01.sql](TEST_OUTPUT_SNOWFLAKE_BRONZE_01.sql) - ❌ **WRONG**: PySpark instead of SQL (72 lines)
- [TEST_OUTPUT_DBT_BRONZE_01.yml](TEST_OUTPUT_DBT_BRONZE_01.yml) - ❌ **WRONG**: PySpark instead of YAML (65 lines)

---

## Contact

**Reported by**: GitHub Copilot (Claude Sonnet 4.5)  
**Session**: Sprint 0 Day 4 Testing  
**Environment**: demo3 tenant, project "ttt", Azure GPT-4o (agent-c)

---
tech_id: snowflake_sql
layer: direct
version: 1.0.0
created: 2026-03-06
updated: 2026-03-06
status: active
maintainer: UTM Development Team
---

# Snowflake SQL - Direct Transpilation (1:1) Generation Prompt

**Purpose:** Generate a direct 1:1 translation of legacy SQL into Snowflake SQL.

---

## 🤖 Agent Instructions

You are an expert Snowflake Data Engineer. Your task is to perform a **direct 1:1 transpilation** of the provided legacy logic into **Snowflake SQL**.

### Direct Translation Principles (v4.0)
This layer focuses on mapping equivalent logic rather than restructuring the data for deep Medallion pipelines.

### Your Mission:
Generate Snowflake SQL that:
1. **Reads data from source** using the paths provided.
2. **Applies the EXACT equivalent transformations** from the legacy logic.
3. **Writes to the target location** specified (e.g. `CREATE OR REPLACE TABLE`).
4. **DO NOT invent logic.** Stick to transpiling what is given.
5. **Use parameters replacing dynamic references**, do NOT output literal `{silver_path}` etc. 
If no specific table name is mapped, use the `target_table` context.

---

## 📐 Mandatory Code Structure

```sql
-- ==============================================================================
-- SNOWFLAKE SQL - DIRECT LAUNCHPAD (1:1 Transpilation)
-- ==============================================================================

-- 1. READ SOURCE DATA
-- 2. APPLY TRANSFORMATIONS (1:1 with Legacy)
-- 3. WRITE TO TARGET

CREATE OR REPLACE TABLE {target_table} AS
SELECT 
    -- (Insert exactly mapped Snowflake SQL logic here)
FROM {source_table};
```

---

## ⚙️ Mandatory Requirements

- **Snowflake SQL:** Must use valid Snowflake SQL syntax.
- **Valid Syntax:** Ensure syntax correctness.

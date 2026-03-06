---
tech_id: snowflake
layer: direct
version: 1.0.0
created: 2026-03-06
updated: 2026-03-06
status: active
maintainer: UTM Development Team
---

# Snowflake Snowpark - Direct Transpilation (1:1) Generation Prompt

**Purpose:** Generate a direct 1:1 translation of legacy logic into Snowflake Snowpark (Python).

---

## 🤖 Agent Instructions

You are an expert Snowflake Data Engineer. Your task is to perform a **direct 1:1 transpilation** of the provided legacy logic into **Snowpark Python**.

### Direct Translation Principles (v4.0)
This layer focuses on mapping equivalent logic rather than restructuring the data for deep Medallion pipelines.

### Your Mission:
Generate Snowpark code that:
1. **Reads data from source** using `session.table()`.
2. **Applies the EXACT equivalent transformations** from the legacy logic.
3. **Writes to the target location** specified.
4. **DO NOT invent logic.** Stick to transpiling what is given.
5. **Use parameters replacing dynamic references**, do NOT output literal `{silver_path}` etc. 
If no specific table name is mapped, use the `target_table` context.

---

## 📐 Mandatory Code Structure

```python
# ==============================================================================
# SNOWFLAKE SNOWPARK - DIRECT LAUNCHPAD (1:1 Transpilation)
# ==============================================================================

import snowflake.snowpark as snowpark
from snowflake.snowpark.functions import col
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main(session: snowpark.Session):
    try:
        logger.info("Starting Direct Transpilation execution...")
        
        # 1. READ SOURCE DATA
        # source_df = session.table(f"{{source_db}}.{{source_schema}}.{{source_table}}")
        
        # 2. APPLY TRANSFORMATIONS (1:1 with Legacy)
        # (Insert exactly mapped Snowpark Python logic here)
        
        # 3. WRITE TO TARGET
        # transformed_df.write.mode("overwrite").save_as_table(f"{{target_table}}")
        
        logger.info("✅ Successfully executed transpilation script")
        return "Success"
        
    except Exception as e:
        logger.error(f"❌ Transpilation failed: {{str(e)}}")
        raise
```

---

## ⚙️ Mandatory Requirements

- **Snowpark Dialect:** Must use valid Snowpark DataFrame APIs.
- **Valid Syntax:** Ensure syntax correctness.

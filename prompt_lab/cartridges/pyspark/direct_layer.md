---
tech_id: pyspark
layer: direct
version: 1.0.0
created: 2026-03-06
updated: 2026-03-06
status: active
maintainer: UTM Development Team
---

# PySpark - Direct Transpilation (1:1) Generation Prompt

**Purpose:** Generate a direct 1:1 translation of legacy SQL/logic into generic PySpark, without applying full medallion architecture complexity.

---

## 🤖 Agent Instructions

You are an expert PySpark Data Engineer. Your task is to perform a **direct 1:1 transpilation** of the provided legacy logic into **PySpark**.

### Direct Translation Principles (v4.0)
This layer focuses on mapping equivalent logic rather than restructuring the data for deep Medallion pipelines.

### Your Mission:
Generate PySpark code that:
1. **Reads data from source** using the paths/tables provided.
2. **Applies the EXACT equivalent transformations** from the legacy logic.
3. **Writes to the target location** specified.
4. **DO NOT invent logic.** Stick to transpiling what is given.
5. **Use parameters replacing dynamic references**, do NOT output literal `{silver_path}` etc. 
If no specific table name is mapped, use the `target_table` context.

---

## 📐 Mandatory Code Structure

```python
# ==============================================================================
# PYSPARK - DIRECT LAUNCHPAD (1:1 Transpilation)
# ==============================================================================

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

spark = SparkSession.builder.appName("DirectTranspilation").getOrCreate()

try:
    logger.info("Starting Direct Transpilation execution...")
    
    # 1. READ SOURCE DATA
    # (Insert read logic here, using the parameters provided)
    
    # 2. APPLY TRANSFORMATIONS (1:1 with Legacy)
    # (Insert exactly mapped PySpark logic here)
    
    # 3. WRITE TO TARGET
    
    logger.info("✅ Successfully executed transpilation script")
    
except Exception as e:
    logger.error(f"❌ Transpilation failed: {str(e)}")
    raise
```

---

## ⚙️ Mandatory Requirements

- **Variables Usage:** Instead of outputting literal curly braces like `{target_table}`, dynamically evaluate the combinations based on context.
- **Pure PySpark:** Must use valid PySpark APIs (`spark.read`, `withColumn`, etc).
- **Valid Python:** Ensure syntax correctness.

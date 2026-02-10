---
tech_id: aws
layer: silver
version: 1.0.0
created: 2026-02-10
status: extracted_from_v39
---

# Aws - Silver Layer

**Extracted from:** v3.9 cartridge (hardcoded template)  
**Date:** 2026-02-10  
**Status:** Draft - Requires review and enhancement

---

## 🎯 Purpose

Glue Job for Silver Layer (Transformation).

---

## 📐 Code Pattern (Extracted from v3.9)

```python
# AWS GLUE - SILVER LAYER
# Source: {...}

import sys
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from glue_config import Config

glueContext = GlueContext(SparkContext())
spark = glueContext.spark_session

# Read Bronze
df_bronze = spark.read.parquet(f"{Config.PATH_BRONZE}/{...}")

# [TRANSFORMATIONS / DEDUPE]
df_silver = df_bronze.dropDuplicates()

# Write to Silver (S3)
target_path = f"{Config.PATH_SILVER}/{...}"
df_silver.write.mode("overwrite").parquet(target_path)
```

---

## ⚠️ Migration Notes

**This prompt was auto-extracted from v3.9 hardcoded template.**

### TODO for v4.0:
- [ ] Review and enhance description
- [ ] Add examples and best practices
- [ ] Define mandatory requirements
- [ ] Add error handling guidelines
- [ ] Document performance considerations
- [ ] Add validation rules
- [ ] Test with Agent C

### Changes from v3.9:
- Converted from hardcoded Python to markdown prompt
- Needs AI agent instructions added
- Requires context variables documentation

---

## 📝 Version History

- **v1.0.0** (2026-02-10): Extracted from v3.9 cartridge

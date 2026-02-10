---
tech_id: aws
layer: gold
version: 1.0.0
created: 2026-02-10
status: extracted_from_v39
---

# Aws - Gold Layer

**Extracted from:** v3.9 cartridge (hardcoded template)  
**Date:** 2026-02-10  
**Status:** Draft - Requires review and enhancement

---

## 🎯 Purpose

Glue Job to load Redshift (Gold Layer).

---

## 📐 Code Pattern (Extracted from v3.9)

```python
# AWS GLUE - GOLD LAYER (Load to Redshift)
# Target: {...}

from glue_config import Config
from glue_utils import write_to_redshift, get_glue_context

glueContext = get_glue_context()
spark = glueContext.spark_session

# Read Silver
df_silver = spark.read.parquet(f"{Config.PATH_SILVER}/{...}")

# Business Logic
df_gold = df_silver.select("*")

# Write to Redshift
write_to_redshift(df_gold, "public." + "{...}", Config)
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

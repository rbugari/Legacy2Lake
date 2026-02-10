---
tech_id: ms_fabric
layer: silver
version: 1.0.0
created: 2026-02-10
status: extracted_from_v39
---

# Ms_Fabric - Silver Layer

**Extracted from:** v3.9 cartridge (hardcoded template)  
**Date:** 2026-02-10  
**Status:** Draft - Requires review and enhancement

---

## 🎯 Purpose

Generate silver layer code for ms_fabric

---

## 📐 Code Pattern (Extracted from v3.9)

```python
# MS FABRIC - SILVER LAYER (Notebook)
# Data Cleaning & Standardization
# Primary Keys: {...}

from fabric_config import Config

# Read from Bronze
df_raw = spark.read.table(f"{Config.LAKEHOUSE_BRONZE}.{...}")

# Basic Deduplication
df_silver = df_raw.dropDuplicates({...})

# Upsert into Silver using Delta Merge
target_table = f"{Config.LAKEHOUSE_SILVER}.{...}"

from delta.tables import DeltaTable

if spark.catalog.tableExists(target_table):
    dt = DeltaTable.forName(spark, target_table)
    dt.alias("target").merge(
        df_silver.alias("source"),
        "{...}"
    ).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
else:
    df_silver.write.format("delta").mode("overwrite").saveAsTable(target_table)

print(f"Silver Layer updated: {target_table}")
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

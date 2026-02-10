---
tech_id: ms_fabric
layer: gold
version: 1.0.0
created: 2026-02-10
status: extracted_from_v39
---

# Ms_Fabric - Gold Layer

**Extracted from:** v3.9 cartridge (hardcoded template)  
**Date:** 2026-02-10  
**Status:** Draft - Requires review and enhancement

---

## 🎯 Purpose

Generate gold layer code for ms_fabric

---

## 📐 Code Pattern (Extracted from v3.9)

```python
# MS FABRIC - GOLD LAYER (Semantic View)
# Business-ready data for Power BI / Reporting

from fabric_config import Config

# Read from Silver
df_silver = spark.read.table(f"{Config.LAKEHOUSE_SILVER}.{...}")

# Project Gold Logic (can be customized via prompt)
df_gold = df_silver.select("*")

# Write to Gold Lakehouse
target_table = f"{Config.LAKEHOUSE_GOLD}.{...}"
df_gold.write.format("delta").mode("overwrite").saveAsTable(target_table)

print(f"Gold Layer updated: {target_table}")
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

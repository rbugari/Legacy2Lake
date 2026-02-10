---
tech_id: ms_fabric
layer: bronze
version: 1.0.0
created: 2026-02-10
status: extracted_from_v39
---

# Ms_Fabric - Bronze Layer

**Extracted from:** v3.9 cartridge (hardcoded template)  
**Date:** 2026-02-10  
**Status:** Draft - Requires review and enhancement

---

## 🎯 Purpose

Generate bronze layer code for ms_fabric

---

## 📐 Code Pattern (Extracted from v3.9)

```python
# MS FABRIC - BRONZE LAYER (Notebook)
# Generated for Microsoft Fabric Lakehouse integration
# Source: {...}

from fabric_config import Config
from fabric_utils import add_audit_columns

# [LOAD RAW DATA]
{...}

# Check if df exists (adapting from legacy logic)
if 'df' not in locals() and 'df_source' in locals():
    df = df_source

# Apply Fabric Bronze Standard
df_bronze = add_audit_columns(df)

# Save to Lakehouse Tables
target_table = f"{Config.LAKEHOUSE_BRONZE}.{...}"
df_bronze.write.format("delta").mode("append").saveAsTable(target_table)

print(f"Ingested to Bronze: {target_table}")
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

---
tech_id: sf
layer: silver
version: 1.0.0
created: 2026-02-10
status: extracted_from_v39
---

# Sf - Silver Layer

**Extracted from:** v3.9 cartridge (hardcoded template)  
**Date:** 2026-02-10  
**Status:** Draft - Requires review and enhancement

---

## 🎯 Purpose

Generates Data Cloud SQL for Transforms (Calculated Insights / Batch).

---

## 📐 Code Pattern (Extracted from v3.9)

```python
-- SALESFORCE DATA CLOUD (TRANSFORM)
-- Target DLO/DMO: {...}

SELECT 
    source.id,
    source.amount,
    CURRENT_TIMESTAMP() as _processed_at
FROM bronze_{...} source
WHERE source.amount IS NOT NULL
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

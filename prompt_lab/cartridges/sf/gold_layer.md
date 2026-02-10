---
tech_id: sf
layer: gold
version: 1.0.0
created: 2026-02-10
status: extracted_from_v39
---

# Sf - Gold Layer

**Extracted from:** v3.9 cartridge (hardcoded template)  
**Date:** 2026-02-10  
**Status:** Draft - Requires review and enhancement

---

## 🎯 Purpose

Generates Data Cloud SQL for Business Layer.

---

## 📐 Code Pattern (Extracted from v3.9)

```python
-- SALESFORCE DATA CLOUD (GOLD/INSIGHT)
-- Insight: {...}

SELECT 
    custId,
    SUM(amount) as total_revenue
FROM silver_{...}
GROUP BY 1
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

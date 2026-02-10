# Technology Cartridges

**Layer 2:** Technology-specific generation prompts

---

## 📦 Cartridges

Each cartridge contains prompts for generating code for a specific target technology.

### Extraction Status (Sprint 0)

| Technology | Status | Prompts | Notes |
|-----------|--------|---------|-------|
| **pyspark** | 🔄 To extract | Bronze, Silver, Gold | Databricks/Spark |
| **snowflake** | 🔄 To extract | Bronze, Silver, Gold | Snowpark + SQL |
| **dbt** | 🔄 To extract | Staging, Intermediate, Marts | SQL + YAML |
| **fabric** | 🔄 To extract | Notebooks | Microsoft Fabric |
| **gcp** | 🔄 To extract | BigQuery, Dataflow | Google Cloud |
| **aws** | 🔄 To extract | Glue, Redshift | Amazon Web Services |
| **sf** | 🔄 To extract | Data Cloud | Salesforce |

---

## 🚀 Extraction

To populate this directory, run:

```powershell
# Extract all cartridges
python scripts/extract_prompts_v39.py

# Extract specific cartridge
python scripts/extract_prompts_v39.py pyspark
```

This will create:
```
cartridges/
├── pyspark/
│   ├── bronze_layer.md
│   ├── silver_layer.md
│   ├── gold_layer.md
│   └── README.md
├── snowflake/
│   └── ...
└── ...
```

---

## 📋 Cartridge Structure

Each cartridge directory should contain:
- `README.md` - Overview and metadata
- `<layer>_layer.md` - Layer-specific prompts
- `examples/` (optional) - Example outputs

---

## 🔄 Current Status

**Feb 10, 2026:** Directory created, awaiting extraction

**Next Steps:**
1. Run extraction script
2. Review extracted prompts
3. Enhance with Agent instructions
4. Add examples

---

**Owner:** Data Engineering Team  
**Status:** Sprint 0 - Foundation

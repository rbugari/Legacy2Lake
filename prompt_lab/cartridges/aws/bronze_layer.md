---
tech_id: aws
layer: bronze
version: 1.0.0
created: 2026-02-10
status: extracted_from_v39
---

# Aws - Bronze Layer

**Extracted from:** v3.9 cartridge (hardcoded template)  
**Date:** 2026-02-10  
**Status:** Draft - Requires review and enhancement

---

## 🎯 Purpose

Glue Job for Bronze Layer (Ingestion).

---

## 📐 Code Pattern (Extracted from v3.9)

```python
# AWS GLUE - BRONZE LAYER
# Source: {...}

import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from glue_config import Config

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
args = getResolvedOptions(sys.argv, ['JOB_NAME'])
job.init(args['JOB_NAME'], args)

# [SOURCE LOGIC FROM MIGRATION]
# Assumes 'df' is created here
{...}

# Write to S3 (Bronze / Parquet)
target_path = f"{Config.PATH_BRONZE}/{...}"
if 'df' in locals():
    df.write.mode("append").parquet(target_path)

job.commit()
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

# 🚀 Quick Start - Sprint 0 (Day 2+)

**Your Current Position:** Day 1 Complete ✅  
**Next Steps:** Review and enhance prompts  
**Timeline:** Feb 11-17

---

## ✅ WHAT'S DONE (Day 1)

```powershell
✅ 4 utility scripts created in scripts/
✅ 24 prompts extracted to prompt_lab/cartridges/
✅ Strategic plan documented
✅ All tested and working
```

---

## 🎯 WHAT'S NEXT (Day 2-3)

### Your Mission:
> **Transform extracted prompts from hardcoded templates into intelligent AI instructions**

---

## 📋 STEP-BY-STEP GUIDE

### **Step 1: Pick a Cartridge to Enhance** (Choose one)

```powershell
# Option A: Start with PySpark (most important)
code prompt_lab/cartridges/pyspark/bronze_layer.md

# Option B: Start with Snowflake
code prompt_lab/cartridges/snowflake/bronze_layer.md

# Option C: Start with dbt
code prompt_lab/cartridges/dbt/bronze_layer.md
```

**Recommendation:** Start with **PySpark** (most used)

---

### **Step 2: Review Current State**

Open the file and you'll see:

```markdown
---
tech_id: pyspark
layer: bronze
version: 1.0.0
status: extracted_from_v39      ← Needs enhancement
---

## 🎯 Purpose
Generate bronze layer code for pyspark    ← Too generic

## 📐 Code Pattern
[hardcoded template]                      ← Raw extract

## ⚠️ Migration Notes
TODO for v4.0:                            ← Your tasks
- [ ] Review and enhance description
- [ ] Add examples
- etc...
```

---

### **Step 3: Enhance the Prompt**

Transform it into this structure:

```markdown
---
tech_id: pyspark
layer: bronze
version: 2.0.0                  ← Bump version
status: active                  ← Change status
maintainer: Your Name
updated: 2026-02-11
---

# PySpark - Bronze Layer Generation Prompt

**Purpose:** Generate production-ready PySpark code for Bronze (raw ingestion) layer

---

## 🤖 Agent Instructions

You are a Senior PySpark Data Engineer. Generate code that:

1. **Reads data from source** using appropriate format
2. **Adds mandatory metadata columns**:
   - `_ingestion_timestamp` (current_timestamp)
   - `_ingestion_date` (current_date)
   - `_source_file` (input_file_name)
   - `_source_system` (literal string)

3. **Writes to Delta Lake** with:
   - Format: `delta`
   - Mode: `append`
   - Partition: by `_ingestion_date`
   - Options: `mergeSchema=true`, `dataChange=true`

4. **Includes error handling** (try/except blocks)
5. **Includes logging** (logger statements)
6. **Validates data** (assertions)

---

## 📐 Code Structure (MANDATORY)

```python
# 1. IMPORTS
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    current_timestamp, current_date, 
    input_file_name, lit
)
from delta.tables import DeltaTable

# 2. SPARK SESSION
spark = SparkSession.builder...

# 3. READ SOURCE
df_source = spark.read...

# 4. ADD METADATA
df_bronze = df_source \
    .withColumn("_ingestion_timestamp", current_timestamp()) \
    .withColumn("_ingestion_date", current_date()) \
    .withColumn("_source_file", input_file_name()) \
    .withColumn("_source_system", lit("SOURCE_NAME"))

# 5. WRITE TO DELTA
df_bronze.write \
    .format("delta") \
    .mode("append") \
    .partitionBy("_ingestion_date") \
    .saveAsTable(target_table)

# 6. VALIDATION
assert df_bronze.count() > 0, "No data ingested"
```

---

## ⚙️ Mandatory Requirements

- [ ] All 4 metadata columns present
- [ ] Delta Lake format used
- [ ] Partition by `_ingestion_date`
- [ ] Error handling implemented
- [ ] Logging statements included
- [ ] Schema evolution enabled (`mergeSchema=true`)

---

## ✅ Validation Checklist

Generated code MUST:
- ✅ Be syntactically valid Python
- ✅ Import all required modules
- ✅ Create SparkSession properly
- ✅ Include all 4 metadata columns
- ✅ Use Delta Lake format
- ✅ Partition correctly
- ✅ Handle errors gracefully
- ✅ Log execution steps

---

## 📚 Examples

### Good Output:
[Include example of perfect code]

### Common Mistakes to Avoid:
- ❌ Missing metadata columns
- ❌ Using `overwrite` instead of `append`
- ❌ No error handling
- ❌ No logging

---

## 🔄 Version History

- **v2.0.0** (2026-02-11): Enhanced with Agent instructions
- **v1.0.0** (2026-02-10): Extracted from v3.9
```

---

### **Step 4: Save and Review**

```powershell
# Save the file in VSCode (Ctrl+S)

# Review it
cat prompt_lab/cartridges/pyspark/bronze_layer.md
```

---

### **Step 5: Commit Your Changes**

```powershell
# Commit the enhanced prompt
python scripts/git_helper.py commit "Enhanced PySpark bronze_layer prompt with Agent instructions"

# Check status
python scripts/git_helper.py status
```

---

### **Step 6: Repeat for Other Layers**

```powershell
# Enhance silver layer
code prompt_lab/cartridges/pyspark/silver_layer.md
# [Follow same structure as bronze]

# Enhance gold layer  
code prompt_lab/cartridges/pyspark/gold_layer.md
# [Follow same structure as bronze]

# Commit each one
python scripts/git_helper.py commit "Enhanced PySpark silver_layer"
python scripts/git_helper.py commit "Enhanced PySpark gold_layer"
```

---

### **Step 7: Move to Next Cartridge**

```powershell
# PySpark done? Move to Snowflake
code prompt_lab/cartridges/snowflake/bronze_layer.md
# [Repeat enhancement process]

# Then dbt, then ms_fabric, etc...
```

---

## 📊 DAILY GOALS

### Day 2 (Feb 11):
- [ ] Enhance **PySpark** (3 prompts: bronze, silver, gold)
- [ ] Enhance **Snowflake** (3 prompts)
- **Goal:** 6 prompts enhanced

### Day 3 (Feb 12):
- [ ] Enhance **dbt** (3 prompts)
- [ ] Enhance **MS Fabric** (3 prompts)
- [ ] Enhance **GCP** (3 prompts)
- **Goal:** 9 prompts enhanced

### Day 4 (Feb 13):
- [ ] Enhance **AWS** (3 prompts)
- [ ] Enhance **Salesforce** (3 prompts)
- [ ] Review all 24 prompts
- **Goal:** 6 prompts + full review

### Day 5-7 (Feb 14-17):
- [ ] Design DB schema
- [ ] Create migrations
- [ ] Add examples
- [ ] Final polish

---

## 🎨 ENHANCEMENT TEMPLATE

Use this checklist for each prompt:

```markdown
Enhancement Checklist for [tech_id]/[layer]:

- [ ] Updated frontmatter (version, status, maintainer, date)
- [ ] Clear purpose statement
- [ ] Detailed Agent instructions
- [ ] Mandatory code structure documented
- [ ] Required elements listed
- [ ] Validation checklist added
- [ ] Examples provided
- [ ] Common mistakes documented
- [ ] Version history updated
- [ ] Committed to Git
```

---

## 🛠️ USEFUL COMMANDS

```powershell
# View a prompt
cat prompt_lab/cartridges/pyspark/bronze_layer.md

# Edit a prompt
code prompt_lab/cartridges/pyspark/bronze_layer.md

# Check Git status
python scripts/git_helper.py status

# Commit changes
python scripts/git_helper.py commit "Your message"

# View commit history
python scripts/git_helper.py history cartridges/pyspark/bronze_layer.md

# List all prompts
dir prompt_lab/cartridges/*/bronze_layer.md

# Count prompts
(dir prompt_lab/cartridges/*/*.md -Exclude README.md).Count
```

---

## 📚 REFERENCES

While enhancing, refer to:

1. **Original cartridge code:**
   ```powershell
   code apps/api/services/refinement/cartridges/pyspark_cartridge.py
   ```

2. **Agent C code (for context):**
   ```powershell
   code apps/api/services/agent_c_service.py
   ```

3. **Existing documentation:**
   ```powershell
   code docs/planning/future_v4.0.md
   ```

---

## 🎯 SUCCESS CRITERIA

By end of Day 3, you should have:

- [ ] **24 prompts reviewed**
- [ ] **24 prompts enhanced** (Agent instructions, examples, validation)
- [ ] **24 Git commits** (one per prompt change)
- [ ] **0 extraction artifacts** (all TODOs addressed)

---

## 🚨 NEED HELP?

### If stuck on prompt format:
→ Look at [future_v4.0.md](docs/planning/future_v4.0.md) lines 400-700  
   (Has a complete example of a well-structured prompt)

### If unsure about Agent instructions:
→ Think: "What would I tell a junior developer to generate this code?"  
   Write that in plain English

### If need validation ideas:
→ Look at `scripts/validate_generated_code.py`  
   It shows what checks we'll run on generated code

---

## 💡 TIPS

1. **Don't overthink it** - Start simple, iterate later
2. **Copy structure** - Use the template, fill in details
3. **Commit often** - One commit per prompt is fine
4. **Test early** - Try explaining your prompt to ChatGPT/Claude
5. **Ask for examples** - Look at existing generated code in `output/`

---

## ⏰ TIME ESTIMATES

- **Reviewing 1 prompt:** 5 minutes
- **Enhancing 1 prompt:** 15-20 minutes
- **Committing:** 2 minutes

**Total per prompt:** ~25 minutes  
**Total for 24 prompts:** ~10 hours

**Spread over 3 days:** ~3-4 hours/day (comfortable pace)

---

## 🎬 START NOW

**Your next command should be:**

```powershell
# Open the first prompt to enhance
code prompt_lab/cartridges/pyspark/bronze_layer.md
```

**Then:**
1. Read the extracted content
2. Add Agent instructions
3. Add examples
4. Save
5. Commit
6. Next prompt

---

## 📈 TRACK PROGRESS

Create a checklist file:

```powershell
# Create progress tracker
echo "# Prompt Enhancement Progress" > ENHANCEMENT_PROGRESS.md
echo "" >> ENHANCEMENT_PROGRESS.md
echo "## Day 2 (Feb 11)" >> ENHANCEMENT_PROGRESS.md
echo "- [ ] pyspark/bronze_layer.md" >> ENHANCEMENT_PROGRESS.md
echo "- [ ] pyspark/silver_layer.md" >> ENHANCEMENT_PROGRESS.md
echo "- [ ] pyspark/gold_layer.md" >> ENHANCEMENT_PROGRESS.md
# etc...

# Edit as you go
code ENHANCEMENT_PROGRESS.md
```

---

**Ready? Let's enhance some prompts!** 🚀  

**First target:** [pyspark/bronze_layer.md](prompt_lab/cartridges/pyspark/bronze_layer.md)

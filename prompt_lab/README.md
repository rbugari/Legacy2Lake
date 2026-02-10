# Prompt Laboratory

**Status:** Sprint 0 - Foundation  
**Version:** 4.0.0  
**Created:** 2026-02-10

---

## 🎯 Purpose

This directory contains the **single source of truth** for all AI prompts used in Legacy2Lake v4.0.

### Three-Layer Architecture:

```
Layer 1: agents/          → Base agent roles and instructions
Layer 2: cartridges/      → Technology-specific generation prompts
Layer 3: [Database]       → Tenant/project overrides (runtime)
```

---

## 📁 Directory Structure

```
prompt_lab/
├── agents/                    # Layer 1: Base Agent Prompts
│   ├── agent_a_base.md       # Detective/Analyst (Discovery)
│   ├── agent_c_base.md       # Code Generator (Refinement)
│   ├── agent_f_base.md       # Compliance Auditor (Certification)
│   └── agent_g_base.md       # Governance Reporter
│
├── cartridges/                # Layer 2: Tech-Specific Prompts
│   ├── pyspark/
│   │   ├── spec.md           # Metadata and configuration
│   │   ├── bronze_layer.md   # Bronze generation prompt
│   │   ├── silver_layer.md   # Silver generation prompt
│   │   ├── gold_layer.md     # Gold generation prompt
│   │   ├── examples/
│   │   └── README.md
│   │
│   ├── snowflake/
│   ├── dbt/
│   ├── fabric/
│   ├── gcp/
│   ├── aws/
│   └── sf/
│
└── examples/                  # Reference examples
    └── successful_generations/
```

---

## 🔄 Workflow

### 1. **Create/Edit Prompts** (Filesystem)
```powershell
# Edit prompts in VSCode
code prompt_lab/cartridges/pyspark/bronze_layer.md
```

### 2. **Sync to Database**
```powershell
# Sync filesystem → database
python scripts/sync_prompts.py

# Check status
python scripts/sync_prompts.py status
```

### 3. **Version Control**
```powershell
# Commit changes
python scripts/git_helper.py commit "Enhanced PySpark bronze prompt"

# View history
python scripts/git_helper.py history cartridges/pyspark/bronze_layer.md
```

### 4. **Use in Generation**
Prompts are automatically loaded from database by Agent C during code generation.

---

## 📋 Prompt Format

All prompts should follow this structure:

```markdown
---
tech_id: pyspark
layer: bronze
version: 2.1.0
created: 2026-02-10
updated: 2026-02-10
maintainer: Data Engineering Team
status: active
---

# Title

**Purpose:** Brief description

---

## 🎯 Objective

What this prompt generates

---

## 🤖 Agent Instructions

Detailed instructions for Agent C

---

## 📐 Code Pattern

Example code structure

---

## ⚙️ Requirements

Mandatory requirements

---

## 🔄 Version History

Change log
```

---

## 🚀 Getting Started (Sprint 0)

### Step 1: Extract Existing Prompts
```powershell
# Extract hardcoded templates from v3.9
python scripts/extract_prompts_v39.py
```

This will populate `prompt_lab/cartridges/` with initial prompts.

### Step 2: Review and Enhance
```powershell
# Review extracted prompts
cd prompt_lab/cartridges
dir

# Edit each prompt to add:
# - Detailed agent instructions
# - Examples
# - Best practices
# - Validation rules
```

### Step 3: Sync to Database (after v4.0 Sprint 1)
```powershell
# Once utm_system_prompts table is created
python scripts/sync_prompts.py
```

---

## 📚 Documentation

- **[RELEASE_STRATEGY_v4.0.md](../docs/planning/RELEASE_STRATEGY_v4.0.md)** - Overall v4.0 plan
- **[TOOLING_v4.0.md](../docs/planning/TOOLING_v4.0.md)** - Tooling strategy
- **[future_v4.0.md](../docs/planning/future_v4.0.md)** - Detailed v4.0 vision
- **[scripts/README.md](../scripts/README.md)** - Script usage guide

---

## 🎯 Current Status

**Sprint 0 (Feb 10-17, 2026):**
- [x] Directory structure created
- [ ] Extract prompts from v3.9
- [ ] Review and enhance prompts
- [ ] Database schema designed
- [ ] Initial sync tested

**Next: Sprint v4.0 (Feb 17-Mar 3):**
- Create `utm_system_prompts` table
- Implement `PromptSyncService`
- Full bidirectional sync working

---

## 🔐 Conventions

### File Naming
- Agent prompts: `agent_X_base.md` (e.g., `agent_c_base.md`)
- Layer prompts: `<layer>_layer.md` (e.g., `bronze_layer.md`)
- Always lowercase with underscores

### Tech IDs
- Use consistent tech_id values:
  - `pyspark` (not PySpark or py_spark)
  - `snowflake` (not Snowflake)
  - `dbt` (not DBT)
  - `fabric` (not ms_fabric)

### Layers
- Standard layers: `bronze`, `silver`, `gold`
- dbt layers: `staging`, `intermediate`, `marts`

---

## ⚠️ Important Notes

### DO:
- ✅ Edit prompts in `prompt_lab/` (filesystem)
- ✅ Sync after changes with `sync_prompts.py`
- ✅ Commit to Git regularly
- ✅ Add examples and best practices
- ✅ Document version changes

### DON'T:
- ❌ Edit prompts directly in database (use UI in v4.4)
- ❌ Hardcode templates in Python code
- ❌ Skip sync after editing
- ❌ Delete files without Git commit
- ❌ Mix tech_id naming conventions

---

## 🤝 Contributing

To add a new technology:

1. **Create directory:**
   ```powershell
   mkdir prompt_lab/cartridges/new_tech
   ```

2. **Create layer prompts:**
   - `bronze_layer.md`
   - `silver_layer.md`
   - `gold_layer.md`

3. **Create README:**
   - `README.md` with tech overview

4. **Sync and commit:**
   ```powershell
   python scripts/sync_prompts.py
   python scripts/git_helper.py commit "Add new_tech cartridge"
   ```

---

**Owner:** Development Team  
**Maintainer:** Data Engineering Team  
**Last Updated:** 2026-02-10  
**Status:** Active Development

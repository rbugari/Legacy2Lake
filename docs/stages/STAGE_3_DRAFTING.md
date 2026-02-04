# Stage 3: Drafting (Architectural Planning & IR Generation)

## 📌 Overview
**Drafting** transforms scoped requirements into a **Universal Intermediate Representation (IR)** - a platform-agnostic JSON blueprint that captures business intent without legacy syntax. This enables multi-cloud deployment without re-analyzing source artifacts.

> **v3.5 Update**: Dynamic **knowledge injection** based on detected source/target technologies. Agent C receives tech-specific prompts from the Prompt Laboratory.

## 🎯 Objectives
- **IR Normalization**: Extract business logic from legacy syntax into universal JSON schema
- **Knowledge Injection**: Load source/target technology prompts (e.g., T-SQL → PySpark)
- **Cartridge Selection**: Choose appropriate code generator based on target platform
- **Design Registry**: Apply naming conventions and architectural patterns
- **Logical Steps**: Generate step-by-step execution plan stored in `utm_logical_steps`

## 👨‍💻 User Guide

### 1. Pre-Drafting Configuration

**Verify Technology Stack**:
- **Source**: Confirmed by Agent S in Triage (e.g., "SQL Server 2019 + SSIS")
- **Target**: Selected by user (e.g., "Databricks with PySpark")

**Design Registry (Optional)**:
- **Naming Conventions**: Prefix/suffix rules (e.g., `tbl_`, `_fact`)
- **Architectural Patterns**: Medallion (Bronze/Silver/Gold), Lambda, Kappa
- **Partitioning Strategy**: Default partition keys from forensics

Navigate to **"Intelligence Configuration"** to review or customize.

### 2. Run Drafting Pipeline

1. **Click "Generate Plan"**: Initiates Agent C (Interpreter) in IR mode
2. **Knowledge Loading**: System automatically:
   - Loads `origins/sqlserver/prompt_v1.md` (source patterns)
   - Loads `destinations/databricks/config_v1.json` (target instructions)
   - Injects tech-specific dialect rules into Agent C context
3. **IR Generation**: For each CORE asset:
   - Parse legacy syntax (T-SQL, SSIS XML, etc.)
   - Extract **business intent** (what, not how)
   - Generate normalized JSON IR
   - Store in `utm_logical_steps` table

### 3. Review Logical Plan

**Drafting Output Explorer** (v3.6 UI Update):
- **Resizable Split Pane**: Drag the border between file tree and code preview to adjust widths
- **Tree Toggle**: Click the "Panel" button to show/hide the file tree for maximum preview space
- **Persistent Layout**: Your preferred tree width and visibility are saved per project
- **Logical Steps View**: Browse generated IR for each asset
- **Dependency Graph**: Visual representation of execution order
- **Schema Reference**: Target DDL organized by layer (Bronze → Silver → Gold)
- **Complexity Metrics**: Lines of code, cyclomatic complexity, risk score

**IR Structure Example** (Stored Procedure → Logical Step):
```json
{
  "step_id": "uuid",
  "step_type": "DATA_TRANSFORMATION",
  "source_asset": "sp_LoadDimCustomer.sql",
  "business_intent": "Upsert customer dimension with SCD Type 2",
  "logical_operations": [
    {
      "operation": "READ",
      "source": "staging.customers",
      "columns": ["customer_id", "name", "email", "modified_date"]
    },
    {
      "operation": "LOOKUP",
      "target": "dim.customers",
      "join_key": "customer_id",
      "scd_type": 2
    },
    {
      "operation": "MERGE",
      "target": "dim.customers",
      "match_condition": "src.customer_id = tgt.customer_id",
      "when_matched": "UPDATE SET current_flag = 0, end_date = CURRENT_DATE",
      "when_not_matched": "INSERT VALUES (...)"
    }
  ],
  "metadata": {
    "partition_key": "modified_date",
    "pii_fields": ["email"],
    "volume": "MEDIUM"
  }
}
```

### 4. Validation and Approval

- **Review**: Check that business logic was extracted correctly
- **Override**: Edit IR directly if Agent C missed nuances  
- **Approve**: Lock the plan to proceed to Refinement (code generation)

## ⚙️ Technical Details

### Services
- **LibrarianService**: Coordinates artifact reading from R2
- **AgentCService**: Interpreter for IR normalization
- **PromptService**: Loads technology-specific prompts dynamically
- **PersistenceService**: Stores IR in Supabase

### Database Tables

1. **utm_logical_steps**: Universal IR storage
   ```sql
   {
     step_id: uuid,
     project_id: uuid,
     tenant_id: uuid,
     source_object_id: uuid,        -- References utm_objects
     step_type: "EXTRACT | TRANSFORM | LOAD",
     step_order: integer,
     logical_operations: jsonb,      -- The IR
     dependencies: jsonb,            -- ["step_id_1", "step_id_2"]
     metadata: jsonb,
     created_at: timestamp
   }
   ```

2. **utm_design_registry**: Architectural patterns (future)
   ```sql
   {
     registry_id: uuid,
     pattern_type: "NAMING | STRUCTURE | OPTIMIZATION",
     rules: jsonb
   }
   ```

### Knowledge Injection Pattern (v3.5)

**Dynamic Prompt Assembly**:
```python
# 1. Load base Agent C prompt
base_prompt = load_prompt("core_agents/agent_c_interpreter/prompt_v1.md")

# 2. Inject source knowledge
source_tech = project.settings['source_tech']  # "SQLSERVER"
source_config = load_config(f"origins/{source_tech}/config_v1.json")
source_instruction = source_config['dialect_instruction']

# 3. Inject destination knowledge
target_tech = project.settings['target_tech']  # "DATABRICKS"
target_config = load_config(f"destinations/{target_tech}/config_v1.json")
target_instruction = target_config['dialect_instruction']

# 4. Assemble final prompt
full_prompt = f"""
{base_prompt}

SOURCE CONTEXT:
{source_instruction}
- Legacy patterns: {source_config['legacy_patterns']}
- Common pitfalls: {source_config['migration_notes']}

TARGET CONTEXT:
{target_instruction}
- Best practices: {target_config['best_practices']}
- Code templates: {target_config['templates']}
"""
```

### Cartridge Pre-Selection

Based on target technology, the appropriate **output cartridge** is identified:
- **Databricks** → `DatabricksCartridge` (PySpark notebooks)
- **Snowflake** → `SnowflakeCartridge` (SQL scripts with tasks)
- **Fabric** → `FabricCartridge` (Notebooks + Pipelines)
- **BigQuery** → `BigQueryCartridge` (SQL procedures)

Cartridges are **not executed** in Drafting - they're prepared for Stage 4 (Refinement).

### IR Normalization (v3.5)

**Philosophy**: Separate **what** from **how**.

Legacy syntax (how):
```sql
-- T-SQL specific
MERGE INTO dim_customer AS target
USING staging_customer AS source
ON target.customer_id = source.customer_id
WHEN MATCHED AND source.modified_date > target.modified_date
THEN UPDATE SET ...
```

Universal IR (what):
```json
{
  "operation": "UPSERT",
  "source": "staging_customer",
  "target": "dim_customer",
  "match_key": "customer_id",
  "update_condition": "source.modified_date > target.modified_date",
  "scd_type": 1
}
```

**Benefits**:
- Same IR can generate **PySpark**, **Snowflake SQL**, or **BigQuery**
- Business logic is preserved across cloud migrations
- No need to re-parse legacy artifacts when changing targets

---

> [!TIP]
> **Optimization Tip**: If Agent C produces overly complex IR, use the "Simplify" button to ask Agent F (Critic) to refactor the logic before code generation.

> [!IMPORTANT]
> **IR is Persistent**: Once approved, the IR is locked. Future stages (Refinement, Certification) use this IR, not the original legacy files. This ensures consistency across regenerations.

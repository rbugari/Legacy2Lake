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

1. **Open Sidebar**: Click the `Settings`/`Actions` icon in the left sidebar to expand it.
2. **Click "Run Pipeline"**: Initiates Agent C (Interpreter) in IR mode from the sidebar.
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
- **Approve**: Click **"Next Phase: Refinement"** in the top header to lock the plan and proceed to code generation.

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

## 🎨 V3.9 Feature: Quality Sub-Tab (February 2026)

### Overview
The **Quality sub-tab** provides real-time data quality monitoring during IR generation, helping developers ensure that normalized logic maintains data integrity standards.

### Access & UI
Located in the **Drafting execution panel** alongside existing tabs:
- **Logs** (execution trace)
- **Code** (IR output)
- **Schema** (DDL preview)
- **Performance** (generation metrics)
- **Quality** ⭐ NEW - Data quality dashboard

### Features

#### 1. Quality Metrics Dashboard
Real-time visualization of:
- **Completeness**: % of non-null required fields in IR
- **Accuracy**: Type validation and constraint adherence
- **Consistency**: Cross-step dependency integrity
- **Conformity**: Adherence to design registry patterns
- **Uniqueness**: Primary key constraint validation
- **Timeliness**: Temporal logic correctness (SCD, event timestamps)

#### 2. Violation Detection
Highlights issues in generated IR:
```json
{
  "violation_type": "NULL_IN_REQUIRED_FIELD",
  "severity": "ERROR",
  "step_id": "uuid",
  "field": "logical_operations[0].target",
  "message": "MERGE operation missing target table name"
}
```

#### 3. Anomaly Detection
AI-powered detection of:
- **Volume Anomalies**: Unexpected record counts in transformations
- **Pattern Breaks**: Deviation from established naming conventions
- **Logic Gaps**: Missing business rules (e.g., SCD handling without date tracking)

### Technical Implementation

**Component:** `QualityDashboard`  
**Location:** `apps/web/app/components/visualization/QualityDashboard.tsx`  
**Endpoint:** `GET /api/visualization/projects/{project_id}/quality`

**Data Source:**  
Queries `utm_quality_metrics` table populated during IR generation:
```sql
SELECT 
  overall_score,
  completeness,
  accuracy,
  consistency,
  conformity,
  uniqueness,
  timeliness
FROM utm_quality_metrics
WHERE project_id = $1
ORDER BY created_at DESC
LIMIT 1
```

### Workflow Integration

1. **During IR Generation:**
   - Agent C normalizes legacy code → IR
   - Quality service analyzes IR structure
   - Metrics updated in real-time (WebSocket)

2. **Developer Review:**
   - Switch to **Quality tab**
   - View metrics dashboard
   - Click violations to jump to affected IR step

3. **Approval Gate:**
   - Minimum quality score required (configurable, default: 75%)
   - Blockers: Critical violations must be resolved
   - Warnings: Can proceed with documentation

### Configuration

**Quality Thresholds** (in project settings):
```json
{
  "quality_gates": {
    "drafting": {
      "min_overall_score": 75,
      "block_on_critical": true,
      "required_checks": ["completeness", "consistency"]
    }
  }
}
```

### Best Practices

✅ **Review Quality Early**: Check after first few assets to catch systemic issues  
✅ **Fix High-Severity First**: Critical violations block code generation  
✅ **Use Annotations**: Document accepted warnings for audit trail  
❌ **Don't Skip**: Low quality IR leads to buggy generated code

---

## 🚀 v4.0 Zero-Hardcode Generation (Feature 1)

### Overview
**Sprint 14 Feature**: Database-driven prompt management replacing all hardcoded templates.

**Status**: ✅ 100% Complete (Backend + Frontend)

### PromptService (531 lines)

**Capabilities**:
- **CRUD Operations**: Create, read, update, delete prompts via API
- **Versioning**: Automatic history snapshots via database triggers
- **Caching**: In-memory cache for hot prompts (reduce DB load 80%+)
- **Tenant Overrides**: Global prompts + tenant-specific customizations
- **Activation Control**: `is_active` flag for A/B testing
- **Metadata Search**: JSONB queries (tech_id, layer, medallion_type)

**API Endpoints**:
```http
GET    /api/v1/prompts                   # List all prompts
GET    /api/v1/prompts/{prompt_id}      # Get specific prompt
POST   /api/v1/prompts                   # Create new prompt
PUT    /api/v1/prompts/{prompt_id}      # Update prompt (creates version)
DELETE /api/v1/prompts/{prompt_id}      # Soft delete
GET    /api/v1/prompts/{prompt_id}/history  # Version history
```

**Example Usage**:
```python
from apps.api.services.prompt_service import PromptService

ps = PromptService(tenant_id=tenant_id)

# Load agent prompt
prompt = await ps.get_prompt("agent_c_developer")

# Load cartridge prompt with tech-specific context
cartridge_prompt = await ps.get_prompt(
    "cartridge_pyspark_bronze",
    metadata_filters={"tech_id": "pyspark", "layer": "bronze"}
)

# Update prompt (automatic versioning)
await ps.update_prompt(
    "agent_c_developer",
    new_content="...",
    changelog="Sprint 14: Added v4.0 validation instructions"
)
```

### utm_prompts Table

**Storage**: Global prompts with trigger-based automatic versioning

**Key Fields**:
- `prompt_id` (TEXT primary key) - e.g., "agent_c_developer", "cartridge_pyspark_bronze"
- `tenant_id` (UUID nullable) - NULL = global, otherwise tenant-specific override
- `version_number` (INTEGER) - Auto-incrementing per prompt_id + tenant_id
- `content` (TEXT) - Full prompt template (multi-line markdown)
- `is_active` (BOOLEAN) - Enable/disable for A/B testing
- `metadata` (JSONB) - Searchable context:
  ```json
  {
    "tech_id": "pyspark",
    "layer": "bronze",
    "medallion_type": "extraction",
    "tags": ["databricks", "spark3.0"]
  }
  ```
- `changelog` (TEXT) - Human-readable version notes
- `created_at`, `updated_at` (TIMESTAMPTZ)

**Automatic Versioning Trigger**:
```sql
CREATE TRIGGER utm_prompts_version_trigger
BEFORE INSERT OR UPDATE ON utm_prompts
FOR EACH ROW
EXECUTE FUNCTION utm_prompts_version_increment();
```

**History Table** (Immutable):
```sql
CREATE TABLE utm_prompts_history (
    history_id          BIGSERIAL PRIMARY KEY,
    prompt_id           TEXT NOT NULL,
    tenant_id           UUID,
    version_number      INTEGER NOT NULL,
    content             TEXT NOT NULL,
    metadata            JSONB DEFAULT '{}',
    changelog           TEXT,
    created_at          TIMESTAMPTZ NOT NULL,
    archived_at         TIMESTAMPTZ DEFAULT NOW()
);
```

**Use Cases**:
- Version control (rollback to previous prompt)
- A/B testing (compare is_active = true vs false)
- Tenant customization (override global prompts)
- Audit trail (who changed what when)

### Knowledge Injection Evolution

**v3.9 (Hardcoded)**:
```python
# Load from filesystem
base_prompt = load_file("prompt_lab_export/core_agents/agent_c/prompt_v1.md")
source_config = load_json(f"origins/{source_tech}/config_v1.json")
target_config = load_json(f"destinations/{target_tech}/config_v1.json")

# Manual assembly
full_prompt = f"{base_prompt}\n\n{source_config['instruction']}\n\n{target_config['instruction']}"
```

**v4.0 (Database-Driven)**:
```python
from apps.api.services.prompt_service import PromptService

ps = PromptService(tenant_id=tenant_id)

# Load from database (cached)
base_prompt = await ps.get_prompt("agent_c_developer")
source_prompt = await ps.get_prompt(f"origin_{source_tech}")
target_prompt = await ps.get_prompt(f"cartridge_{target_tech}_{layer}")

# Automatic assembly with metadata filtering
full_prompt = await ps.assemble_prompt(
    agent_id="agent-c",
    source_tech="sqlserver",
    target_tech="pyspark",
    layer="bronze"
)
```

**Benefits**:
- ✅ No code deployment for prompt updates (live editing)
- ✅ Automatic versioning (rollback capability)
- ✅ Tenant-specific customization (multi-tenant SaaS)
- ✅ A/B testing infrastructure (is_active flag)
- ✅ Caching (80%+ DB load reduction)
- ✅ Audit trail (utm_prompts_history)

### Cartridge Pre-Selection (v4.0)

**Database Query**:
```python
# Get active cartridge prompt
cartridge = await ps.get_prompt(
    prompt_id=f"cartridge_{target_tech}_{layer}",
    metadata_filters={"tech_id": target_tech, "layer": layer, "is_active": True}
)
```

**Active Cartridges** (v4.0):
- **Databricks**: `cartridge_pyspark_bronze`, `cartridge_pyspark_silver`, `cartridge_pyspark_gold`
- **Snowflake**: `cartridge_snowflake_bronze`, `cartridge_snowflake_silver`, `cartridge_snowflake_gold`
- **Fabric**: `cartridge_fabric_bronze`, `cartridge_fabric_silver_direct`, `cartridge_fabric_gold`
- **BigQuery**: `cartridge_bigquery_bronze`, `cartridge_bigquery_silver`, `cartridge_bigquery_gold`

Cartridges execute in **Stage 4 (Refinement)** with real-time validation (ValidationService).

### Migration Path

**Migrating Hardcoded Prompts to Database**:
```bash
# Run migration script
python migrations/sprint_v4.0_prompts.sql

# Sync specific prompt
python sync_agent_f_prompt.py  # Example for Agent F
```

**Active Prompts** (v4.0 - Feb 2026):
- **Agent Prompts**: 6 (agent_a, agent_s, agent_c, agent_f, agent_g, agent_d)
- **Cartridge Prompts**: 8 (pyspark, snowflake, fabric, bigquery × bronze/silver/gold)
- **Total**: 14 active prompts (~200KB including history)

---

## 🔧 v4.0 E2E Stabilization Fixes (Marzo 3, 2026)

### Bug #1 — Drafting BLOCKED: Project status is 'TRIAGED'

**Síntoma:** Al clickar "Run Pipeline", el log retornaba inmediatamente `BLOCKED: Project status is 'TRIAGED'`.

**Causa:** `run_full_migration()` valida que el status sea `DRAFTING` o `DRAFTED` al inicio. El endpoint `POST /transpile/orchestrate` lanzaba el background task sin actualizar primero el status.

**Fix** (`apps/api/routers/transpile.py`):
```python
# ANTES (roto)
# DO NOT change status here - let run_full_migration do validations first
background_tasks.add_task(_run_orchestration_background, ...)

# DESPUÉS (correcto)
await db.update_project_status(project_id, "DRAFTING")   # ← sincrónico
background_tasks.add_task(_run_orchestration_background, ...)
```

### Bug #2 — Logs mostraban ejecución anterior (logs stale)

**Síntoma:** Al navegar a Drafting desde Triage, el panel de logs mostraba la corrida anterior incluyendo errores viejos.

**Fix** (`DraftingView.tsx`):

| Status al montar | Acción |
|---|---|
| `TRIAGED` (recién llegado) | Logs vacíos — pantalla limpia |
| `DRAFTING` (run activo) | Carga logs + arranca polling |
| `DRAFTED` / beyond (completado) | Carga logs históricos + marca completo |

```tsx
// DraftingView.tsx — mount
if (status === 'DRAFTING') {
    await fetchOrchestrationLogs();
    setIsOrchestrationRunning(true);
} else if (DRAFTED_OR_BEYOND.includes(status)) {
    await fetchOrchestrationLogs();
    setIsDraftingComplete(true);
    setProgress(100);
}
// Si TRIAGED → logs vacíos, fresh start
```

> [!TIP]
> **Optimization Tip**: If Agent C produces overly complex IR, use the "Simplify" button to ask Agent F (Critic) to refactor the logic before code generation.

> [!IMPORTANT]
> **IR is Persistent**: Once approved, the IR is locked. Future stages (Refinement, Certification) use this IR, not the original legacy files. This ensures consistency across regenerations.

> [!NOTE]
> **v4.0 Prompts**: All prompts now loaded from utm_prompts table. Legacy `prompt_lab_export/` files remain for reference only.

---

**Document Version:** 3.0 (v4.0 E2E Stabilization)  
**Last Updated:** Marzo 3, 2026  
**Sprint:** E2E Stabilization (Post-Launch)  
**Status:** ✅ Stable — Drafting BLOCKED bug fixed, stale logs fixed  

**See Also**:
- [DATABASE_SCHEMA.md](../DATABASE_SCHEMA.md) - utm_prompts schema details
- [SYSTEM_ARCHITECTURE.md](../SYSTEM_ARCHITECTURE.md) - Zero-Hardcode architecture flow
- [STAGE_4_REFINEMENT.md](STAGE_4_REFINEMENT.md) - Real-time validation integration
- [V4.0_DEVELOPER_GUIDE.md](../../V4.0_DEVELOPER_GUIDE.md) - PromptService usage patterns

---

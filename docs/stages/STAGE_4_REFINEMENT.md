# Stage 4: Refinement (Code Synthesis & Transpilation)

## 📌 Overview
**Refinement** is the core code generation engine. It uses the **Universal IR** from Drafting and applies **cartridge-based transpilation** to generate production-ready code for the target platform (PySpark, Snowflake, BigQuery, etc.).

> **v3.5 Update**: **Self-correcting AI loop** - Agent C generates code, Agent F reviews and fixes, repeat until quality threshold is met.

## 🎯 Objectives
- **Cartridge Execution**: Apply target-specific code templates to IR
- **Medallion Architecture**: Generate Bronze (Raw), Silver (Curated), Gold (Business) layers
- **Platform Optimization**: Leverage target-specific features (Delta Lake Z-Order, Snowflake clustering, etc.)
- **Self-Correction Loop**: Agent C → Agent F iterative refinement
- **Quality Assurance**: Automated linting, syntax validation, best practice checks

## 👨‍💻 User Guide
### 1. The Refinement Loop
- Click **"Refine & Modernize"**.
- The system runs the **Agent C (Coder)** -> **Agent F (Fixer)** loop.
- It writes code, checks it against the compiler/linter, and fixes errors automatically.

### 2. Workflow Tabs
- **Orchestrator**: View the live logs of the agents modifying files.
- **Output Explorer**: Browse the generated directory structure.
- **Workbench (Diff)**: Compare side-by-side.
    - **Left**: Original Legacy Source (from Triage).
    - **Right**: Generated Modern Code.
    - Use this to verify logic translation accuracy.

## ⚙️ Technical Details

### Services
- **AgentCService**: Code synthesis using IR + cartridges
- **AgentFService**: Code review and optimization
- **PersistenceService**: R2 storage for generated artifacts
- **CartridgeService**: Loads and executes technology-specific generators

### Agents
- **Agent C (Interpreter)** - Mode: `Code_Synthesis`
  - Input: Universal IR from `utm_logical_steps`
  - Process: Apply cartridge templates + tech knowledge
  - Output: Platform-specific code (`.py`, `.sql`, `.ipynb`)
- **Agent F (Critic)** - Mode: `Code_Review`
  - Input: Generated code from Agent C
  - Process: Lint, validate, optimize, suggest fixes
  - Output: Improved code or rejection with feedback

### Self-Correction Loop

**Iterative Quality Improvement**:
```python
max_iterations = 3
quality_threshold = 85  # Score out of 100

for iteration in range(max_iterations):
    # Agent C generates code
    code = agent_c.synthesize(ir, cartridge, tech_knowledge)
    
    # Agent F reviews
    review = agent_f.critique(code, quality_requirements)
    
    if review.score >= quality_threshold:
        break  # Code approved
    else:
        # Feed back critique to Agent C for next iteration
        agent_c.incorporate_feedback(review.suggestions)
```

**Quality Metrics**:
- **Syntax Validity**: Code parses without errors
- **Best Practices**: Follows platform-specific patterns
- **Performance**: Uses efficient operations (broadcast joins, partitioning)
- **Security**: No hardcoded credentials, PII is masked
- **Idempotency**: MERGE operations instead of INSERT/DELETE

### Cartridge System

**Available Cartridges** (v3.5):
1. **DatabricksCartridge**: PySpark notebooks with Delta Lake optimization
2. **SnowflakeCartridge**: SQL scripts with Snowflake tasks and streams
3. **FabricCartridge**: Fabric notebooks + data pipelines
4. **BigQueryCartridge**: SQL procedures with BigQuery optimizations
5. **RedshiftCartridge**: SQL with Redshift distribution strategies
6. **SalesforceCartridge**: Apex classes and SOQL queries

**Cartridge Execution**:
```python
# 1. Load cartridge
cartridge = CartridgeLoader.load(target_tech)  # "DATABRICKS"

# 2. For each IR step
for step in utm_logical_steps:
    # 3. Apply cartridge template
    code = cartridge.transpile(
        ir=step.logical_operations,
        metadata=step.metadata,
        tech_config=destination_config
    )
    
    # 4. Save to R2
    r2_path = f"tenant-{tid}/projects/{pid}/generated/{step.name}.py"
    persistence.write_file(r2_path, code)
```

### Database Tables

**utm_transformations**: Generated code metadata
```sql
{
  transformation_id: uuid,
  project_id: uuid,
  tenant_id: uuid,
  logical_step_id: uuid,        -- References utm_logical_steps
  output_file_path: "tenant-x/projects/y/generated/dim_customer.py",
  file_type: "pyspark | sql | notebook",
  medallion_layer: "BRONZE | SILVER | GOLD",
  agent_c_version: "v1",
  agent_f_review: {
    "score": 92,
    "iterations": 2,
    "issues_found": [],
    "optimizations_applied": ["added partitioning", "replaced broadcast join"]
  },
  generated_at: timestamp
}
```

### Cloud-Scale Synthesis (v3.5)

**Parallel Code Generation**:
- Each IR step can be transpiled independently
- Multiple Agent C instances process steps in parallel
- Generated files stream directly to R2 (no local disk)
- File inventory updated in Supabase for fast listing

**Storage Structure**:
```
tenant-{id}/projects/{pid}/
├── generated/
│   ├── bronze/
│   │   ├── src_customers.py
│   │   └── src_orders.py
│   ├── silver/
│   │   ├── stg_customers.py
│   │   └── stg_orders.py
│   └── gold/
│       ├── dim_customer.py
│       └── fact_sales.py
└── schema/
    └── ddl_reference.sql
```

**Workbench Diff View**:
- **Left Panel**: Original legacy file from R2 (`source/`)
- **Right Panel**: Generated modern code from R2 (`generated/`)
- Both loaded via `PersistenceService.read_file_content()`
- Syntax highlighting for both legacy and modern code

---

> [!TIP]
> **Optimization**: Enable "Fast Mode" to skip Agent F review for simple transformations (flat file loads). Use "Quality Mode" for complex business logic.

> [!IMPORTANT]
> **Medallion Architecture**: Bronze = raw ingestion, Silver = cleaned/conformed, Gold = aggregated/business-ready. The system automatically organizes code by layer.

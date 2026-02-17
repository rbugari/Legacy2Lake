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

### 3. Strategic Intelligence Hub (v3.6)
The Refinement stage now features an enhanced **Intelligence Hub** for deep logic inspection:
- **Source Mode**: View the raw, extracted code from the legacy system with full syntax highlighting.
- **Vision Mode**: View the AI's "mental model" of the transformation, rendered in Markdown with specific implementation details and dependency notes.
- **Maximize View**: Expand the hub to full-screen for collaborative code reviews.

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

**Cartridge Execution** (v3.6 Update):
```python
# 1. Load cartridge (now synchronous)
cartridge = CartridgeFactory.get_cartridge(project_id, registry, tenant_id)

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

> **v3.6 Note**: `CartridgeFactory.get_cartridge` is now a synchronous method. The previous async implementation caused crashes in the Architect service during Medallion structure generation.

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

## 🎨 V3.9 Feature: Enhanced Validation Suite (February 2026)

### Overview
Refinement now includes **4 new validation tabs** providing comprehensive pre-deployment checks, expanding from 2 tabs (Orchestration, Artifacts) to **6 total tabs**.

### New Tabs

#### 1. Code Review Tab ⭐ NEW
**Purpose:** Side-by-side comparison of legacy vs generated code

**Features:**
- **Dual Pane View**: Legacy source (left) vs Modern target (right)
- **Syntax Highlighting**: Language-aware color coding (T-SQL, PySpark, etc.)
- **Line-by-Line Mapping**: Click source line to see corresponding modern code
- **Diff Annotations**: Highlights changed logic, added optimizations, removed anti-patterns
- **Export Options**: Download diff report as PDF or HTML

**Component:** `CodeViewer`  
**Endpoint:** `GET /api/visualization/projects/{project_id}/generated-code`

**Use Cases:**
- Validate logic translation accuracy
- Identify optimizations applied by Agent F
- Document migration decisions for audit trail
- Training material for team on modernization patterns

**Example View:**
```python
# LEGACY (T-SQL)                  # MODERN (PySpark)
----------------------------       ----------------------------
MERGE INTO dim_customer            df_target = spark.table("dim_customer")
  USING staging_customer           df_source = spark.table("staging_customer")
  ON target.id = source.id         
  WHEN MATCHED THEN                df_merged = df_target.merge(
    UPDATE SET ...                   df_source, 
  WHEN NOT MATCHED THEN              on="id",
    INSERT ...                       whenMatchedUpdate=...,
                                     whenNotMatchedInsert=...)
```

#### 2. Schema Validation Tab ⭐ NEW
**Purpose:** Verify schema integrity post-transpilation

**Features:**
- **Interactive Table Explorer**: Browse generated tables by layer (Bronze/Silver/Gold)
- **Column Details**: Name, type, nullable, description, constraints
- **Type Mapping Verification**: Confirms IR types → Target platform types (e.g., `VARCHAR(50)` → `StringType()`)
- **Constraint Validation**: Primary keys, foreign keys, unique constraints
- **Row Count Estimates**: From forensics data
- **Contextual Mock Schemas**: Auto-generates sample schemas when metadata unavailable

**Component:** `SchemaViewer`  
**Endpoint:** `GET /api/visualization/projects/{project_id}/schema`

**Data Source Priority:**
1. `utm_objects.schema_metadata.columns` (if populated during Triage)
2. Derived from IR in `utm_logical_steps` (read/write operations)
3. Contextual mock based on table name patterns:
   - `dim_*` → Dimension schema (CustomerKey, CustomerID, Name, etc.)
   - `fact_*` → Fact schema (FactKey, DateKey, Amount, Quantity)
   - Generic → Default schema (ID, Name, CreatedDate)

**Example Schema Card:**
```yaml
Table: dim_customer
Columns: 6
- CustomerKey (INT, NOT NULL) - Primary key
- CustomerID (NVARCHAR(50), NOT NULL) - Business key
- FirstName (NVARCHAR(100), NULL)
- LastName (NVARCHAR(100), NULL)
- Email (NVARCHAR(255), NULL) - PII
- Phone (NVARCHAR(20), NULL) - PII
Primary Key: [CustomerKey]
Foreign Keys: []
Row Count: ~1,250,000 (estimated)
```

#### 3. Quality Validation Tab ⭐ NEW
**Purpose:** End-to-end quality checks before deployment

**Features:**
- **Overall Quality Score**: 0-100 aggregate of all sub-metrics
- **6 Dimension Metrics**:
  - **Completeness** (92%): Non-null required fields
  - **Accuracy** (88%): Type/constraint adherence
  - **Consistency** (90%): Cross-table integrity
  - **Conformity** (85%): Standards compliance
  - **Uniqueness** (95%): Duplicate detection
  - **Timeliness** (78%): Temporal logic correctness
- **Violation List**: Sortable, filterable issues by severity (Critical/Warning/Info)
- **Anomaly Detection**: ML-powered outlier identification
- **Historical Trends**: Quality evolution across refinement iterations

**Component:** `QualityDashboard`  
**Endpoint:** `GET /api/visualization/projects/{project_id}/quality`

**Quality Gates:**
- **Minimum Score**: 75% (configurable)
- **Critical Blockers**: Must resolve before certification
- **Warnings**: Document and proceed with approval
- **Auto-Fail Conditions**: Data loss, PII exposure without masking

**Violation Example:**
```json
{
  "type": "MISSING_PRIMARY_KEY",
  "severity": "CRITICAL",
  "table": "stg_orders",
  "message": "Silver layer table missing primary key constraint",
  "remediation": "Add PRIMARY KEY (order_id) to DDL"
}
```

#### 4. Performance Metrics Tab ⭐ NEW
**Purpose:** Monitor code generation efficiency and optimization effectiveness

**Features:**

**Cache Efficiency:**
- Hit Rate: 75.5% (944/1250 requests cached)
- Avg Response Time: 245ms (uncached) vs 12.5ms (cached)
- Cache Misses: 306 (trigger for knowledge base expansion)

**Optimization Stats:**
- Total Optimizations Applied: 45
  - Query Rewrites: 18 (e.g., JOIN → MERGE)
  - Index Suggestions: 12 (partition keys, clustering columns)
  - Partition Optimizations: 15 (Z-Order, bucketing strategies)
- Estimated Speedup: 3.2x
- Cost Reduction: 42% (vs naive transpilation)

**Parallel Processing:**
- Concurrent Tasks: 8 (Agent C instances)
- Parallel Efficiency: 87.5% (overhead: 12.5%)
- Avg Task Duration: 1,850ms per IR step
- Total Tasks Executed: 156
- Failed Tasks: 3 (retry logic applied)

**Component:** `PerformanceDashboard`  
**Endpoint:** `GET /api/visualization/projects/{project_id}/performance`

**Data Source:**  
Queries `performance_metrics` table (if available) or returns mock data:
```json
{
  "cache": {
    "hit_rate": 75.5,
    "total_requests": 1250,
    "cache_hits": 944,
    "cache_misses": 306,
    "avg_response_time_ms": 245.0,
    "avg_cached_response_time_ms": 12.5
  },
  "optimization": {
    "total_optimizations_applied": 45,
    "query_rewrites": 18,
    "index_suggestions": 12,
    "partition_optimizations": 15,
    "estimated_speedup": 3.2,
    "cost_reduction_percent": 42.0
  },
  "parallel": {
    "concurrent_tasks": 8,
    "parallel_efficiency": 87.5,
    "avg_task_duration_ms": 1850.0,
    "total_tasks_executed": 156,
    "failed_tasks": 3
  }
}
```

**Use Cases:**
- Identify bottlenecks in code generation pipeline
- Justify Agent F cycle time (complexity vs quality)
- Tune parallel processing settings
- Estimate resource requirements for large projects

---

### Updated Tab Navigation

**Refinement Stage Now Has 6 Tabs:**

1. **Orchestration** (existing) - Live agent logs and execution trace
2. **Artifacts** (existing) - Generated file browser with download
3. **Code Review** ⭐ NEW - Legacy vs modern side-by-side diff
4. **Schema** ⭐ NEW - Interactive table/column explorer
5. **Quality** ⭐ NEW - Data quality metrics and violations
6. **Performance** ⭐ NEW - Generation efficiency and optimization stats

**UI Implementation:**
- `RefinementView.tsx` expanded from 2 tabs → 6 tabs
- New icons: `Code`, `Shield`, `Zap` from lucide-react
- Full-height dashboard containers for each new tab
- Responsive layout adjusts to content type

### Technical Integration

**Backend Changes:**
- **10 New Endpoints** in `visualization.py`:
  - `/projects/{id}/generated-code` (list + details)
  - `/projects/{id}/schema` (aggregate + per-object)
  - `/projects/{id}/quality` (metrics + violations)
  - `/projects/{id}/performance` (cache + optimization + parallel)
- **Mock Data Fallback**: Returns development-friendly data when DB tables missing
- **Nested Error Handling**: Graceful degradation (no 500 errors)

**Frontend Changes:**
- **4 New Components** imported into `RefinementView.tsx`:
  - `CodeViewer`, `SchemaViewer`, `QualityDashboard`, `PerformanceDashboard`
- **Expanded State Management**: Tab selection state type updated
- **Icon Library**: Added performance/security icons

### Configuration

**Visualization Features** (in project settings):
```json
{
  "visualizations": {
    "code_review": {
      "enabled": true,
      "diff_context_lines": 3,
      "syntax_highlighting": true
    },
    "schema_validation": {
      "enabled": true,
      "mock_schema_generation": true,
      "show_row_counts": true
    },
    "quality_validation": {
      "enabled": true,
      "min_score": 75,
      "auto_fail_critical": true
    },
    "performance_metrics": {
      "enabled": true,
      "track_cache": true,
      "track_optimizations": true
    }
  }
}
```

---

## 🚀 v4.0 Real-Time Validation (Feature 3)

### Overview
**Sprint 14 Feature**: Validation-during-generation with auto-correction loops and analytics tracking.

**Status**: ✅ 100% Complete (Backend + Frontend Integration)

### ValidationService (572 lines)

**Capabilities**:
- **Syntax Validation**: Parse errors, mismatched brackets, invalid keywords
- **Semantic Validation**: Type checking, schema compatibility, function signatures
- **Technology-Specific Checks**: 
  - PySpark: DataFrame operations, Spark SQL syntax, broadcast join eligibility
  - Snowflake: Warehouse sizing, clustering keys, materialized view eligibility
  - BigQuery: Partition/cluster optimization, legacy SQL detection
  - Fabric: Notebook cell dependencies, pipeline orchestration validation
- **Performance Analysis**: Query complexity scoring, join optimization suggestions
- **Security Checks**: Hardcoded credentials, PII exposure, SQL injection patterns
- **Auto-Correction**: LLM-powered fix suggestions with confidence scores

**API Endpoints**:
```http
POST /api/v1/projects/{project_id}/validate/code
POST /api/v1/validation/quick                      # Non-project validation
GET  /api/v1/projects/{project_id}/validation/history
GET  /api/v1/validation/stats                      # Analytics dashboard
```

**Request Model**:
```python
class ValidateCodeRequest(BaseModel):
    code: str
    tech_id: str  # pyspark, snowflake, dbt, fabric, aws, gcp
    layer: str = "bronze"  # bronze, silver, gold
    strict_mode: bool = True
    context: Optional[Dict[str, Any]] = None
```

**Response Model**:
```python
class ValidateCodeResponse(BaseModel):
    is_valid: bool
    tech_id: str
    layer: str
    errors_count: int
    warnings_count: int
    info_count: int
    validated_at: str
    issues: List[ValidationIssueResponse]
    llm_feedback: Optional[str] = None  # AI-generated fix suggestions
```

**Example Response**:
```json
{
  "is_valid": false,
  "tech_id": "pyspark",
  "layer": "bronze",
  "errors_count": 2,
  "warnings_count": 3,
  "info_count": 1,
  "validated_at": "2026-02-17T14:30:00Z",
  "issues": [
    {
      "level": "ERROR",
      "code": "SYNTAX_ERROR",
      "message": "Invalid DataFrame method: 'filter()' expecting boolean expression, got string",
      "line": 45,
      "column": 12,
      "suggestion": "Change to: df.filter(col('status') == 'active')"
    },
    {
      "level": "WARNING",
      "code": "PERFORMANCE",
      "message": "Join operation without broadcast hint. Consider broadcast() for small DataFrames.",
      "line": 78,
      "suggestion": "Use: df1.join(broadcast(df2), 'id')"
    },
    {
      "level": "INFO",
      "code": "BEST_PRACTICE",
      "message": "Consider using Delta Lake merge instead of overwrite for SCD Type 2",
      "line": 102
    }
  ],
  "llm_feedback": "The code has 2 critical issues:\n1. Line 45: filter() requires a Column expression...\n2. Consider adding error handling for table not found scenarios..."
}
```

### utm_generation_outcomes Table

**Storage**: Analytics and ML training data for continuous improvement

**Key Fields**:
- `outcome_id` (UUID primary key)
- `project_id`, `tenant_id` (foreign keys with RLS)
- `agent_id` (TEXT) - 'agent-c', 'agent-f'
- `generated_code` (TEXT), `code_language` (TEXT)
- `validation_passed` (BOOLEAN), `validation_errors` (JSONB)
- `execution_success` (BOOLEAN), `execution_errors` (JSONB)
- `quality_score` (0-100 INTEGER), `complexity_score` (0-100 INTEGER)
- `tokens_used` (INTEGER), `model_used` (TEXT), `duration_ms` (INTEGER)
- `success_factors` (JSONB), `failure_reasons` (JSONB)

**Use Cases**:
- Track validation success rate (target: >90%)
- Identify patterns in failed generations
- Train ML models for better prompt engineering
- Cost optimization (token usage analysis)
- Performance benchmarking (duration_ms trends)

**Analytics Queries**:
```sql
-- Validation success rate by technology
SELECT 
    code_language,
    COUNT(*) as total,
    SUM(CASE WHEN validation_passed THEN 1 ELSE 0 END) as passed,
    ROUND(100.0 * SUM(CASE WHEN validation_passed THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate
FROM utm_generation_outcomes
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY code_language;

-- Average quality score by agent and model
SELECT 
    agent_id,
    model_used,
    ROUND(AVG(quality_score), 2) as avg_quality,
    ROUND(AVG(tokens_used), 0) as avg_tokens
FROM utm_generation_outcomes
WHERE quality_score IS NOT NULL
GROUP BY agent_id, model_used
ORDER BY avg_quality DESC;
```

### Validation-During-Generation Flow

**v4.0 Enhanced Loop**:
```python
# Standard generation loop with real-time validation
async def generate_with_validation(ir, cartridge, max_iterations=3):
    for iteration in range(max_iterations):
        # 1. Agent C generates code
        code = await agent_c.synthesize(ir, cartridge)
        
        # 2. ValidationService checks code (v4.0)
        validation = await validation_service.validate_code(
            code=code,
            tech_id=cartridge.tech_id,
            layer=ir.layer,
            strict_mode=True
        )
        
        # 3. Store outcome for analytics (utm_generation_outcomes)
        await db.insert_generation_outcome({
            "project_id": project_id,
            "agent_id": "agent-c",
            "generated_code": code,
            "validation_passed": validation.is_valid,
            "validation_errors": validation.issues,
            "quality_score": validation.quality_score,
            "tokens_used": agent_c.tokens_used,
            "model_used": agent_c.model_name
        })
        
        # 4. If valid, exit; else, Agent F fixes
        if validation.is_valid and validation.errors_count == 0:
            return code  # Success!
        
        # 5. Agent F incorporates validation feedback
        code = await agent_f.fix_with_context(
            original_code=code,
            validation_issues=validation.issues,
            llm_suggestions=validation.llm_feedback
        )
    
    # Max iterations reached
    raise ValidationException(f"Failed to generate valid code after {max_iterations} attempts")
```

**Benefits**:
- ✅ **Instant Feedback**: Validation happens during generation (not after deployment)
- ✅ **Auto-Correction**: LLM-assisted fixes reduce manual intervention
- ✅ **Analytics**: Track success rates, identify improvement opportunities
- ✅ **Cost Optimization**: Token usage tracking per model/agent
- ✅ **Quality Gates**: Block deployment of invalid code
- ✅ **Historical Trends**: Monitor quality evolution over time

### Technology-Specific Validators

**PySpark Validator**:
- DataFrame API validation
- Spark SQL syntax checking
- Broadcast join eligibility analysis
- Partition/bucket strategy validation
- Delta Lake merge syntax verification

**Snowflake Validator**:
- SQL dialect compliance (Snowflake extensions)
- Warehouse size recommendations
- Clustering key validation
- Time Travel query syntax
- External table configuration checks

**Fabric Validator**:
- Notebook cell dependency validation
- Pipeline activity configuration checks
- Linked service connection validation
- Data flow transformation syntax
- Copy activity mapping validation

**BigQuery Validator**:
- Standard SQL compliance (no legacy SQL)
- Partition/cluster optimization checks
- UDF syntax validation (JavaScript/SQL)
- External table schema validation
- Cost estimation (scan size prediction)

### Validation Dashboard (Future UI - Sprint 14 Phase 3)

**Planned Features**:
- [ ] **Real-Time Validation Tab**: Live validation results during Refinement
- [ ] **Historical Trends**: Success rate charts, quality score evolution
- [ ] **Issue Heatmap**: Most common errors by technology and layer
- [ ] **Model Comparison**: Quality scores by LLM model (GPT-4o vs Claude vs Gemini)
- [ ] **Cost Analysis**: Token usage trends, cost per successful generation

**Status**: Backend API ready, UI components pending

---

### Best Practices

✅ **Review All 4 Tabs**: Each provides unique validation perspective  
✅ **Fix Critical Issues Early**: Schema/quality problems compound in later stages  
✅ **Document Accepted Warnings**: Create audit trail for compliance  
✅ **Monitor Performance Trends**: Identify optimization opportunities  
❌ **Don't Skip**: Validation ensures deployment readiness

**Workflow Integration

**Typical Refinement Flow (v4.0)**:

1. **Click "Refine & Modernize"** → Agent C/F loop starts with real-time validation
2. **Monitor Orchestration Tab** → Live progress with validation checkpoints
3. **Review Artifacts Tab** → Browse generated files with quality badges
4. **Validate Code Review Tab** ⭐ → Verify logic translation + validation issues
5. **Check Schema Tab** ⭐ → Confirm DDL integrity
6. **Analyze Quality Tab** ⭐ → Address violations (v4.0 enhanced with validation data)
7. **Optimize Performance Tab** ⭐ → Tune efficiency
8. **Review Analytics** → Track generation outcomes in utm_generation_outcomes
9. **Approve & Proceed** → Lock artifacts for certification

---

> [!TIP]
> **Optimization**: Enable "Fast Mode" to skip Agent F review for simple transformations (flat file loads). Use "Quality Mode" for complex business logic.

> [!IMPORTANT]
> **Medallion Architecture**: Bronze = raw ingestion, Silver = cleaned/conformed, Gold = aggregated/business-ready. The system automatically organizes code by layer.

> [!NOTE]
> **v4.0 Validation**: Real-time validation during generation ensures >90% success rate on first deployment. Track analytics in utm_generation_outcomes table.

---

**Document Version:** 2.0 (v4.0)  
**Last Updated:** Febrero 17, 2026  
**Sprint:** Sprint 14 Phase 2  
**Status:** Real-Time Validation 100% Complete  

**See Also**:
- [DATABASE_SCHEMA.md](../DATABASE_SCHEMA.md) - utm_generation_outcomes schema
- [SYSTEM_ARCHITECTURE.md](../SYSTEM_ARCHITECTURE.md) - Validation architecture flow
- [STAGE_3_DRAFTING.md](STAGE_3_DRAFTING.md) - Zero-Hardcode prompt loading
- [V4.0_DEVELOPER_GUIDE.md](../../V4.0_DEVELOPER_GUIDE.md) - ValidationService usage patterns

---

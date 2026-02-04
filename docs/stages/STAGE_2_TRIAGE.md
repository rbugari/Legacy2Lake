# Stage 2: Triage (Strategy & Scoping)

## 📌 Overview
**Triage** is where the "noise" is filtered out and source technology is automatically detected. You define the **migration scope** by classifying assets into CORE, SUPPORT, or IGNORED.

> **v3.5 Enhancement**: Automatic technology detection using **Agent S (Scout)** analyzes source artifacts to identify SQL dialects, ETL tools, and platform versions.

## 🎯 Objectives
- **Technology Detection**: Identify source platform (SQL Server, Oracle, SSIS, DataStage, etc.)
- **Visual Classification**: Organize assets by migration priority
- **Dependency Inference**: Build dependency mesh architecture
- **Risk and Complexity Scoring**: Automated analysis of migration difficulty

## 👨‍💻 User Guide

### 1. Technology Detection (Agent S)
When you start Triage, **Agent S (Scout)** automatically:
- **Analyzes File Extensions**: `.dtsx` → SSIS, `.dsx` → DataStage, `.sql` → SQL dialect detection
- **Inspects Content**: Detects T-SQL vs PL/SQL vs MySQL syntax
- **Suggests Configuration**: Proposes source/target technology pairing
- **Updates Project Settings**: Stores detected tech in `utm_projects.settings`

You can review and override the detection in the Triage configuration panel.

### 2. Classification Canvas
- **CORE**: Business critical logic. Everything here *will* be migrated.
- **IGNORED**: Legacy backups, temp tables, logs - excluded from processing.
- **SUPPORT**: Required for the build but not migrated directly (e.g., config files, DDL scripts).

### 3. Actions
- **Drag & Drop**: Move items between columns to define scope.
- **Run Analysis**: Activates **Agent A (Architect v2.0)** in Forensics Mode:
    - Calculates `Cyclomatic Complexity`
    - Identifies `P1/P2/P3` criticality
    - Detects **PII** exposure risk
    - Estimates **Data Volumes** (Small/Medium/Large)
    - Suggests **Partition Keys** for optimization
- **Graph View**: Switch to the Graph tab to see a visual dependency mesh.
- **Approve Triage**: Locks the scope and advances to Drafting stage

- Select any file to add "User Context".
- Example: *"This table is deprecated, map it to `sales_history` instead."*
- Context is stored in `utm_solution_context` and injected into all agent prompts

### 5. Process Cancellation (v3.6)
- **Immediate Termination**: If a Triage analysis is taking too long or was started by mistake, you can use the **"Cancel Process"** button.
- **Graceful Detection**: The backend checks for a `cancellation_requested` flag in `utm_projects` between agent calls (Agent S and Agent A).
- **Auto-Cleanup**: When a process is cancelled, the project state remains in Triage, allowing you to re-configure and restart when ready.

## ⚙️ Technical Details

### Services
- **DiscoveryService**: Scans R2 bucket for artifacts
- **AgentAService**: Architect v2.0 for forensics analysis
- **AgentSService**: Scout for technology detection
- **GraphService**: Builds dependency mesh

### Database Tables
- **utm_objects**: Asset inventory with metadata (`metadata` JSONB field)
  - `metadata.pii_exposure`: Boolean flag
  - `metadata.volume`: "SMALL" | "MEDIUM" | "LARGE"
  - `metadata.partition_key`: Suggested partitioning column
  - `metadata.complexity`: Cyclomatic complexity score
- **utm_projects**: Project settings
  - `settings.source_tech`: Detected source (e.g., "SQLSERVER", "ORACLE")
  - `settings.target_tech`: Selected target (e.g., "DATABRICKS", "SNOWFLAKE")
  - `triage_approved_at`: Timestamp when triage was approved

### Technology Knowledge Injection
When a source technology is detected, the system:
1. Loads the appropriate prompt from `prompt_lab_export/origins/{tech}/`
2. Injects technology-specific patterns into Agent prompts
3. Configures cartridge selection for code generation

### Metadata Forensics (v3.5)
In v3.5, Triage identifies **PII**, **Data Volumes**, and **Partition Keys** automatically using the Architect v2.0 engine. All inferred forensics are stored in Supabase with strict **Row-Level Security (RLS)** tenant isolation, ensuring that specific business context is never leaked between client projects.

**Forensics Output Example**:
```json
{
  "pii_exposure": true,
  "volume": "LARGE",
  "partition_key": "order_date",
  "complexity": 42,
  "dependencies": ["dim_customer", "fact_sales"]
}
```

---

> [!TIP]
> **Multi-Tenant Isolation**: All triage data is scoped by `tenant_id`. User A cannot see User B's project metadata, even in the

 same Supabase instance.

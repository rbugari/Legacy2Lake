# Release Notes

## Version 3.6 (Quality & Stability Enhancement) - 2026-02-03 ⭐ LATEST

This release focuses on improving code quality enforcement, UI polish, and system stability through compliance rule externalization and critical bug fixes.

### 🌟 Major Features

#### Compliance Rule Externalization (Phase 4)
*   **Database-Driven Compliance**: Moved hardcoded cartridge rules from Python code to `utm_system_catalog.config` for centralized management.
*   **Technology-Specific Rules**: Each target technology (Oracle, SSIS, Fabric, etc.) now stores its unique compliance guidelines in the database.
*   **Agent F Synchronization**: Updated compliance auditor to fetch rules dynamically, ensuring knowledge parity with code generators.
*   **Migration Bitácora**: Introduced auto-generated markdown logbooks that document Agent F critiques, scores, and reasoning for each migration file.

#### UI/UX Refinements (Phase 5)
*   **Resizable Drafting Explorer**: Output Explorer in Stage 3 now features a draggable split pane, allowing users to adjust the file tree and preview panel widths.
*   **Tree Visibility Toggle**: Added a "Panel" button to show/hide the file tree, maximizing code preview space when needed.
*   **Persistent Preferences**: Tree width and visibility state are saved per project in localStorage, preserving user layout preferences across sessions.
*   **Enhanced Toolbar**: Improved icons and visual styling for better contrast and clarity in the Drafting stage.

#### Stability Fixes (Phase 6)
*   **Cartridge Factory Synchronization**: Fixed a critical crash in the Refinement pipeline where `CartridgeFactory.get_cartridge` was incorrectly defined as `async`.
*   **Method Refactoring**: Converted `get_cartridge` to synchronous execution and updated all callers (`AgentCService`, `AgentFService`, `ArchitectService`).
*   **Pipeline Verification**: Confirmed end-to-end success of the full refinement pipeline (Profiler → Architect → Refactoring → OpsAuditor).

### 🎨 UI/UX Enhancements

*   Drafting stage now provides professional-grade code review experience with adjustable layouts.
*   Improved visual feedback with better icon choices (`PanelLeftClose`, `PanelLeftOpen`).
*   Smooth transitions and hover effects on resize handles and toggle buttons.

### 🐛 Bug Fixes

*   **Fixed**: `AttributeError: 'coroutine' object has no attribute 'generate_scaffolding'` in Architect service.
*   **Fixed**: Incorrect tech ID capitalization in Solution Configuration UI defaults (now uses lowercase consistently).
*   **Fixed**: Removed erroneous `await` from synchronous Supabase `execute()` calls in cartridge factory.

### ⚠️ Technical Changes

*   **Modified Services**:
    *   `CartridgeFactory.get_cartridge` (`factory.py`): Now synchronous.
    *   `AgentCService` (`agent_c_service.py`): Removed `await` from cartridge calls.
    *   `AgentFService` (`agent_f_service.py`): Removed `await` from cartridge calls.
    *   `DraftingView.tsx`: Added resizable split pane logic with `useCallback` and `useRef` hooks.
*   **Database Schema**:
    *   `utm_system_catalog.config`: Now stores technology-specific compliance rules (e.g., `oracle.compliance.rules`).
*   **Frontend Components**:
    *   New resize handle implementation with visual feedback.
    *   localStorage integration for UI state persistence.

### 📚 Documentation Updates
*   Updated stage documentation to reflect UI improvements.
*   Revised technical documentation for cartridge synchronization changes.
*   Enhanced database structure documentation with compliance rule schema.

---

## Version 3.5 (The Cloud-Native & Multi-Tenant Reset) - 2026-01-31

This foundational release completes the transition to a fully cloud-native, multi-tenant architecture, removing all local filesystem dependencies and introducing high-performance data handling via Cloudflare R2 and Supabase.

### 🌟 Major Features

#### Phase 14: Cloud-Native Storage (R2 Integration)
*   **Total Decoupling**: Replaced the local `solutions/` directory with **Cloudflare R2** as the primary storage backend.
*   **Storage Abstraction**: Introduced `StorageProvider` and `PersistenceService` layers to handle file operations (Save, Read, Delete, List) transparently across cloud backends.
*   **Signed URL Support**: Performance optimization that allows direct-to-browser downloads from R2, bypassing API proxies for large artifact bundles.

#### Phase 15: Enterprise Multi-Tenancy (Supabase v2)
*   **Tenant Isolation**: Every project, object, and asset is now strictly isolated via `tenant_id` at both the database (Supabase RLS) and storage (R2 prefixing) levels.
*   **Global Reset Capability**: New administration tools allow for a clean environment wipe per tenant or globally, ensuring a fresh start for large-scale migration testing.
*   **Service-Role Security**: Backend operations now use elevated service roles to manage tenant-aware maintenance without compromising security.

#### Phase 16: Performance Optimized Governance
*   **Parallelization 2.0**: The Governance Export process now utilizes `asyncio.gather` for parallel R2 file reading and database querying, reducing bundle generation time by over 60%.
*   **Fault-Tolerant Exports**: AI-driven certification (Agent G) now runs with robust timeouts. If a report fails, the system delivers a technical package with placeholders instead of timing out the entire request.
*   **Memory-Safe Packaging**: Artifact ZIP bundles are now built entirely in memory buffers before streaming to the client, eliminating server-side disk bloat.

### 🐛 Bug Fixes
*   **ZIP Leak Fixed**: Resolved a resource leak where temporary ZIP files from project uploads were not being deleted from the server.
*   **Permissions Resolution**: Fixed a critical `permission denied` error on the `utm_column_mappings` table.
*   **Tenant Header Persistence**: Fixed an issue where browser-initiated downloads lost the `X-Tenant-ID` header; the system now auto-resolves tenancy from project metadata.

---

## Version 3.3 (The Universal Connector) - 2026-01-26

This release dramatically expands the platform's input/output capabilities, making it simpler to ingest legacy logic from enterprise ETL tools and deploy to modern data clouds.

### 🌟 Major Features

#### Phase 10: Expanded Source Cartridges (Input)
*   **Universal ETL Ingestion**:
    *   **IBM DataStage (PX)**: Native parsing of `.dsx` exports. Logic extraction from stages and connectors.
    *   **Informatica PowerCenter**: Full XML introspection for `.xml` metadata. Captures Source Qualifiers and Transformations.
    *   **SAP BODS (Data Integrator)**: Reads `.atl` formats to reconstruct Jobs and Dataflows.
    *   **Talend**: Parsing of `.item` files to recover SQL from `tInput` components and `tMap` logic.
    *   **Pentaho (Kettle)**: Support for `.ktr` and `.kjb` files, identifying `TableInput` sources and `TableOutput` targets.

#### Phase 11: Multi-Cloud Destination Cartridges (Output)
*   **Native Generation for 5 Major Platforms**:
    *   **Microsoft Fabric**: Generates PySpark notebooks + Fabric Pipelines (JSON).
    *   **Google Cloud**: BigQuery SQL + LookerML + Airflow DAGs.
    *   **AWS**: Glue (PySpark) + Redshift SQL + QuickSight definitions.
    *   **Salesforce Data Cloud**: Tableau `.tds` + Data Cloud ingestion SQL.
    *   **Snowflake**: Snowpark Python + Snowflake Tasks (native orchestration).

#### Phase 12: Automated Orchestration Layer
*   **Workflow Synthesis**:
    *   Automatically generates the "glue" code to run pipelines.
    *   **Airflow DAGs**: Standard for GCP, AWS, and generic targets.
    *   **Fabric Pipelines**: Specific JSON format for MS Fabric.
    *   **Snowflake Tasks**: SQL-based dependency management.

#### Phase 13: Certified Output Package (COP) Architecture
*   **Vendor-Agnostic Export Bundle**:
    *   Delivers a structured zip file (`src/`, `config/`, `docs/`, `tests/`) ready for enterprise handoff.
    *   **Packaging Service**: Automatically reorganizes refined code into a production-ready folder hierarchy.
    *   **Audit Trail enforcement**: All generated code now includes mandatory `# L2L MODERNIZATION TRACE` headers.
    *   **Auto-Config**: Generates `env_config.yaml` and compliance reports on extraction.

### 🎨 UI/UX Enhancements
*   **Technology Mixer**: Updated with 5 new selection options (GCP, AWS, Fabric, Snowflake, Salesforce).
*   **Design Registry**: Now auto-populates cloud-specific configuration keys (e.g., `gcp_project_id`, `aws_s3_bucket`) upon selection.

---

## Version 3.2 (The Enterprise Modernization Suite) - 2026-01-25

This transformational release elevates Legacy2Lake from a code generator into a **SaaS-ready Enterprise Migration Factory** with forensic intelligence, automated optimization, and AI-driven certification.

### 🌟 Major Features

#### Phase 5: Architect v2.0 & Discovery Heatmaps
*   **Automated Metadata Inference**:
    *   **Agent A (The Architect)** now automatically infers operational metadata from source schemas:
        - **Data Volume**: LOW/MED/HIGH classification for cluster sizing.
        - **PII Detection**: Column-level analysis (`email`, `ssn`, `phone`).
        - **Partition Key Suggestion**: Identifies high-cardinality date columns.
        - **Execution Latency**: DAILY/HOURLY/REAL_TIME frequency estimation.
*   **Discovery Heatmaps**:
    *   **PII Exposure Map**: Color-coded visualization (Red = High PII concentration).
    *   **Criticality Matrix**: Business importance vs. Data Volume quadrants.
    *   Interactive filtering and asset prioritization in Discovery UI.

#### Phase 6: Intelligent Code Generation
*   **Context-Aware Transpilation**:
    *   **Agent C (The Interpreter)** now generates **optimized PySpark** based on Architect v2.0 metadata.
    *   **Auto-Partitioning**: If `partition_key` is detected, generates `.partitionBy(col)` automatically.
    *   **PII Masking**: Automatically applies `SHA2()` hashing for flagged columns.
    *   **Volume Optimization**: High-volume assets get shuffle-optimized joins.
*   **Transformation Logic Editor**:
    *   New **per-column custom expression** support in Column Mapping.
    *   Example: `CASE WHEN age < 18 THEN 'Minor'` auto-injected into generated code.
*   **Code Blueprint Preview**:
    *   Read-only preview of generated structure before transpilation runs.

#### Phase 7: AI-Driven Governance & SaaS Delivery
*   **Compliance Certification (Agent G)**:
    *   **Automated Audit**: Verifies Architect v2.0 recommendations were followed.
    *   **0-100 Scoring**: Numeric compliance score with detailed check results.
    *   **Certification Badge**: Visual indicator in Governance UI.
*   **Automated Runbook Generation**:
    *   System-generated `Modernization_Runbook.md` included in every export.
    *   Contains: Prerequisites, Deployment Steps, Validation Checklist.
*   **Enhanced Export Bundle**:
    ```
    solution_export.zip
    ├── Modernization_Runbook.md
    ├── variables_manifest.json
    ├── quality_contracts/
    └── [Bronze/Silver/Gold scripts]
    ```

#### Phase 8: Variable Injection Framework
*   **Environment Parameterization**:
    *   New **Variable Editor** in Project Settings.
    *   Define key-value pairs (e.g., `S3_ROOT`, `ENV`, `DB_SCHEMA`).
*   **Dynamic Code Generation**:
    *   Agent C replaces hardcoded paths with placeholders: `f"{S3_ROOT}/bronze/data"`.
*   **Handover Manifest**:
    *   Export includes `variables_manifest.json` for deployment teams.
*   **Optionality**: If no variables defined, standard code generation proceeds.

#### Phase 9: Data Quality Contracts (Optional)
*   **Auto-Generated Validation Suites**:
    *   **Great Expectations**: JSON suites with `expect_column_values_to_not_be_null`, type checks, etc.
    *   **Soda Core**: YAML check files with `missing_count(col) = 0`.
*   **Rule-Based Generation**:
    *   `is_nullable=False` → NOT NULL expectation.
    *   `datatype=Integer` → Type validation.
    *   `is_pii=True` → Presence/format checks.
*   **Optional Execution**:
    *   Contracts only generated if Column Mapping defines rules.
    *   No rules? No contracts. Graceful degradation.
*   **Export Integration**:
    *   Quality contracts included in `solution_export.zip` under `quality_contracts/`.

### 🎨 UI/UX Enhancements

*   **Discovery View**:
    *   New heatmap visualizations for PII and Criticality.
    *   Color-coded asset badges (Red/Yellow/Green).
*   **Governance View**:
    *   New **"Data Quality"** tab showing GX/Soda contract previews.
    *   Certification badge with score prominently displayed.
    *   Enhanced Audit Details expandable panel.
*   **Project Settings**:
    *   New **"Variables & Environment Parameters"** section.
    *   Interactive key-value table editor.

### 🐛 Bug Fixes

*   Fixed partition key inference hanging on very large schemas.
*   Resolved PII detection false positives for columns like `email_sent_date`.
*   Fixed variable injection not applying when context was empty.
*   Corrected YAML syntax in generated Soda checks.

### ⚠️ Technical Changes

*   **New Services**:
    *   `ArchitectService` (`architect_service.py`): Metadata inference engine.
    *   `QualityService` (`quality_service.py`): GX/Soda contract generator.
*   **Enhanced Services**:
    *   `GovernanceService`: Now includes audit, runbook, and bundle generation.
    *   `AgentCService`: Variable injection and metadata-driven optimization.
*   **Database Schema**:
    *   `UTM_Object.metadata` (JSONB): Stores Architect v2.0 forensics.
    *   `UTM_Project.settings.variables`: Stores environment parameters.
    *   `UTM_Column_Mapping.logic`: Custom transformation expressions.
*   **API Endpoints**:
    *   `GET /projects/{id}/architect`: Retrieve inferred metadata.
    *   `GET /api/governance/certification/{id}`: Get compliance audit.
    *   `PATCH /projects/{id}/settings`: Update variables.

### 📚 Documentation Updates
*   New phase documents:
    *   `PHASE_5_ARCHITECT.md`
    *   `PHASE_6_INTELLIGENCE.md`
    *   `PHASE_7_GOVERNANCE_DELIVERY.md`
    *   `PHASE_8_VARIABLES.md`
    *   `PHASE_9_QUALITY.md`
*   Updated technical specs:
    *   `technical/architecture.md` - v3.2 agent table
    *   `technical/data_model.md` - Architect v2.0 fields
    *   `technical/api_contract.md` - New endpoints
    *   `technical/system_prompts_and_agents.md` - Enhanced capabilities

---

## Version 3.0 (The Enterprise Compliance Hub) - 2026-01-24

This major release transforms Legacy2Lake from a code generation tool into a comprehensive, governed, and audited modernization platform.

### 🌟 New Features

*   **AI-Guided Architectural Audit (Phase D)**:
    *   **Agent D (Auditor)**: A new specialized agent that performs automated code reviews for PySpark.
    *   **Architectural Scoring**: Real-time 0-100 score based on Idempotency, Medallion standards, Performance, and Security (PII).
    *   **Actionable Suggestions**: Specific code refactoring advice provided directly in the Governance UI.
*   **Granular Column Mapping (Phase A)**:
    *   **New Editor**: Interactive UI to map source legacy columns to modernized target schemas (Bronze/Silver/Gold).
    *   **Business Context Sidebar**: Ability to inject business logic constraints per field.
    *   **PII Tagging**: Direct integration with theauditor to ensure sensitive data is masked.
*   **Universal Orchestration (Phase B)**:
    *   **Multi-Platform DAGs**: Generation of production-ready orchestration files for **Apache Airflow**, **Databricks Jobs (JSON)**, and generic **YAML**.
    *   **Persistence**: Auto-saving of orchestration artifacts into the project directory.
*   **One-Click Deployment Bundles (Phase C)**:
    *   **Project ZIP Export**: New endpoint to export the entire solution (Refined Code, DAGs, and Governance Docs) as a single bundle.
    *   **Git Handover**: Integrated UI feedback for repository pushing.

### 🎨 UI/UX Enhancements (v3.0 Premium Style)

*   **Glassmorphism Theme**: Updated the entire platform with a premium purple theme, blurred backgrounds (`card-glass`), and sleek typography.
*   **Unified Explorer**: Integrated `PromptsExplorer` and `ColumnMappingEditor` into a cohesive tabbed interface in `TriageView`.
*   **Global Layout 3.0**: Optimized workspace for large-screen engineering.

### 🐛 Bug Fixes

*   **Triage Logic**: Fixed edge cases in asset classification during deep scanning.
*   **Persistence Issues**: Improved Supabase sync reliability for large projects.
*   **CSS Conflicts**: Resolved z-index and spacing issues in the new stage navigation bar.

This release focuses on platform stability, artifact visibility, and enhanced AI diagnostic tools.

### 🌟 New Features

*   **Validation Playground**: Integrated interactive testing console in the System Administration page. Allows administrators to run "Dry Run" tests against specific Agents (A, C, F, G) using the configured Azure OpenAI connection.
*   **Consolidated Cartridge API**:
    *   Unified endpoint logic for `Input Cartridges` (Origins) and `Output Cartridges` (Destinations).
    *   Clearer separation in the UI between Ingestion and Synthesis capabilities.
*   **Real-time Artifact Explorer**:
    *   The File Explorer now scans the file system directly instead of relying on a database cache.
    *   **Benefit**: Generated files (e.g., inside `Refinement/Bronze`) appear instantly without manual synchronization.
*   **Robust Frontend Server**:
    *   Migrated from `http-server` to a custom `server.js` (Node/Express based) for better routing support of Next.js static exports.

### 🐛 Bug Fixes

*   **Prompt Validation Error 500**: Fixed an issue where the `validate` function failed due to missing `agent_id` mapping. Implemented a dedicated `/system/validate` endpoint in the Backend.
*   **Missing Bronze Artifacts**: Fixed the visibility issue where the "Bronze" folder appeared empty in the UI.
*   **Azure Configuration**: Streamlined the `.env` handling for Azure OpenAI credentials.

### ⚠️ Technical Changes

*   **Backend**: validation logic moved to `apps/api/routers/system.py`.
*   **Frontend**: `PromptsExplorer` and `SystemPage` updated to support interactive testing.
*   **Startup**: Recommended startup command for frontend changed to `node server.js`.

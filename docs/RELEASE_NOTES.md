# Release Notes

## Version 3.9 (The Multi-User Simplificado Release) - 2026-02-10 ⭐ LATEST

This release delivers complete multi-user support with role-based access control, enabling teams to collaborate on migration projects with proper permission management.

### 🌟 Major Features

#### Multi-User Architecture
*   **Separated User Identity**: New `utm_users` table separates user accounts from `utm_tenants` (organizations)
*   **Role-Based Access**: Four roles with distinct permissions:
    *   **ADMIN**: Platform-level administration (Platform owner only)
    *   **MANAGER**: Tenant administration, user management, all project access
    *   **COLLABORATOR**: Create/edit projects, execute stages
    *   **VIEWER**: Read-only access, download reports
*   **Organization Model**: `utm_tenants` now represents organizations with `display_name` and `tier`
*   **Simplified Schema**: Removed redundant `client_id` and `org_name` columns

#### User Management (Tenant Console)
*   **User Management Tab**: Complete UI at `/settings` for MANAGER to manage team
*   **Create Users**: Direct user creation with automatic temporary password generation
*   **Edit Users**: Update roles, display names, and active status
*   **Reset Password**: MANAGER can reset passwords for team members
*   **Search & Filter**: Find users by username or email
*   **Role Badges**: Visual indicators for user roles (color-coded)

#### Project-Level Access Control
*   **Project Access Tab**: MANAGER can control who accesses which projects
*   **Member Management**: Add/remove users from specific projects
*   **Granular Permissions**: Different roles per project possible
*   **`utm_project_members` Table**: Tracks project-level assignments

#### Platform Admin Dashboard
*   **All Users Tab**: Cross-tenant view of all users in the system
*   **Advanced Filters**: Filter by tenant, role, or search by username/email
*   **Password Reset**: Platform ADMIN can reset any user's password
*   **Ghost Mode**: Impersonate users for troubleshooting (see system as that user)
*   **Tenant Management**: Create, edit, delete tenants with tier management

### 📊 Database Changes

#### New Tables
*   `utm_users`: User identities with email, username, password_hash, role
*   `utm_user_invitations`: Invitation tokens for email-based onboarding
*   `utm_project_members`: Project-level access assignments

#### Schema Modifications
*   `utm_tenants`: Simplified to `tenant_id`, `display_name`, `tier`, `is_active`
*   Removed: `client_id` column (Migration 024)
*   Removed: `org_name` column (Migration 025)

#### Migrations Executed
*   020: Project-level invitations
*   021: Project members table
*   022: Global system catalog
*   023: Admin role support
*   024: Remove client_id simplification
*   025: Remove org_name simplification

### 🔧 Backend Enhancements

#### New Endpoints
*   `GET /auth/users` - List tenant users (MANAGER)
*   `POST /auth/users` - Create user with temp password
*   `PATCH /auth/users/{user_id}` - Update user
*   `POST /auth/users/{user_id}/reset-password` - Reset password (MANAGER)
*   `PATCH /auth/auth/users/{user_id}/reset-password` - Platform ADMIN reset
*   `GET /auth/admin/users` - List all users (Platform ADMIN)
*   `POST /auth/admin/impersonate` - Ghost Mode

#### Authentication Updates
*   Login returns `user_id` in addition to `tenant_id`
*   Password verification uses bcrypt exclusively
*   Last login timestamp tracking
*   Session validation with user context

### 🎨 UI/UX Improvements

#### Tenant Console (`/settings`)
*   **User Management Tab**: Full CRUD interface for team members
*   **Project Access Tab**: Project-level permission management
*   **Role Selector**: Dropdown with COLLABORATOR/VIEWER options for new users
*   **Status Indicators**: Active/Inactive badges for users

#### Platform Admin (`/admin`)
*   **All Users Dashboard**: New tab with cross-tenant user view
*   **Filter Controls**: Three-column filter grid (tenant, role, search)
*   **Reset Password Modal**: Professional modal with password validation
*   **Impersonate Button**: Eye icon to start Ghost Mode
*   **Simplified Tenant Table**: Shows display_name with tenant_id subtitle

### 🔐 Security
*   **Role Validation**: All endpoints validate user role before access
*   **Tenant Isolation**: Users can only see/manage their own tenant
*   **Platform ADMIN**: Special role for cross-tenant operations
*   **Password Hashing**: bcrypt-only with secure salting
*   **Session Headers**: X-Tenant-ID, X-User-ID, X-Role validation

### 📚 Documentation Updates
*   Updated ROADMAP.md with v3.9 completion status
*   Updated RELEASE_PLAN_SIMPLE_v3.9.md with implementation checklist
*   Verified ROLES_AND_ONBOARDING.md alignment

### 🚀 Deployment Notes
*   **Database Migrations**: Execute migrations 020-025 in Supabase Dashboard
*   **Platform Admin**: User with role='ADMIN' in PLATFORM tenant
*   **Default Credentials**: admin / Admin123! (change in production)
*   **No New Environment Variables**: Uses existing configuration

---

## Version 3.8 (The Governance & Architecture Clarity Release) - 2026-02-09

This release formalizes the governance model, implements process locking to prevent data corruption, and introduces professional UI components for system administration and process visualization.

### 🌟 Major Features

#### Process Locking System (CRITICAL)
*   **Data Corruption Prevention**: Implemented comprehensive process locking to prevent concurrent execution of processes on the same project
*   **Database Table**: New `utm_process_locks` table tracks active locks with timeout management
*   **Lock Service**: Backend service with acquire, release, extend, and force-release capabilities
*   **Smart Timeouts**: Process-specific timeouts (triage: 60min, drafting: 30min, refinement: 120min)
*   **Professional Error UI**: `ProcessLockModal` component shows friendly lock errors with user information
*   **Admin Management**: Complete admin interface to view all active locks and force-release stuck processes
*   **Auto-Expiration**: Stale locks automatically expire after timeout (RPC function in Supabase)

#### Process Visualization & UX
*   **ProcessExecutionModal**: Professional modal component for real-time process monitoring
*   **Visual Agent Pipeline**: Interactive display of agent execution stages with status indicators
*   **Live Logs**: Real-time log streaming with color-coded messages (errors, warnings, success)
*   **Progress Tracking**: Visual progress bars and elapsed time counters
*   **Stage Status**: Each agent stage shows: pending, running, completed, or error states
*   **Professional Design**: Replaced basic alerts with polished modal interfaces

#### Admin Tools Enhancement
*   **Process Locks Tab**: New admin section for system-wide lock management
*   **Active Lock Viewer**: Table showing all locks with project, user, process type, and expiration
*   **Force Release**: One-click admin override to release stuck locks
*   **Auto-Refresh**: Lock list automatically updates every 30 seconds
*   **Expired Lock Detection**: Visual warnings for locks past their expiration time

#### Governance Rules Documentation (Phase 19)
*   **Ownership Matrix Formalized**: Comprehensive documentation of who owns what in the system (Admins vs Tenants vs Users)
*   **3-Layer Prompt System**: Clarified the hierarchical prompt architecture:
    *   **Layer 1 (Agent)**: System-level, ADMIN-owned, immutable
    *   **Layer 2 (Cartridge)**: Technology-level, ADMIN-owned, immutable
    *   **Layer 3 (Custom)**: Solution-level, USER-owned, additive modifiers
*   **Technology Catalog Enforcement**: Strict validation that projects can only use origins/destinations that exist in `utm_system_catalog`
*   **Cost Ownership Model**: Formalized tenant responsibility for provider selection and model assignment costs
*   **Data Consistency Rules**: SQL validation queries to detect architectural inconsistencies

### 🎨 UI/UX Improvements
*   **ProcessLockModal**: Amber-themed modal with lock details and user guidance
*   **ProcessExecutionModal**: Gradient-themed with stage visualization and progress tracking
*   **ReportsLibraryModal**: Unified modal component for centralized report access with status badges
*   **Admin Interface**: Clean table layout with status badges and action buttons
*   **Toolbar Cleanup**: Removed duplicate report buttons from stage views for cleaner interface
*   **Consistent Dark Mode**: All new components support dark theme seamlessly
*   **Accessibility**: Proper disabled states and loading indicators

### 📚 Documentation Updates
*   **New**: [`docs/technical/GOVERNANCE_RULES.md`](docs/technical/GOVERNANCE_RULES.md) - Complete governance framework
*   **Updated**: System architecture diagrams with ownership boundaries
*   **Added**: Validation checklist for deployment integrity
*   **Updated**: BACKLOG_v3.8.md with implementation status

### 🔧 Backend Enhancements
*   **LockService**: Async service with database integration
*   **Lock Endpoints**: RESTful API at `/locks/*`:
    *   `POST /locks/acquire` - Acquire lock with session tracking
    *   `POST /locks/release` - Release lock by ID or project+process
    *   `POST /locks/check` - Check lock status
    *   `POST /locks/force-release` - Admin force-release
    *   `GET /locks/all` - List all active locks (admin only)
    *   `POST /locks/{lock_id}/force-release` - Force-release by ID
    *   `GET /locks/project/{project_id}` - Project lock history
*   **Error Handling**: HTTP 423 Locked status with detailed error messages
*   **Session Tracking**: User agent and IP logging for audit trail

### 🐛 Bug Fixes
*   **Fixed**: Lock service async/await errors (Supabase Python client is synchronous)
*   **Fixed**: Duplicate NavBar in profile page
*   **Fixed**: Code viewer expansion beyond viewport
*   **Fixed**: Error display showing `[object Object]` instead of formatted messages
*   **Fixed**: Workbench (Diff) tab removed from Refinement view (UI simplification)
*   **Fixed**: GitBranch icon reference error in RefinementView

### ⚡ Performance
*   **Lock Expiration**: Database-level RPC function for efficient stale lock cleanup
*   **Optimized Queries**: Indexed lock queries on project_id and process_type
*   **Threadpool Execution**: Reports run in threadpool for non-blocking generation

### 🎯 Architectural Principles
*   **Separation of Concerns**: Clear boundaries between ADMIN (infrastructure), TENANT (providers/cost), and USER (customization)
*   **Catalog Coherence**: Zero-tolerance for technology references outside the system catalog
*   **Multi-Tenant Cost Control**: Each tenant owns and controls their AI provider costs
*   **Data Integrity**: Process locking prevents race conditions and data corruption

### 📦 Report System
*   ✅ **Triage PDF Report**: Discovery analysis with asset statistics, PII detection, complexity assessment
*   ✅ **Final PDF Report**: Migration delivery report with outputs, timeline, and metadata
*   ✅ **Professional Templates**: Jinja2 templates with branding, watermarks, headers/footers
*   ✅ **Playwright Integration**: Headless Chrome for high-quality PDF generation
*   ✅ **Reports Library Modal**: Unified interface for all project reports with stage-aware availability
*   ✅ **Centralized Access**: Library icon (📚) in workspace header opens modal with all available reports
*   ✅ **Version-Agnostic Templates**: Report templates no longer include version numbers for maintenance-free updates
*   ✅ **Clean Stage Toolbars**: Report download buttons removed from stage views, centralized in Reports Library

### 🔐 Security
*   **Admin-Only Endpoints**: Force-release and list-all-locks require ADMIN role
*   **Session Validation**: Lock acquisition validates user session and tenant context
*   **Audit Trail**: All lock operations logged with user, timestamp, and IP address

### 🚀 Deployment Notes
*   **Database Migration**: Run `supabase_migrations/add_process_locks.sql` to create lock table
*   **RPC Function**: Deploy `expire_stale_locks()` function to Supabase
*   **Environment**: No new environment variables required
*   **Dependencies**: Existing Playwright and Jinja2 dependencies support reports

---

## Version 3.7 (The System & Identity Release) - 2026-02-06

This release solidifies the platform's multi-tenant architecture with a complete refactor of the System API, introducing dynamic agent management and strict identity controls.

### 🌟 Major Features

#### System Router Refactor (Phase 17)
*   **Centralized Configuration**: Moved all system-level endpoints to a dedicated `SystemRouter` (`/system/*`), separating administrative logic from core execution.
*   **Dynamic Agent Loading**: Agents are now loaded dynamically from the `utm_agent_catalog` database table, removing hardcoded references and allowing for runtime updates to the agent fleet.
*   **Strict Provider Vault**: The Provider Vault now strictly filters and displays only *configured and active* providers for the current tenant, effectively hiding irrelevant options.

#### Identity & Governance (Phase 18)
*   **Identity Management UI**: Full administrative control over Tenants, Users, and Clients directly from the `Platform Admin` > `Identity` tab.
*   **Environment Synchronization**: Introduced tooling (`sync_config.py`) to synchronize critical configuration data (Providers, Models, Matrix) between DEV and PROD environments.
*   **Enhanced Diagnostics**: New suite of diagnostic scripts (`check_providers_diag.py`, `check_users_diag.py`) to verify environment health and data persistence.

### 🐛 Bug Fixes
*   **Fixed**: 404 Errors on `/system` endpoints caused by missing router registration.
*   **Fixed**: "No prompt found" error in Strategy Canvas for newer agents.
*   **Fixed**: Discrepancy in Admin Page UI between DEV and PROD environments.

---

## Version 3.6 (Quality & Stability Enhancement) - 2026-02-03

### 🌟 Major Features

#### Compliance Rule Externalization (Phase 4)
*   **Database-Driven Compliance**: Moved hardcoded cartridge rules from Python code to `utm_system_catalog.config` for centralized management.
*   **Technology-Specific Rules**: Each target technology (Oracle, SSIS, Fabric, etc.) now stores its unique compliance guidelines in the database.
*   **Compliance Auditor Synchronization**: Updated compliance auditor to fetch rules dynamically, ensuring knowledge parity with code generators.
*   **Migration Bitácora**: Introduced auto-generated markdown logbooks that document Compliance Auditor critiques, scores, and reasoning for each migration file.

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
*   **Fault-Tolerant Exports**: AI-driven certification (Governance Agent) now runs with robust timeouts. If a report fails, the system delivers a technical package with placeholders instead of timing out the entire request.
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
    *   **Discovery Agent (The Architect)** now automatically infers operational metadata from source schemas:
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
    *   **Code Generator (The Interpreter)** now generates **optimized PySpark** based on Architect v2.0 metadata.
    *   **Auto-Partitioning**: If `partition_key` is detected, generates `.partitionBy(col)` automatically.
    *   **PII Masking**: Automatically applies `SHA2()` hashing for flagged columns.
    *   **Volume Optimization**: High-volume assets get shuffle-optimized joins.
*   **Transformation Logic Editor**:
    *   New **per-column custom expression** support in Column Mapping.
    *   Example: `CASE WHEN age < 18 THEN 'Minor'` auto-injected into generated code.
*   **Code Blueprint Preview**:
    *   Read-only preview of generated structure before transpilation runs.

#### Phase 7: AI-Driven Governance & SaaS Delivery
*   **Compliance Certification (Governance Agent)**:
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
    *   Code Generator replaces hardcoded paths with placeholders: `f"{S3_ROOT}/bronze/data"`.
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

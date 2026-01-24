# Release Notes

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
    *   **PII Tagging**: Direct integration with the auditor to ensure sensitive data is masked.
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

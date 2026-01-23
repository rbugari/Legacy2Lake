# Release Notes

## Version 2.0 Beta (Stabilization & Intelligence) - 2026-01-23

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

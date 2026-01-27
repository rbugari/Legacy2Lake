# Stage 1: Discovery (Technical Ingestion)

## 📌 Overview
The **Discovery** phase is the entry point for code ingestion. It performs a static analysis of the uploaded artifacts to generate a preliminary inventory.

## 🎯 Objectives
- Ingest source files (`.sql`, `.xml`, `.dtsx`, `.zip`).
- Identify technical signatures (Storage vs Logic vs Orchestration).
- Generate a `manifest.json` for the Triage phase.

## 👨‍💻 User Guide
1.  **Preparation**: Ensure your source files are accessible. Supports SQL Server, Oracle, SSIS, and flat files.
2.  **Upload**: Drag and drop your files into the "Drop Zone".
3.  **Run Discovery**: Click the button to start **Agent A (Analyst)**.
    - *Under the hood*: The agent parses headers, create statements, and file extensions to categorize assets.
4.  **Review**: A console log will show the scanning progress.
5.  **Proceed**: Once "Discovery Complete" appears, click **"Start Triage"** to move to classification.

## ⚙️ Technical Details
- **Service**: `DiscoveryService` / `LibrarianService`
- **Output**: `solutions/{project}/discovery/manifest.json`
- **Agents**: Agent A (Analyst) - Mode: `Scan`

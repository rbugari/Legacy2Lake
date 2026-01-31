# Stage 2: Triage (Strategy & Scoping)

## 📌 Overview
**Triage** is where the "noise" is filtered out. You define the **migration scope** by classifying assets into CORE, SUPPORT, or IGNORED.

## 🎯 Objectives
- Visual classification of assets.
- Dependency inference (Mesh Architecture).
- Risk and Complexity scoring.

## 👨‍💻 User Guide
### 1. Classification Canvas
- **CORE**: Business critical logic. Everything here *will* be migrated.
- **IGNORED**: Legacy backups, temp tables, logs.
- **SUPPORT**: Required for the build but not migrated directly (e.g., config files).

### 2. Actions
- **Drag & Drop**: Move items between columns to define scope.
- **Run Analysis**: Activates **Agent S (Strategist/Scout)**.
    - Calculates `Cyclomatic Complexity`.
    - Identifies `P1/P2/P3` criticality.
- **Graph View**: Switch to the Graph tab to see a visual dependency mesh.

### 3. Context Injection (Tribal Knowledge)
- Select any file to add "User Context".
- Example: *"This table is deprecated, map it to `sales_history` instead."*

## ⚙️ Technical Details
- **Service**: `DiscoveryService` / `ArchitectService`
- **Output**: Persistent metadata in `utm_objects` (JSONB `metadata` field).
- **Agents**: Agent A (Architect v2.0) - Mode: `Forensics`

### Metadata Forensics (v3.5)
In v3.5, Triage identifies **PII**, **Data Volumes**, and **Partition Keys** automatically using the Architect v2.0 engine. All inferred forensics are stored in Supabase with strict tenant isolation, ensuring that specific business context is never leaked between client projects.

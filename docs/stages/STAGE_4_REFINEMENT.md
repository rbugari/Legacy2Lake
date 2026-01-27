# Stage 4: Refinement (Modernization Factory)

## 📌 Overview
**Refinement** is the core execution engine. It transpiles legacy logic into high-performance, modern code implementing the **Medallion Architecture**.

## 🎯 Objectives
- Generate Bronze (Raw), Silver (Curated), and Gold (Business) layers.
- Optimize for the target platform (e.g., Databricks optimization).
- Self-Correction loop.

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
- **Service**: `RefactoringService`, `ProfilerService`
- **Output**: `solutions/{project}/refinement/`
- **Agents**: 
    - Agent C (Coder) - Mode: `Implement`
    - Agent F (Fixer) - Mode: `Debug`

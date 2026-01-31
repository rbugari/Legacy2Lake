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
- **Service**: `AgentCService`, `AgentFService`
- **Output Storage**: Cloudflare R2 (`{tenant_id}/{project_id}/Refinement/`)
- **Agents**: 
    - Agent C (The Interpreter) - Mode: `Synthesis`
    - Agent F (The Fixer) - Mode: `Optimization`

### Cloud-Scale Synthesis (v3.5)
In v3.5, code generation is decentralized. The backend streams generated code directly to **Cloudflare R2**. This bypasses local file system bottlenecks and allows for massive parallel generation across multiple agents. The Workbench diff view pulls original and generated files directly from R2 using `PersistenceService.read_file_content`.

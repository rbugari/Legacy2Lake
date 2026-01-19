# Shift-T (Release R1) - Modernization Platform

Shift-T is an AI-powered agentic platform designed to automate the migration of legacy SSIS packages to modern PySpark/Databricks architectures using an Execution Mesh approach.

## 🚀 Quick Start

To start the entire platform (Backend + Frontend), simply run:

```bash
python run.py
```

This script will start the FastAPI backend (Port 8000), the Next.js frontend (Port 3001), and open your dashboard.

## ✨ Key Features (Triage & Discovery)

We have recently enhanced the Discovery phase to provide a premium architecture design experience:

-   **Interactive Execution Mesh:** Dynamic graph visualization using React Flow and Dagre for auto-layout.
-   **Collapsible Workspace:** Hide/Show the assets sidebar to maximize architecture design space.
-   **Fullscreen Mode:** Dedicated "Maximize" view for immersive graph editing.
-   **Smart Triage:** Intelligent classification (CORE, SUPPORT, IGNORED) and dependency inference.
-   **Project Reset:** Ability to purge discovery data and restart the analysis from scratch.
-   **Editable Grid:** Mass-edit categories and sync changes instantly with the visual graph.
-   **Migration Persistence:** Real-time log persistence to view historical execution results (Log Replay).
-   **Workflow Toolbar:** Seamless stage transitions with "Approve & Refine" actions.
-   **Enhanced Dashboard:** Project cards with clear stage indicators, origin types, and asset counts.

## 📋 Prerequisites
-   Python 3.11+
-   Node.js 18+
-   Supabase Project (configured in `.env`)
-   Azure OpenAI Key (configured in `.env`)

## 🛠️ Components
-   **Frontend**: Next.js 14, React Flow (Mesh Design), Tailwind CSS.
-   **Backend**: FastAPI, Dagre (Layout Engine), Supabase.
-   **Agents**:
    -   **Agent A (Mesh Architect)**: Discovery and topology inference.
    -   **Agent C (Interpreter)**: Code transpilation to PySpark.
    -   **Agent F (Critic)**: Validation and optimization.

## 📖 Documentation
Detailed guides are available in the `/docs` folder:
-   [Fase 1: Triage & Discovery](docs/PHASE_1_TRIAGE.md)
-   [Fase 2: Drafting & Code Generation](docs/PHASE_2_DRAFTING.md)
-   [Fase 3: Refinement & Medallion Architecture](docs/PHASE_3_REFINEMENT.md)
-   [Fase 4: Governance & Compliance](docs/PHASE_4_GOVERNANCE.md)
-   [Technical Specification](docs/SPECIFICATION.md)

---
*Shift-T: Automating de-complexification.*

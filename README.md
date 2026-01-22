# Legacy2Lake 🚀 (Release 2.0 - The Style Master)

**Legacy2Lake** is an AI-augmented modernization platform that automates the transition from legacy ETL ecosystems (SSIS, Informatica, SQL) to modern Cloud Lakehouse architectures (Databricks, Snowflake).

## 🧠 Release 2.0 Highlights
- **Contextual Configuration**: "Solution Config" tabs embedded directly in Drafting and Refinement stages.
- **Technology Mixer**: Prominent UI to toggle between **PySpark**, **Pure SQL**, or **Mixed** generation modes.
- **Design Registry**: Enforce architectural standards (naming conventions, masking rules) via a global policy engine.
- **Expanded Workspace**: Optimized 80% width layout for engineering workflows.
- **Stage 4 Governance**: Automated lineage mapping and certification reports.

## 📖 Documentation
- **[Getting Started](docs/INTRODUCTION.md)**
- **[Roadmap & Future](docs/ROADMAP.md)**
- **[Phase 1: Triage](docs/PHASE_1_TRIAGE.md)**
- **[Phase 2: Drafting](docs/PHASE_2_DRAFTING.md)**
- **[Phase 3: Refinement](docs/PHASE_3_REFINEMENT.md)**
- **[Phase 4: Governance](docs/PHASE_4_GOVERNANCE.md)**
- **[Technical Specification](docs/SPECIFICATION.md)**

## ⚙️ Key Features

### 1. Technology Mixer
Located in the **Solution Config** tab, this allows you to choose the target output dialect:
- **PySpark Native**: Standard Delta Lake data engineering.
- **Pure SQL**: Legacy-friendly stored procedures and DDL.
- **Mixed / Dual**: Generate both dialects simultaneously for maximum flexibility.

### 2. Design Registry
Define your "Tribal Knowledge" once, apply it everywhere:
- **NAMING**: Prefixes for Bronze/Silver/Gold tables.
- **PATHS**: Root locations for ADLS/S3.
- **PRIVACY**: Default masking strategies (SHA256, Partial).

### 3. Multi-Agent Orchestration
- **Agent A (Architect)**: Designing the Medallion architecture.
- **Agent C (Coder)**: Generating high-fidelity PySpark/SQL code.
- **Agent F (Fixer)**: Self-healing refinement loops.

## 🛠 Quick Start
To launch the platform locally:
1. Ensure your `.env` is configured.
2. Run the unified launcher:
```bash
python run.py
```
3. Access the dashboard at `http://localhost:3005`.

---
*Powered by the Legacy2Lake Orchestration Engine.*

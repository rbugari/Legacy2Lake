# Legacy2Lake 🚀 (v3.5 - Configurable Architect)

**Legacy2Lake** is an AI-augmented modernization platform that automates the transition from legacy ETL ecosystems (SSIS, Informatica, SQL) to modern Cloud Lakehouse architectures (Databricks, Snowflake).

## 🧠 Core Capabilities (Rel 3.5)
- **Multi-Agent Orchestration**: Specialized agents (Detective, Cartographer, Interpreter, Critic) collaborating to build high-fidelity solutions.
- **Admin Panel & Global Config**: Centralized management for AI Agents, Prompts, and LLM Providers.
- **Database-First State**: Robust persistence using Supabase for all execution logs, file inventories, and settings.
- **Design Registry**: Global policy engine to enforce senior-architect standards (naming, paths, security) across the entire codebase.
- **Context Injection**: Incorporate "Tribal Knowledge" into the migration loop to generate **Virtual Steps**.

## 📖 Quick Links
- **[Getting Started: Introduction](docs/INTRODUCTION.md)**
- **[Project Roadmap & Versions](docs/FUTURE_RELEASES.md)**
- **[Phase 1: Triage & Discovery](docs/PHASE_1_TRIAGE.md)**
- **[Phase 2: Drafting](docs/PHASE_2_DRAFTING.md)**
- **[Phase 3: Refinement & Medallion](docs/PHASE_3_REFINEMENT.md)**
- **[Phase 4: Governance](docs/PHASE_4_GOVERNANCE.md)**
- **[Technical Architecture](docs/SPECIFICATION.md)**
- **[Admin Panel Walkthrough](docs/walkthrough_admin_panel.md)**

## ⚙️ General Configuration
Manage the platform behavior via the new **Admin Panel** (`/settings`):
- **Cartridges**: Enable/Disable generation engines (PySpark, dbt, SQL).
- **LLM Providers**: Configure Azure OpenAI / Anthropic keys.
- **Prompts**: Tune the system instructions for Agents A, C, F.

## 🛠 Quick Start
To launch the platform locally:
1. Ensure your `.env` is configured with Azure OpenAI and Supabase credentials.
2. Run the unified launcher:
```bash
python run.py
```
3. Access the dashboard at `http://localhost:3005`.

---
*Powered by the Legacy2Lake Orchestration Engine.*

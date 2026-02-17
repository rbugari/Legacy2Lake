# Legacy2Lake Documentation Index (v3.9 GA)

> **Version:** v3.9 GA (February 13, 2026) ✅ **RELEASED**  
> **Status:** Production Ready - Multi-User + Advanced Visualization Integration Complete

Welcome to the **Legacy2Lake** Documentation Center. Legacy2Lake is a **Cloud-Native, Multi-Tenant Data Modernization Factory** that automates the migration of legacy ETL logic to modern Snowflake, Databricks, and Fabric architectures using advanced AI synthesis.

## 🎉 What's New in v3.9 GA (Feb 13, 2026)

**Multi-User Collaboration** (Feb 10):
- ✔️ 4-role system (ADMIN, MANAGER, COLLABORATOR, VIEWER)
- ✔️ User Management UI with password reset
- ✔️ Project-level access control
- ✔️ Platform Admin Dashboard with Ghost Mode

**Visualization Integration** (Feb 13):
- ✔️ **Triage Dashboards**: Quality, Schema, PII, Partitioning (4 tabs)
- ✔️ **Drafting Quality**: Real-time monitoring during IR generation
- ✔️ **Refinement Suite**: Code Review, Schema, Quality, Performance (4 validation tabs)
- ✔️ 10 new visualization endpoints with graceful fallback
- ✔️ Enhanced launcher (`run.py`) with environment validation

**Value Delivered**: $240K of $400K V3.9 roadmap (60% complete)

## 🚀 Getting Started
- **[Installation Guide](docs/INSTALL.md)**: Setup instructions for Backend (API) and Frontend (Web Console).
- **[Release Notes](docs/RELEASE_NOTES.md)**: Latest updates and features.
- **[Introduction to Legacy2Lake](docs/INTRODUCTION.md)**: Vision, Architecture, and Lifecycle overview.
- **⚠️ [Environment Variables vs Database](docs/ENV_VS_DATABASE.md)**: **IMPORTANTE v3.9** - Configuración de .env vs credenciales en DB.

## ⚙️ Configuration (v3.9 Multi-User)

### 🔑 Roles & Responsibilities
- **[Roles and Onboarding](docs/ROLES_AND_ONBOARDING.md)**: Complete role hierarchy, onboarding flow, and impersonation guide.
  - **ADMIN**: Platform-level (manages global catalogs, creates tenants, can impersonate users)
  - **MANAGER**: Tenant-level (configures LLM providers, manages spending, invites users)
  - **COLLABORATOR**: Project-level (creates and edits projects)
  - **VIEWER**: Project-level (read-only access)

### 📦 Catalogs Architecture

**Global Catalogs (ADMIN manages)**:
- **utm_agent_catalog**: AI Agents (Agent S, Agent A, Agent B, etc.)
- **utm_system_catalog**: Technology Cartridges (SQL Server, Oracle, Snowflake, Databricks)

**Tenant-Level Catalogs (MANAGER configures)**:
- **utm_provider_vault**: LLM Provider API Keys (OpenAI, Groq, Azure) - Each tenant pays for their own
- **utm_model_catalog**: Enabled LLM Models (gpt-4o, claude-3-5, etc.) - Private per tenant

⚠️ **IMPORTANTE**: LLM credentials (API keys) are NO LONGER in `.env` - they're in the database per tenant.

See: **[ENV_VS_DATABASE.md](docs/ENV_VS_DATABASE.md)** for migration guide.

## 🔄 Project Lifecycle (The 6 Stages)

Legacy2Lake utilizes a 6-stage "Compiler Flow" to ensure logic is extracted correctly, refined by AI, and packaged for production.

1.  **[Stage 1: Discovery (Ingest)](docs/stages/STAGE_1_DISCOVERY.md)**
    - Technical ingestion to Cloudflare R2 and initial inventory.
2.  **[Stage 2: Triage (Strategy)](docs/stages/STAGE_2_TRIAGE.md)**
    - Forensic analysis (PII, Volume detection).
    - **New**: Native **Process Cancellation** for long-running analyses.
3.  **[Stage 3: Drafting (Plan)](docs/stages/STAGE_3_DRAFTING.md)**
    - Normalization into Intermediate Representation (IR) in Supabase.
4.  **[Stage 4: Refinement (Build)](docs/stages/STAGE_4_REFINEMENT.md)**
    - AI-driven code generation with dynamic **Knowledge Injection**.
    - **New**: **Strategic Intelligence Hub** with "Vision Mode" for architectural inspection.
5.  **[Stage 5: Certification (Audit)](docs/stages/STAGE_5_CERTIFICATION.md)**
    - Cloud-native compliance scoring and quality gating.
6.  **[Stage 6: Handover (Deliver)](docs/stages/STAGE_6_HANDOVER.md)**
    - Certified Output Package (COP) generation via Signed URLs.

## 🧠 AI Infrastructure & Prompt Lab
- **[System Prompts & Agents](docs/technical/system_prompts_and_agents.md)**: Agent roles and core prompts.
- **[Knowledge Injection Guide](knowledge_injection_guide.md)**: How agents are enriched with platform best practices.
- **[Cartridge Manual](docs/technical/cartridge_manual.md)**: Rules for the 15+ supported technology cartridges.
- **[Governance Rules](docs/technical/GOVERNANCE_RULES.md)**: 🆕 Ownership model, permission boundaries, and cost control framework.

## 📊 Cloud-Native Advantage (v3.8)
- **Zero-Trust Multi-Tenancy**: Asset isolation via Supabase RLS (Tenant Headers enforced).
- **Formalized Governance Model**: Clear ownership boundaries between Admin, Tenant, and User responsibilities.
- **3-Layer Prompt Architecture**: System prompts (Admin) + Cartridge prompts (Admin) + Custom modifiers (User).
- **Cost Control Framework**: Tenant-level model assignment with cost optimization recommendations.
- **Refactored API Architecture**: Modular System Router (`/system/*`) for centralized configuration management.
- **Dynamic Agent Management**: Agent catalog and prompts loaded from database, eliminating hardcoded logic.
- **Enhanced Provider Vault**: Strict filtering to display only active, configured providers per tenant.
- **Hyperscale Storage**: All artifacts stored in high-availability Cloudflare R2.

---
*Legacy2Lake Documentation Framework v3.9 GA - Multi-Tenant Enterprise Edition with Advanced Visualization*
*Released: February 13, 2026*

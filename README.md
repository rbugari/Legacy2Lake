# Legacy2Lake Documentation Index (v4.0 GA)

> **Version:** v4.0.1 GA (February 25, 2026) ✅ **RELEASED**  
> **Status:** Production Ready - Zero-Hardcode Architecture, Two-Layer Prompts & Discovery Enhancements

Welcome to the **Legacy2Lake** Documentation Center. Legacy2Lake is a **Cloud-Native, Multi-Tenant Data Modernization Factory** that automates the migration of legacy ETL logic to modern Snowflake, Databricks, and Fabric architectures using advanced AI synthesis.

## 🎉 What's New in v4.0.1 GA (Feb 2026)
 
**Two-Layer Prompt Architecture** (Feb 25):
- ✔️ **Core System Safety**: Global system prompts locked for safety.
- ✔️ **Project-Specific Overrides**: Authorized users can now supply project-level rule amendments.
- ✔️ **Dynamic Assembly**: Cartridges dynamically join core rules and overrides right before execution.

**Identity & Governance Governance** (Feb 25):
- ✔️ **Role-Based Visibility limits**: Collaborators and Viewers only see assigned projects.
- ✔️ **Admin Impersonation**: Admins bypass tenant boundaries for full platform visibility and troubleshooting.

**Zero-Hardcode Architecture** (Feb 15):
- ✔️ **Database-Driven Parser Registry**: Add new tech (Talend, Oracle) via DB inserts, ZERO code changes.
- ✔️ **Dynamic Prompt Management**: All prompts (Agent A, B, C, F, G) loaded from database.
- ✔️ **Automatic Versioning**: `utm_prompts_history` tracks all prompt changes.
 
**Robust Discovery & UI Componentization** (Feb 24-25):
- ✔️ **Pre-Classification Grid**: Categorize assets individually as CORE, SUPPORT, or IGNORE prior to triage. 
- ✔️ **Robust Folder Heuristics**: Dynamic scanning gracefully identifies historical ("triage") or new ("source") directory definitions natively.
- ✔️ **Unified File & Log Explorers**: Replaced disparate implementations with unified components.
- ✔️ **Sidebar Execution Ecosystem**: Moved actions to Sidebar for a cleaner focus.
 
**Value Delivered**: Scale multi-tenant migrations with highly confident discovery classification and uncompromised core code safety.

### ⏳ Pending to Close v4.0 GA
1. **Client GitHub Integration**: Export mapped outputs directly to a target client GitHub repository for final deployment.
2. **Review PDF Reports**: Visual review of formatting, tables, and variable integrations in exported final status PDF reports.
3. **Comprehensive Testing Plan**: Full validation of all updated flows via end-to-end multi-tenant simulation testing.

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
*Legacy2Lake Documentation Framework v4.0.1 GA - Zero-Hardcode, Deep RBAC, Pre-Classification*
*Released: February 25, 2026*

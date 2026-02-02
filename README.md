# Legacy2Lake Documentation Index (v3.5)

Welcome to the **Legacy2Lake** Documentation Center. Legacy2Lake is a **Cloud-Native, Multi-Tenant Data Modernization Factory** that automates the migration of legacy ETL logic to modern Snowflake, Databricks, and Fabric architectures using advanced AI synthesis.

## 🚀 Getting Started
- **[Installation Guide](docs/INSTALL.md)**: Setup instructions for Backend (API) and Frontend (Web Console).
- **[Release Notes](docs/RELEASE_NOTES.md)**: Details on the v3.5 cloud-native reset.
- **[Introduction to Legacy2Lake](docs/INTRODUCTION.md)**: Vision, Architecture, and Lifecycle overview.

## 🔄 Project Lifecycle (The 6 Stages)

Legacy2Lake utilizes a 6-stage "Compiler Flow" to ensure logic is extracted correctly, refined by AI, and packaged for production.

1.  **[Stage 1: Discovery (Ingest)](docs/stages/STAGE_1_DISCOVERY.md)**
    - Technical ingestion to Cloudflare R2 and initial inventory.
2.  **[Stage 2: Triage (Strategy)](docs/stages/STAGE_2_TRIAGE.md)**
    - Forensic analysis (PII, Volume detection) and technology scoping.
3.  **[Stage 3: Drafting (Plan)](docs/stages/STAGE_3_DRAFTING.md)**
    - Normalization into Intermediate Representation (IR) in Supabase.
4.  **[Stage 4: Refinement (Build)](docs/stages/STAGE_4_REFINEMENT.md)**
    - AI-driven code generation with dynamic **Knowledge Injection**.
5.  **[Stage 5: Certification (Audit)](docs/stages/STAGE_5_CERTIFICATION.md)**
    - Cloud-native compliance scoring and quality gating.
6.  **[Stage 6: Handover (Deliver)](docs/stages/STAGE_6_HANDOVER.md)**
    - Certified Output Package (COP) generation via Signed URLs.

## 🧠 AI Infrastructure & Prompt Lab
- **[System Prompts & Agents](docs/technical/system_prompts_and_agents.md)**: Agent roles and core prompts.
- **[Knowledge Injection Guide](knowledge_injection_guide.md)**: How agents are enriched with platform best practices.
- **[Cartridge Manual](docs/technical/cartridge_manual.md)**: Rules for the 15+ supported technology cartridges.

## 🛠 Project Maintenance
- **[Database Cleanup Utility](scripts/db_cleanup.py)**: Automated orphan removal and R2 storage sync.
- **[Database Cleanup Guide](database_cleanup_guide.md)**: Operations manual for maintenance scripts.

## 📊 Cloud-Native Advantage (v3.5)
- **Zero-Trust Multi-Tenancy**: Asset isolation via Supabase RLS and Cloudflare R2 prefixes.
- **Prompt Laboratory**: Dynamic knowledge enrichment (MERGE, Delta patterns, SCD Type 2).
- **Hyperscale Storage**: All artifacts stored in high-availability Cloudflare R2.
- **Parallel Synthesis**: Concurrent AI generation via `asyncio` and optimized LLM context.

---
*Legacy2Lake Documentation Framework v3.5 - Multi-Tenant Enterprise Edition*

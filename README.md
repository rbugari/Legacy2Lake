# Legacy2Lake Documentation Index (v3.5)

Welcome to the **Legacy2Lake** Documentation Center. Legacy2Lake is a **Cloud-Native, Multi-Tenant Data Modernization Factory** that automates the migration of legacy ETL logic to modern Snowflake, Databricks, and Fabric architectures.

## 🚀 Getting Started
- **[Installation Guide](docs/INSTALL.md)**: Setup instructions for Backend (API) and Frontend (Web Console).
- **[Release Notes](docs/RELEASE_NOTES.md)**: Details on the v3.5 cloud-native reset.
- **[Introduction to Legacy2Lake](docs/INTRODUCTION.md)**: Vision, Architecture, and Lifecycle overview.

## 🔄 Project Lifecycle (The 6 Stages)

Legacy2Lake utilizes a 6-stage "Compiler Flow" to ensure logic is extracted correctly, refined by AI, and packaged for production.

1.  **[Stage 1: Discovery (Ingest)](docs/stages/STAGE_1_DISCOVERY.md)**
    - Technical ingestion to Cloudflare R2 and initial inventory.
2.  **[Stage 2: Triage (Strategy)](docs/stages/STAGE_2_TRIAGE.md)**
    - Forensic analysis (PII, Volume detection) and scoping.
3.  **[Stage 3: Drafting (Plan)](docs/stages/STAGE_3_DRAFTING.md)**
    - Normalization into Intermediate Representation (IR) in Supabase.
4.  **[Stage 4: Refinement (Build)](docs/stages/STAGE_4_REFINEMENT.md)**
    - AI-driven code generation and iterative "Fixer" loops.
5.  **[Stage 5: Certification (Audit)](docs/stages/STAGE_5_CERTIFICATION.md)**
    - Cloud-native compliance scoring and quality gating.
6.  **[Stage 6: Handover (Deliver)](docs/stages/STAGE_6_HANDOVER.md)**
    - Certified Output Package (COP) generation via Signed URLs.

## 🛠 Technical Reference
- [Cloud-Native Architecture](docs/technical/architecture.md)
- [Multi-Tenant Data Model](docs/technical/data_model.md)
- [API Contract](docs/technical/api_contract.md)
- [System Prompts & Agents](docs/technical/system_prompts_and_agents.md)
- [Future Releases & Roadmap](docs/ROADMAP.md)

## 📊 Cloud-Native Advantage (v3.5)
- **Zero-Trust Multi-Tenancy**: Complete asset isolation via Supabase RLS and Cloudflare R2 tenant-prefixes.
- **Hyperscale Storage**: No more local disk bottlenecks—all artifacts are stored in R2.
- **Parallel Synthesis**: `asyncio`-driven backend ensures concurrent AI generation and packaging.
- **Direct-to-Cloud Delivery**: High-performance downloads using S3-compatible Signed URLs.

---
*Legacy2Lake Documentation Framework v3.5 - Multi-Tenant Enterprise Edition*

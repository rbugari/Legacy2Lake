# Legacy2Lake Documentation Index (v3.2)

Welcome to the **Legacy2Lake** Documentation Center. This directory contains detailed guides for every phase of the intelligent data modernization process.

## 🚀 Getting Started
- **[Installation Guide](INSTALL.md)**: Setup instructions for Backend and Frontend.
- **[Release Notes](RELEASE_NOTES.md)**: What's new in the latest version.
- **[Introduction to Legacy2Lake](INTRODUCTION.md)**: Vision, Architecture, and Lifecycle overview.

## 🔄 Project Lifecycle (Phase-by-Phase)

The modernization process is orchestrated through **NINE critical phases**:

### Core Phases
1.  **[Phase 1: Triage & Discovery](PHASE_1_TRIAGE.md)**
    - Repository scanning, asset classification, and orchestration mesh design.
2.  **[Phase 2: Drafting & Code Generation](PHASE_2_DRAFTING.md)**
    - Automatic PySpark notebook generation and code quality auditing.
3.  **[Phase 3: Refinement & Medallion](PHASE_3_REFINEMENT.md)**
    - Transformation into Medallion architecture (Bronze/Silver/Gold) and security hardening.
4.  **[Phase 4: Governance & Compliance](PHASE_4_GOVERNANCE.md)**
    - Modernization certificates, lineage mapping, and solution bundle delivery.

### Enterprise Suite (v3.2)
5.  **[Phase 5: Architect v2.0 & Discovery Heatmaps](PHASE_5_ARCHITECT.md)** ⭐ NEW
    - Automated metadata inference (Volume, PII, Latency, Partition Keys).
    - Visual intelligence: PII Exposure and Criticality heatmaps in Discovery UI.
6.  **[Phase 6: Intelligent Code Generation](PHASE_6_INTELLIGENCE.md)** ⭐ NEW
    - Context-aware PySpark generation using Architect v2.0 metadata.
    - Auto-optimization: partitioning, PII masking, custom transformation logic.
7.  **[Phase 7: AI-Driven Governance & SaaS Delivery](PHASE_7_GOVERNANCE_DELIVERY.md)** ⭐ NEW
    - Compliance audit with 0-100 scoring (Agent G).
    - Automated Runbook generation (`Modernization_Runbook.md`).
    - Complete export bundle with variable manifest.
8.  **[Phase 8: Variable Injection Framework](PHASE_8_VARIABLES.md)** ⭐ NEW
    - Environment-agnostic code generation using placeholders (e.g., `${S3_ROOT}`).
    - Centralized variable management in Project Settings.
9.  **[Phase 9: Data Quality Contracts (Optional)](PHASE_9_QUALITY.md)** ⭐ NEW
    - Auto-generated Great Expectations & Soda validation suites.
    - Derived from Column Mapping metadata (nullable, PII, data types).

## 🛠 Technical Reference
- [Platform Architecture](technical/architecture.md) - Updated with v3.2 agents
- [Metadata Store (Data Model)](technical/data_model.md) - Includes Architect v2.0 fields
- [API Contract](technical/api_contract.md) - v3.2 endpoints for variables, quality, governance
- [System Prompts & Agents](technical/system_prompts_and_agents.md) - Agent capabilities breakdown
- [Universal IR Grammar](technical/universal_ir.md)
- [Cartridge Development Manual](technical/cartridge_manual.md)
- [Function Registry](technical/function_registry.md)
- [Test Scenarios](technical/test_scenarios.md)
- [AI Infrastructure (Multi-LLM)](technical/ai_infrastructure.md)
- **[Future Releases & Roadmap](ROADMAP.md)** - Backlog and deferred features

## 📊 What's New in v3.2?

**Enterprise Modernization Suite:**
- **Forensic Intelligence**: Automatic Volume, PII, and Partition detection
- **Smart Generation**: AI-optimized code based on data characteristics
- **Certification**: Compliance scoring and automated runbook delivery
- **Parameterization**: Environment-agnostic artifacts via variable injection
- **Quality Assurance**: Optional GX/Soda contracts for data validation

---
*Legacy2Lake Documentation Framework v3.2 - Enterprise Ready*

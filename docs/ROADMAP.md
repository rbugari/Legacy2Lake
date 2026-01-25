# Project Roadmap 🗺️

> [!NOTE]
> **Product Strategy**: Legacy2Lake operates as a high-fidelity **Artifact Generator**. Our roadmap focuses on generating production-ready code, IaC, and Orchestration manifests while maintaining a zero-access security posture relative to client infrastructure.

## � Future Backlog (Post-v3.2)

### Phase E: Infrastructure as Code (IaC) - **DEFERRED**
- [ ] **Terraform/Bicep Generation**: Auto-generate IaC for Cloud Storage, Databricks Clusters, and Secrets Managers.
- [ ] **Network & Security Provisioning**: Automate VNet injection.

### Phase G: Real-time Modernization - **DEFERRED**
- [ ] **Delta Live Tables (DLT)**: Streaming-ready pipelines.
- [ ] **CDC Pattern Automation**: Merge/Upsert patterns for real-time ingest.

### Phase H: Multi-Dialect Expansion - **DEFERRED**
- [ ] **Informatica/DataStage**: XML exports support.
- [ ] **PL/SQL Modernization**: Oracle package conversion.

## 📦 Delivered Scope (v3.2)
The **Enterprise Modernization Suite** is feature complete for the core artifact generation use case. Focus is on high-fidelity PySpark, Governance, and Parameterized Delivery.

## 📅 Release History

### v3.2 (The Enterprise Modernization Suite) - LATEST
- **Architect v2.0**: Automated inference of partitioning, volume, and latency.
- **Discovery Analytics**: Real-time heatmaps for PII and Business Criticality.
- **Governance Audit (Agent G)**: AI-driven compliance scoring and automated Runbook generation.
- **High-Fidelity Generation**: Context-aware PySpark code with partition-by and PII masking support.
- **Variable Injection**: Dynamic Environment parameterization (e.g. `${S3_ROOT}`).
- **Data Quality**: Auto-generated Great Expectations & Soda validation suites.

### v3.1 (The Discovery Gate & Management Hub) 

### v3.0 (The Enterprise Compliance Hub)
- **AI Audit Engine**: Automated architectural reviews with scoring and suggestions.
- **Column Mapping Editor**: Detailed field-level mapping with business context.
- **Universal Orchestration**: Airflow, Databricks, and YAML DAG generation.
- **Project Export**: ZIP bundle generation with all modernization artifacts.
- **Glassmorphism UI**: Premium visual overhaul (Purple accent theme).

### v2.0 (The Style Master)
- **Contextual Config**: Embedded "Solution Config" tabs in Drafting and Refinement.
- **Technology Mixer**: UI toggles for PySpark, Pure SQL, or Mixed generation.
- **Design Registry**: Global policy engine for naming and paths.
- **Expanded Layout**: 80% width optimization for engineering workflows.

### v1.5: Governance & Lineage
- **Lineage Mapper**: Mapping legacy artifacts to OpenLineage-compliant targets.
- **Certification**: Automated compliance scores.

### v1.0 - v1.3: The Contextual Architect
- **Context Injection**: "Virtual Steps" for business logic.
- **Operational Intelligence**: Automated load strategy and PII detection.
- **Base Registry**: Initial implementation of naming conventions.

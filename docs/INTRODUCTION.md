# Welcome to Legacy2Lake 🚀

**Legacy2Lake** (v3.6) is a **Cloud-Native, Multi-Tenant AI-Augmented Data Engineering Platform** that automates and optimizes the transition from legacy architectures (Traditional ETL) to modern Cloud Lakehouse ecosystems (ELT/ETLT).

> **v3.6 Latest**: Adds UI refinements (resizable drafting explorer), pipeline stability (cartridge sync fix), and compliance improvements (dynamic rules from database).

## 1. The Vision: "Shift the T" 🧬

The core concept of **Legacy2Lake** is mathematically simple but strategically profound: **Move the Transformation**.

In traditional ETL (Extract, Transform, Load), the "T" happens in a rigid, intermediate middleware server which often becomes a bottleneck. In the **Legacy2Lake** model, we shift that logic to execute directly on elastic, distributed cloud processors (like Spark or Snowflake). This eliminates data movement latency and allows organizations to scale analytical capacity independently of data volume.

---

## 2. Core Architecture: The Three-Layer Engine ⚙️

To solve the complexity of $N$ source technologies and $M$ target platforms, Legacy2Lake uses a decoupled **Compiler Model**:

### A. Ingestion Layer (The Ear)
- **Mission**: Read the original artifact (DTSX, SQL, etc.) and extract raw metadata.
- **Component**: **Input Cartridges** (e.g., `SSISCartridge`).
- **Output**: Structured, non-normalized metadata.

### B. Universal Kernel (The Brain)
- **Mission**: Normalize raw metadata into a **Universal Intermediate Representation (IR)**.
- **Component**: Logic Mapper & Canonical Function Registry.
- **Output**: A platform-agnostic JSON-IR stored in the Metadata Store.

### C. Synthesis Layer (The Voice)
- **Mission**: Translate the Universal IR into the target language and platform.
- **Component**: **Output Cartridges** (e.g., `DatabricksCartridge`).
- **Output**: Executable source code (PySpark Notebooks, SQL Scripts).

### D. Administration Layer (The Control Tower)
- **Mission**: Centralized management of Agent behavior, Prompts, and Cloud Providers.
- **Component**: **Admin Panel** & `utm_global_config`.
- **Output**: Dynamic runtime configuration for the entire fleet.

### E. Cloud-Native Storage (v3.6)
- **Mission**: Hyperscale object storage with zero local disk dependency.
- **Component**: **Cloudflare R2** (S3-compatible) + **Supabase** metadata cache.
- **Features**:
  - **R2 Storage**: All source artifacts, generated code, and packages stored in object storage
  - **Tenant Isolation**: Per-tenant prefixes (`tenant-{id}/`) ensure complete data isolation
  - **File Inventory**: `utm_file_inventory` table provides fast listing without S3 API calls
  - **Signed URLs**: Secure, time-limited download links for artifact delivery

### F. Multi-Tenancy & Security (v3.6)
- **Zero-Trust Architecture**: Row-Level Security (RLS) policies enforce tenant isolation
- **Provider Vault**: Encrypted API keys stored in `utm_provider_vault` per tenant
- **Agent Matrix**: Each tenant configures their own LLM model assignments
- **Audit Trail**: Complete execution logs in `utm_execution_logs` per project

---

## 3. The Agentic Workforce 🤖

The platform operates via specialized agents that interact through the Metadata Store:

| Agent | Role | Responsibility |
| :--- | :--- | :--- |
| **Scout (Agent S)** | **Technology Detection** | Analyzes repositories during triage to detect source technology (SQL Server, Oracle, SSIS, etc.). |
| **Detective (Agent A)** | **Discovery** | Scans repositories and identifies technology footprints and complexity. |
| **Cartographer (Agent B)** | **Mesh & Lineage** | Builds the execution graph and precedence constraints. |
| **Interpreter (Agent C)** | **Transpiler** | The main execution engine. Writes code using target-specific patterns. |
| **Critic (Agent F)** | **QA & Refinement** | Senior architect that optimizes code for performance and security. |
| **Governor (Agent G)** | **Governance** | Generates modernization certificates and column-level lineage. |

### Prompt Laboratory (v3.6)

Legacy2Lake v3.6 continues the **dynamic prompt management system** introduced in v3.5, with enhanced compliance rule management:

- **Core Agents**: 7 system prompts for A, B, C, D, F, G, S
- **Origin Knowledge**: 9 source technology prompts (SSIS, SQL Server, Oracle, DataStage, Informatica, SAP BODS, Talend, Pentaho, MySQL)
- **Destination Knowledge**: 6 target platform prompts (Databricks/PySpark, Snowflake, Microsoft Fabric, BigQuery, Redshift, Salesforce)
- **Configuration per Tech**: Each technology has a `config_v1.json` defining dialect-specific instructions
- **Versioning**: Prompts support v1, v2, etc. for A/B testing and rollback
- **Export/Import**: Complete prompt packages can be exported as ZIP for sharing or backup

## 4. The 6-Stage Lifecycle 🔄

1.  **Stage 1: Discovery (Ingest)**
    - Repository scanning and technical asset identification.
2.  **Stage 2: Triage (Strategy)**
    - Scope definition and dependency mesh construction.
3.  **Stage 3: Drafting (Plan)**
    - Architectural blueprinting (Logic Mapping).
4.  **Stage 4: Refinement (Build)**
    - Code synthesis, transpilation, and self-correcting optimization loops.
5.  **Stage 5: Certification (Audit)**
    - Security scanning, compliance scoring, and quality auditing.
6.  **Stage 6: Handover (Deliver)**
    - Variable injection, Runbook generation, and final Golden Bundle export.

---

## 5. Advanced Concepts 🧠

For deep-technical details, refer to our specialized reference guides:

- **[Platform Architecture](technical/architecture.md)**: Deep dive into the 3-layer decoupled model.
- **[Metadata Store (Data Model)](technical/data_model.md)**: Explore the UTM database schema.
- **[Universal IR Grammar](technical/universal_ir.md)**: The JSON schema used for cross-platform logic.
- **[Cartridge Developer Manual](technical/cartridge_manual.md)**: How to build new input/output modules.
- **[Function Registry](technical/function_registry.md)**: Mapping logic between legacy and cloud functions.

---
> [!TIP]
> **Legacy2Lake** is designed with a "Human-in-the-Loop" philosophy. The AI proposes the architecture, but the User maintains total control via overrides in the Metadata Store.

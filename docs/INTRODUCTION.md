# Welcome to Legacy2Lake 🚀

**Legacy2Lake** is an AI-augmented Data Engineering platform designed to automate and optimize the transition from legacy architectures (Traditional ETL) to modern Cloud Lakehouse ecosystems (ELT/ETLT).

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

---

## 3. The Agentic Workforce 🤖

The platform operates via specialized agents that interact through the Metadata Store:

| Agent | Role | Responsibility |
| :--- | :--- | :--- |
| **Detective (Agent A)** | **Discovery** | Scans repositories and identifies technology footprints and complexity. |
| **Cartographer (Agent B)** | **Mesh & Lineage** | Builds the execution graph and precedence constraints. |
| **Interpreter (Agent C)** | **Transpiler** | The main execution engine. Writes code using target-specific patterns. |
| **Critic (Agent F)** | **QA & Refinement** | Senior architect that optimizes code for performance and security. |
| **Governor (Agent G)** | **Governance** | Generates modernization certificates and column-level lineage. |

---

## 4. The 4-Phase Lifecycle 🔄

1.  **Phase 1: Triage & Discovery**
    - Repository scanning and asset classification (Core/Support/Ignore).
2.  **Phase 2: Drafting & Code Generation**
    - Automatic generation of the first code draft (The "Ear to Voice" transition).
3.  **Phase 3: Refinement & Medallion**
    - Transitioning drafts into a structured **Medallion Architecture** (Bronze, Silver, Gold).
4.  **Phase 4: Governance & Compliance**
    - Final certification, lineage mapping, and delivery of the **Solution Bundle**.

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

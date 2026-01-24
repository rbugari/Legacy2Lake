# Technical Architecture: The Compiler Model

Legacy2Lake (formerly UTM) is a data logic transpilation platform designed to decouple business intent from its technical implementation. Unlike a point-to-point converter, the platform extracts the "DNA" of ETL processes and stores it in an agnostic Intermediate Representation (IR).

## 1. The Three-Layer Compiler Model

To resolve the $N \times M$ complexity problem, Legacy2Lake implements a total decoupling architecture:

### A. Ingestion Layer (Front-End)
- **Mission**: Read the original artifact (XML, SQL, etc.) and extract raw metadata.
- **Components**: Technology-specific **Input Cartridges** (e.g., `SSISCartridge`).
- **Output**: Structured, non-normalized metadata.

### B. Universal Kernel (Mid-End / IR)
- **Mission**: Normalize raw metadata into the **Universal Metadata Schema**.
- **Components**: Logic inference engine and **Canonical Function Registry**.
- **Output**: Persisted records in the Metadata Store (`UTM_Logical_Step`) as JSON-IR.

### C. Synthesis Layer (Back-End / Cartridges)
- **Mission**: Translate the JSON-IR into the target language and platform.
- **Components**: Technology **Output Cartridges** based on Jinja2 templates (e.g., `DatabricksCartridge`).
- **Output**: Executable source code (Notebooks, SQL Scripts).

## 2. Multi-Agent System (MAS v3.0)

The system operates via specialized AI agents interacting through the metadata store and the file system:

| Agent | Name | Role | Responsibility |
| :--- | :--- | :--- | :--- |
| **A** | **The Architect** | Inference & Triage | Scans the repo, identifies assets, and builds the dependency graph (`READS_FROM`, `SEQUENTIAL`). Inference of business intent from file names. |
| **C** | **The Interpreter** | Code Generation | Converts legacy logic (XML/SQL) into modern PySpark/SQL code. This is the "Compiler" working on individual units. |
| **F** | **The Fixer** | QA & Refinement | Reviews Agent C's output. Checks for syntax errors and applies "Design Registry" patterns (e.g. naming conventions). |
| **G** | **The Guardian** | Governance | Generates technical documentation, data lineage, and deployment artifacts (ZIP bundles, DAGs). |
| **D** | **The Auditor** | Compliance (New) | Performs deep architectural reviews. Scores code on Idempotency, Medallion Compliance, and PII Security. |

### Interaction Model
1. **Agent A** builds the map.
2. **Agent C** drafts the code for each node.
3. **Agent F** refines the code iteratively.
4. **Agent D** audits the final artifact.
5. **Agent G** packages everything for deployment.

## 3. System Data Flow

1. **Artifact Ingestion**: A user loads an `.dtsx` (SSIS) file.
2. **DNA Analysis**: The Parser identifies components like "Lookup" and "Derived Column".
3. **Normalization**: The Kernel translates the "Lookup" into a **JOIN** object and the "Derived Column" into a **TRANSFORM** object in the IR.
4. **Persistence**: Logic is saved in the `UTM_Logical_Step` table.
5. **Human-in-the-Loop**: The user reviews the logic in the UI and adjusts if necessary (e.g., changing a data type).
6. **Cartridge Execution**: The user selects "Databricks" and the Generator assembles code using templates.

## 4. Design Principles

- **Total Agnosticism**: The core doesn't know what a Spark "DataFrame" or a Snowflake "CTE" is. It only understands "Joins", "Filters", and "Canonical Data Types".
- **Extensibility**: Adding a new source or target only requires creating a new Cartridge module, without changing the Kernel's code.
- **Traceability**: Every line of generated code can be traced back to its original component in the legacy system.

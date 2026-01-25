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

## 2. Multi-Agent System (MAS v3.2)

The system operates via specialized AI agents interacting through the metadata store and the file system:

| Agent | Name | Role | Responsibility |
| :--- | :--- | :--- | :--- |
| **S** | **The Scout** | Validation (Phase 4) | Initial repository scan. Validates source technology, identifies context gaps, and suggests missing mission-critical files. |
| **A** | **The Architect v2.0** | Forensics & Inference (Phase 5) | Scans repo, builds dependency graph, **infers metadata** (Volume, PII, Latency, Partition Keys). Generates Discovery Heatmaps. |
| **C** | **The Interpreter** | Context-Aware Generation (Phase 6) | Converts legacy logic into modern PySpark/SQL code. Uses Architect v2.0 metadata for **auto-optimization** (partitioning, PII masking). Supports **Variable Injection** (Phase 8). |
| **F** | **The Fixer** | QA & Refinement | Reviews Agent C's output. Checks for syntax errors and applies "Design Registry" patterns. |
| **G** | **The Guardian** | AI-Driven Certification (Phase 7) | Performs **compliance audit** (0-100 score), generates **Runbook.md**, bundles **Variable Manifest**, and optionally includes **Data Quality Contracts** (Phase 9). |
| **D** | **The Auditor** | Compliance (Legacy) | Deep architectural reviews. Scores code on Idempotency and PII. *(Note: Functionality migrated to Agent G in v3.2)* |

### New Services (v3.2)

| Service | File | Purpose |
| :--- | :--- | :--- |
| **ArchitectService** | `architect_service.py` | Metadata inference engine (Volume, PII, Partition Keys) |
| **QualityService** | `quality_service.py` | Generates Great Expectations & Soda validation suites from Column Mappings |
| **GovernanceService** | `governance_service.py` | Enhanced with AI audit, runbook generation, and export bundling |


### Interaction Model (Modernized)
1. **Agent S** performs the "Discovery Gate" check (Tech validation + Gap analysis).
2. **Agent A** builds the map after the user validates the Scout's report.
3. **Agent C** drafts the code for each node.
4. **Agent F** refines the code iteratively.
5. **Agent D** audits the final artifact.
6. **Agent G** packages everything for deployment.

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

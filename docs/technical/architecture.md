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

## 2. Agentic Orchestration

The system operates via specialized agents interacting through the metadata store:

| Agent | Responsibility |
| :--- | :--- |
| **Detective** | Identifies new files in the source repository and registers them. |
| **Parser** | Deconstructs the XML/SQL and extracts raw processing logic. |
| **Kernel** | Translates raw logic to the Universal IR grammar and resolves functions. |
| **Critic (QA)** | Validates that the logical flow is consistent and flags incompatibilities. |
| **Generator** | Takes the approved IR and the selected cartridge to produce final code. |

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

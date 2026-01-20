# **Legacy2Lake Project: Intelligent Data Modernization Framework**

## **1. Vision and Purpose**

**Legacy2Lake** is an AI-augmented data engineering platform designed to automate and optimize the transition from legacy architectures (Traditional ETL) to modern Cloud Lakehouse ecosystems (ELT/ETLT). The core concept of the project, "Move the T", represents a strategic relocation of transformation logic.

Unlike traditional ETL, where transformation happens in a rigid intermediate server, the **Legacy2Lake** model executes logic directly on elastic, distributed processors (like Spark or Snowflake). This eliminates data movement latency and allows for independent scaling of analytical capacity, drastically reducing operational costs.

## **2. Mission Definitions**

To ensure development success, the system must meet the following design pillars:

* **Source & Format Agnosticism:** The tool must process heterogeneous repositories, from complex SSIS XML files (.dtsx) and Informatica exports to procedural SQL scripts or legacy Python code.
* **High-Fidelity Transpilation (Semantic Mapping):** We do not seek literal "line-by-line" translation. Legacy2Lake adapts paradigms: for example, converting a manual loop iterating over rows into a vectorized PySpark operation.
* **Native Lineage & Observability:** Column-level lineage is generated in real-time during translation. Every target column has a digital "birth certificate" explaining what transformations it underwent and its source of origin.
* **Refinement Loop (Modernization Loop):** An audit layer where advanced reasoning models evaluate the first code draft to detect inefficiencies, security risks, or lack of standards before final output.

## **3. Technical Architecture**

### **3.1. Software Stack**

* **Backend:** Python 3.11+ using **FastAPI** for asynchronous migration handling.
* **Agentic Orchestration:** Specialized agents managed via the Metadata Store.
* **SQL Parsing:** `sqlglot` for decomposing complex queries into ASTs.
* **Persistence:** **Supabase (PostgreSQL + pgvector)** for mission control, storing project states and vector embeddings of common transformations.
* **Frontend:** Next.js with Tailwind CSS, using **React Flow** for orchestration mesh rendering.

### **3.2. Metadata Store Schema**

* `projects`: Stores global context, credentials, and LLM settings.
* `assets`: Individual record of every loaded file with content hashes for deduplication.
* `nodes_edges`: Persistence of the mesh graph for UI reconstruction.
* `transformations`: Mapping table for original code vs. translated version.
* `lineage_metadata`: Structured JSON following OpenLineage principles.

## **4. Multi-Agent Workforce (Responsibilities)**

- **Detective (Discovery)**: Performs deep scanning of the repo structure, identifying legacy tool versions and external dependencies.
- **Cartographer (Lineage & Mesh)**: Builds the execution graph and precedence constraints for parallel execution optimization.
- **Interpreter (Transpiler)**: The main execution engine. Applies target-specific design patterns (e.g., Delta Lake MERGE for SCD Type 2).
- **Critic (Refinement & Optimization)**: Acts as a senior architect, analyzing the project for anti-patterns, cost optimization (FinOps), and consistency.

## **5. Step-by-Step Workflow (Lifecycle)**

1. **Ingest & Identification**: Agent A classifies files (Core/Support/Ignore) and reports on the "Technology Footprint."
2. **Mesh Construction**: Agent B translates legacy control flow to a visual graph for user validation.
3. **Synthesis & Metadata Extraction**: Agent C generates code while metadata is documented in real-time.
4. **Refinement Loop**: Agent F presents a findings report and refactors code for efficiency and standardization.
5. **Deployment & Delivery**: Packaging a solution bundle (.zip) containing production-ready code, operation manuals, and governance certificates.

## **6. Fulfillment Guidelines**

- **Persistence**: Migration state must persist every 10 seconds to ensure recovery in large migrations.
- **Security**: Mandatory anonymization filter to mask IPs, server names, and credentials before LLM submission.
- **Rate Limiting**: Implementation of Exponential Backoff for API calls.

## **7. Technical Annex: Compliance Standards (v2.0)**

### **7.1 Stable Surrogate Keys**
Mandatory "Lookup + New" pattern for idempotency in dimension tables:
1. Target Read -> Join -> Preserve existing keys -> Incremental generation for new records.

### **7.2 Strict Type Safety**
Explicit casting (`.cast()`) is required before any write operation. No automatic Spark type inference is allowed.
# Phase 4: Governance & Compliance (Complete Guide)

## 📌 Introduction
The **Governance (Stage 4)** phase closes the modernization lifecycle in Legacy2Lake. It provides the technical evidence, data lineage, orchestration schedules (`DAGs`), and deployment bundles needed to ensure corporate compliance.

---

## 👨‍💻 For the User: Modernization Certification
The system generates the "Passport" for your new data solution.

### Key Capabilities (v3.0)
1.  **AI-Guided Architectural Audit**: 
    - Click **"Run AI Audit"** to have Agent D scan your code.
    - Receive a dynamic score (0-100) based on Idempotency, Medallion Compliance, and Security.
    - View actionable **"Refactor Suggestions"** directly in the UI.
2.  **Orchestration Panel**:
    - Preview auto-generated **Airflow DAGs** and **Databricks Job JSONs**.
    - Configure schedule intervals (e.g., `@daily`) and retries.
3.  **Deployment Handover**:
    - **Download Bundle**: Get a ZIP with `Refined/`, `Orchestration/`, and `Governance/` folders.
    - **Push to Repo**: Direct integration to commit changes to the connected Git repository.

---

## ⚙️ For the Technical Team: Governance Services

### 1. Audit Service (Agent D)
Scans the `Refined/` directory to calculate a Compliance Score.
- **Security**: Checks for PII masking using the *Column Mapping* metadata.
- **Performance**: Flags inefficient Spark joins or lack of caching.
- **Idempotency**: Verifies distinct write modes (`overwrite`/`merge`).

### 2. DagGeneratorService
Converts the dependency mesh (`READS_FROM`, `SEQUENTIAL`) into executable workflow definitions.
- **Supported Targets**: Apache Airflow (Python), Databricks Workflows (JSON), Generic YAML.

### 3. Solution Bundler
Generates a compressed ZIP package containing:
- `Refined/`: Optimized PySpark/SQL code.
- `Orchestration/`: Scheduled tasks.
- `Governance/`: Documentation and Lineage reports.

---

## 🚀 Final Delivery
Upon completion, users download the **Solution Bundle**, representing the final, audited, and certified version of the modernization.

---
*Legacy2Lake Documentation Framework v3.0 - Stage 4*

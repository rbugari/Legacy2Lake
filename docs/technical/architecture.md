# Technical Architecture: The Cloud-Native Compiler
Legacy2Lake (formerly UTM) is a multi-tenant, data logic transpilation platform designed to decouple business intent from its technical implementation. The platform extracts the "DNA" of ETL processes and stores it in an agnostic Intermediate Representation (IR), leveraged across a distributed cloud-native architecture.

## 1. The Four-Layer Cloud Architecture

To ensure enterprise scalability and tenant isolation, Legacy2Lake implements a totally decoupled architecture:

### A. Managed Ingestion Layer
- **Mission**: Read original artifacts (XML, SQL, etc.) and extract raw metadata.
- **Components**: Technology-specific **Input Cartridges**.
- **Cloud-Native**: All uploads are staged in **Cloudflare R2** via `StorageProvider`.

### B. Universal Kernel (IR & Logic Store)
- **Mission**: Normalize raw metadata into the **Universal Metadata Schema**.
- **Components**: Logic inference engine and **Canonical Function Registry**.
- **Persistence**: Metadata is stored in **Supabase** (PostgreSQL) with Row-Level Security (RLS) for multi-tenancy.

### C. Synthesis Layer (Back-End / Cartridges)
- **Mission**: Translate the JSON-IR into the target language.
- **Components**: **Output Cartridges** (Jinja2-based).
- **Optimization**: Uses `asyncio` for parallel code generation.

### D. Cloud Delivery & Packaging (COP)
- **Mission**: Bundle code, logs, and audit reports into a production-ready package.
- **Components**: `GovernanceService`, `PackagingService`.
- **Performance**: Direct-to-client streaming via **Signed URLs** and memory-buffered zipping.

## 2. Multi-Agent System (MAS v3.5)

The system operates via specialized AI agents interacting through the metadata store and the cloud storage:

| Agent | Name | Role | Responsibility |
| :--- | :--- | :--- | :--- |
| **S** | **The Scout** | Discovery | Initial repository scan. Identifies context gaps and mission-critical files in R2 storage. |
| **A** | **The Architect** | Forensics | Scans manifest, builds dependency graph, and **infers metadata** (PII, Volumes). Stores forensics in `UTM_Object.metadata`. |
| **C** | **The Interpreter** | Transpilation | Converts legacy logic into optimized modern code. Applies **Auto-Partitioning** and **PII Masking** based on Architect forensics. |
| **F** | **The Fixer** | Refinement | Operates on draft code in R2. Applies "Design Registry" patterns and checks for synthax errors. |
| **G** | **The Guardian** | Certification | Performs **compliance audit** (0-100 score), generates **Runbooks**, and handles memory-safe bundle packaging. |

## 3. System Data Flow (Cloud-Native)

1. **Artifact Ingestion**: User uploads `.dtsx` (or clones Git). Files are written to **Cloudflare R2** under a tenant-prefixed key.
2. **DNA Analysis**: `DiscoveryService` reads from R2 to identify components like "Lookup" and "Derived Column".
3. **Normalization**: The Kernel translates logic into a **JOIN** or **TRANSFORM** object in the IR.
4. **Persistence**: Logic is saved in Supabase. Project settings and variables are auto-injected.
5. **Parallel Synthesis**: `Agent C` and `Agent F` generate code in parallel, reading/writing to the R2 `Refinement` stages.
6. **Certified Packaging**: `Agent G` gathers code and logs from R2, generates an AI certification, and streams a ZIP bundle directly to the user.

## 4. Multi-Tenant Guardrails (v3.6)

- **Zero-Trust Access**: The backend now strictly enforces tenant-scoped access via the `SupabasePersistence` service. Ad-hoc connections are prohibited to prevent data leakage.
- **Header Enforcement**: Every request must include `X-Tenant-ID`, which is sanitized and validated by the `get_identity` middleware.
- **Process Robustness**: Long-running orchestrators (Triage, Drafting, Refinement) check the `cancellation_requested` flag at granular steps, ensuring projects can be stopped immediately and safely.
- **Storage Isolation**: R2 keys follow the pattern `{tenant_id}/{project_name}/...` with signed URLs used for secure, performant delivery.

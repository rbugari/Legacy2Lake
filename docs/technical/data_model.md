# Metadata Store: Data Model Specification (v3.2)

The **Metadata Store** is the central repository where the "intelligence" of Legacy2Lake resides. Its design allows Ingestion agents (Parsers) to deposit raw logic, the Kernel to normalize it into an Intermediate Representation (IR), and the final user to intervene before Output Cartridges generate code.

## v3.2 Updates

**New Fields:**
- **`UTM_Object.metadata`** (JSONB): Architect v2.0 inferred metadata (Volume, PII, Partition Keys)
- **`UTM_Project.settings.variables`**: Variable injection framework (Phase 8)
- **Column Mappings**: Extended with `logic` field for custom transformation expressions

**New Tables/Entities:**
- **Governance Reports**: `audit_json` structure (score, checks, recommendations)
- **Quality Contracts**: Generated GX/Soda suites (stored in export bundles, not DB)

---

## 1. Entity-Relationship Diagram (Logical Structure)

### 1.1 Table: `UTM_Project`
Stores the global context of the modernization project.
- `project_id (UUID, PK)`: Unique identifier.
- `name (VARCHAR)`: Project name (e.g., "Legacy Sales Migration").
- `created_at (TIMESTAMP)`: Start date.
- `settings (JSONB)`: Global configuration including:
  - `migration_limit`: Batch processing limit
  - `variables`: **[Phase 8]** Key-value pairs for environment parameterization (e.g., `{S3_ROOT: "s3://bucket"}`)
  - Design registry patterns (naming conventions, target paths)

### 1.2 Table: `UTM_Object`
Represents an individual artifact from the source system.
- `object_id (UUID, PK)`: Unique ID.
- `project_id (UUID, FK)`: Relation to the project.
- `source_name (VARCHAR)`: Filename (e.g., `Load_Sales.dtsx`).
- `source_tech (ENUM)`: SSIS, Informatica, SQL_Proc, etc.
- `raw_content (TEXT)`: Original content for traceability.
- `metadata (JSONB)`: **[Phase 5 - Architect v2.0]** Inferred operational metadata:
  - `volume`: LOW | MED | HIGH (estimated data volume)
  - `is_pii`: Boolean flag if PII detected
  - `pii_columns`: Array of column names containing PII
  - `partition_key`: Suggested partitioning column (e.g., `transaction_date`)
  - `latency`: DAILY | HOURLY | REAL_TIME (execution frequency)
  - `criticality`: Business criticality score

### 1.3 Table: `UTM_Logical_Step` (The IR Core)
Stores each ETL step transformed into the Universal Grammar.
- `step_id (UUID, PK)`: Unique step ID.
- `object_id (UUID, FK)`: Parent object.
- `step_order (INT)`: Logical execution order.
- `step_type (ENUM)`: READ, TRANSFORM, JOIN, FILTER, AGGREGATE, WRITE.
- `ir_payload (JSONB)`: The Universal Grammar JSON object.
- `status (ENUM)`: DRAFT, VALIDATED, OVERRIDDEN, ERROR.

### 1.4 Table: `UTM_Column_Mapping` (Extended in v3.2)
Stores column-level transformations and metadata.
- `mapping_id (UUID, PK)`: Unique ID.
- `object_id (UUID, FK)`: Parent asset.
- `source_column (VARCHAR)`: Source column name.
- `target_column (VARCHAR)`: Target column name.
- `source_datatype (VARCHAR)`: Original data type.
- `target_datatype (VARCHAR)`: Modernized data type.
- `is_nullable (BOOLEAN)`: Nullability constraint.
- `is_pii (BOOLEAN)`: PII flag for masking.
- `logic (TEXT)`: **[Phase 6]** Custom transformation SQL expression (e.g., `CASE WHEN age < 18 THEN 'Minor'`).
- `masking_rule (VARCHAR)`: PII masking strategy (e.g., `SHA2`, `REDACT`).

### 1.5 Table: `UTM_User_Override`
Stores manual adjustments made by the data architect over the automatic IR.
- `override_id (UUID, PK)`: Unique ID.
- `step_id (UUID, FK)`: Target step.
- `field_path (VARCHAR)`: JSON path (e.g., `params.on_missing.action`).
- `old_value (TEXT)`: Original value proposed by the Kernel.
- `new_value (TEXT)`: Value adjusted by the user.

### 1.6 Table: `UTM_Function_Registry`
The translation dictionary for functions between languages.
- `func_id (UUID, PK)`: Unique ID.
- `canonical_name (VARCHAR)`: Name in the IR (e.g., `DATE_DIFF`).
- `tech_context (VARCHAR)`: `Databricks_13.3`, `Snowflake`, `SQLServer`, etc.
- `implementation_template (TEXT)`: Jinja2 template (e.g., `datediff({{end}}, {{start}})`).

### 1.7 Governance Artifacts (Virtual/Export)
Not stored in DB, but generated on-demand in v3.2:
- **Certification Report**: JSON structure with `score`, `checks[]`, `recommendations[]`
- **Runbook**: Markdown document (`Modernization_Runbook.md`)
- **Variable Manifest**: JSON file (`variables_manifest.json`)
- **Quality Contracts**: GX/Soda suites in `quality_contracts/` folder

---

## 2. Persistence & Consumption Logic

1. **Ingestion**: The **Parser Agent** populates `UTM_Object`.
2. **Forensics (Phase 5)**: **Architect v2.0** analyzes schema and populates `UTM_Object.metadata`.
3. **Normalization**: The **Kernel Agent** reads `UTM_Object`, processes logic, and generates multiple records in `UTM_Logical_Step`.
4. **Column Mapping (Phase 6)**: User defines transformations in `UTM_Column_Mapping`, including custom `logic` expressions.
5. **Change Management**: When a user edits a step in the UI, the system inserts a record into `UTM_User_Override` instead of overwriting the `ir_payload`.
6. **Code Generation (Phase 6)**: The **Output Cartridge** queries `UTM_Logical_Step`, applies any existing `UTM_User_Override`, and processes the Jinja2 template. Uses `metadata` for optimizations (partitioning, PII masking) and `variables` for parameterization.
7. **Governance (Phase 7)**: **Agent G** audits final code, generates certification report and runbook.
8. **Quality Contracts (Phase 9)**: **QualityService** reads `UTM_Column_Mapping` rules and generates validation suites.

---

## 3. Technical Considerations

- **Referential Integrity**: Maintaining Foreign Keys is vital for automatic column-level lineage.
- **Auditability**: `UTM_User_Override` is the most important table for Compliance, explaining why final code differs from legacy logic.
- **Scalability**: Using `JSONB` for payloads allows adding new operational types without altering physical table structures.
- **Metadata Evolution**: The `metadata` JSONB field in `UTM_Object` is version-safe—Architect v2.0 fields coexist with future enhancements.
- **Variable Injection**: Variables in `UTM_Project.settings.variables` are injected at code generation time, enabling environment-agnostic artifacts.

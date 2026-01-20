# Metadata Store: Data Model Specification

The **Metadata Store** is the central repository where the "intelligence" of Legacy2Lake resides. Its design allows Ingestion agents (Parsers) to deposit raw logic, the Kernel to normalize it into an Intermediate Representation (IR), and the final user to intervene before Output Cartridges generate code.

## 1. Entity-Relationship Diagram (Logical Structure)

### 1.1 Table: `UTM_Project`
Stores the global context of the modernization project.
- `project_id (UUID, PK)`: Unique identifier.
- `name (VARCHAR)`: Project name (e.g., "Legacy Sales Migration").
- `created_at (TIMESTAMP)`: Start date.
- `settings (JSONB)`: Global configuration (e.g., default Medallion layer names).

### 1.2 Table: `UTM_Object`
Represents an individual artifact from the source system.
- `object_id (UUID, PK)`: Unique ID.
- `project_id (UUID, FK)`: Relation to the project.
- `source_name (VARCHAR)`: Filename (e.g., `Load_Sales.dtsx`).
- `source_tech (ENUM)`: SSIS, Informatica, SQL_Proc, etc.
- `raw_content (TEXT)`: Original content for traceability.

### 1.3 Table: `UTM_Logical_Step` (The IR Core)
Stores each ETL step transformed into the Universal Grammar.
- `step_id (UUID, PK)`: Unique step ID.
- `object_id (UUID, FK)`: Parent object.
- `step_order (INT)`: Logical execution order.
- `step_type (ENUM)`: READ, TRANSFORM, JOIN, FILTER, AGGREGATE, WRITE.
- `ir_payload (JSONB)`: The Universal Grammar JSON object.
- `status (ENUM)`: DRAFT, VALIDATED, OVERRIDDEN, ERROR.

### 1.4 Table: `UTM_User_Override`
Stores manual adjustments made by the data architect over the automatic IR.
- `override_id (UUID, PK)`: Unique ID.
- `step_id (UUID, FK)`: Target step.
- `field_path (VARCHAR)`: JSON path (e.g., `params.on_missing.action`).
- `old_value (TEXT)`: Original value proposed by the Kernel.
- `new_value (TEXT)`: Value adjusted by the user.

### 1.5 Table: `UTM_Function_Registry`
The translation dictionary for functions between languages.
- `func_id (UUID, PK)`: Unique ID.
- `canonical_name (VARCHAR)`: Name in the IR (e.g., `DATE_DIFF`).
- `tech_context (VARCHAR)`: `Databricks_13.3`, `Snowflake`, `SQLServer`, etc.
- `implementation_template (TEXT)`: Jinja2 template (e.g., `datediff({{end}}, {{start}})`).

---

## 2. Persistence & Consumption Logic

1. **Ingestion**: The **Parser Agent** populates `UTM_Object`.
2. **Normalization**: The **Kernel Agent** reads `UTM_Object`, processes logic, and generates multiple records in `UTM_Logical_Step`.
3. **Change Management**: When a user edits a step in the UI, the system inserts a record into `UTM_User_Override` instead of overwriting the `ir_payload`.
4. **Code Generation**: The **Output Cartridge** queries `UTM_Logical_Step`, applies any existing `UTM_User_Override`, and processes the Jinja2 template.

## 3. Technical Considerations

- **Referential Integrity**: Maintaining Foreign Keys is vital for automatic column-level lineage.
- **Auditability**: `UTM_User_Override` is the most important table for Compliance, explaining why final code differs from legacy logic.
- **Scalability**: Using `JSONB` for payloads allows adding new operational types without altering physical table structures.

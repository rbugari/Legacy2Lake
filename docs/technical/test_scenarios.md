# Test Scenarios & End-to-End Validation

This document outlines the end-to-end validation flow for Legacy2Lake using the "Sales Base" solution. The goal is to confirm that agents can process `.dtsx` files and `.sql` scripts to generate a functional Lakehouse architecture.

## 1. Test Ingress (Base Files)
- **Source DDL**: `origen.sql` (Relational tables: Products, Customers, Sales).
- **Target DDL**: `destino_DW.sql` (Star Schema: DimProduct, FactSales).
- **ETL Logic**:
    - `DimProduct.dtsx`: To validate Slowly Changing Dimension (SCD) logic.
    - `FactSales.dtsx`: To validate complex Lookups, Staging, and Orchestration.

## 2. Validation Phases

### 2.1 Ingestion & Parsing
- **Test A: SQL Metadata**: Verify the SQL Parser correctly identifies source tables and data types from `.sql` scripts.
- **Test B: DTSX Logic**: Verify the SSIS Parser detects Data Flow components (Source, Derived Column, Join, Destination).

### 2.2 Kernel Normalization
Verify that the Kernel converts legacy components into the **Universal IR** describing *intent* rather than tool-specific syntax.

**Expected SCD Representation (IR):**
```json
{
  "step_id": "SCD_PRODUCT_001",
  "type": "TRANSFORM",
  "subtype": "SCD_TYPE_2",
  "params": {
    "business_key": ["productid"],
    "changing_attributes": ["unitprice"]
  }
}
```

### 2.3 Output Synthesis
Verify that the Output Cartridge reads the IR and generates target-native code (e.g., Delta Lake MERGE for SCD Type 2).

## 3. Success Criteria (Acceptance)
- **Integrity**: Generated code handles missing values (e.g., assigning -1 to keys) as defined in the IR.
- **Idempotency**: Running generated code twice does not duplicate data.
- **Agnosticism**: Switching cartridges (e.g., Databricks to Snowflake) changes the syntax without altering the logical IR.

---

## 4. Implementation Roadmap
- **Week 1**: Process basic `.dtsx` (e.g., `DimCategory`).
- **Week 2**: Map `DimProduct` to the Kernel and validate SCD metadata.
- **Week 3**: Generate the first Databricks Notebook and perform manual comparison.
- **Week 4**: Process `FactSales` to validate complex join orchestration.

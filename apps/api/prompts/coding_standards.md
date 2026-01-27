# Platform Standard: High-Quality Code (Target: PySpark)

## Environment
- **Target Platform**: Databricks (Lakehouse Architecture)
- **Spark Version**: Databricks Runtime 13.3+ LTS
- **Language**: PySpark / Spark SQL

## Key Architectural Rules (MANDATORY)
0. **Audit Trail Headers (CRITICAL)**:
   - EVERY generated file MUST start with the standard L2L Trace block:
   ```python
   # L2L MODERNIZATION TRACE
   # Source: {source_system} Asset '{asset_name}'
   # Component: {component_type}
   # Logic: Transpiled from {legacy_type}
   # Refactoring: {refactoring_note}
   # Generated At: {timestamp}
   ```
1. **Idempotency via MERGE**:
   - All Delta Lake writes MUST use the `MERGE INTO` statement for target tables.
   - Using `.mode("overwrite")` or `.mode("append")` is forbidden unless explicitly justified for Bronze/Raw layers.
2. **Data Integrity (Unknown Handling)**:
   - All Lookups/Joins against dimension tables must handle misses.
   - Use `COALESCE(col, -1)` (or appropriate surrogate key) to avoid NULLs in Fact tables.
3. **High-Fidelity Casting (STRICT)**:
   - Every column cast must explicitly match the Destination DDL.
   - **MANDATORY**: You must iterate through the Target Schema and apply `.withColumn(col, col.cast(type))` for EVERY column before writing.
   - Use `Decimal(18,2)`, `Long`, `Boolean` precisely. Do not rely on Spark's auto-inference.
6. **Load Strategy Awareness**:
   - **INCREMENTAL**: Must implement watermark-based filtering using a `ModifiedDate` or `ID` column.
   - **SCD_2**: Must implement history tracking (Start/End dates, `is_current` flag).
   - **FULL**: Replace target completely (standard `mode("overwrite")` only for Bronze, use `STATIC_PARTITION` for others).
7. **Sovereignty (PII Masking)**:
   - If an asset is flagged for PII, you MUST apply the requested `masking_rule` (e.g., `F.sha2(col, 256)` or `F.lit('REDACTED')`) in the Silver layer.

## Code Structure (Medallion Standard)
```python
def execute_task(spark, context):
    """
    Principal Engineer Transpilation
    """
    # 1. PARAMETERS (from context)
    target_table = context['target']
    business_keys = context['business_keys'] # e.g. ["OrderID", "LineID"]
    
    # 2. EXTRACT (Silver/Bronze)
    # df_source = spark.table(...)
    
    # 3. TRANSFORM (Intention-based logic)
    # df_transformed = spark.sql(""" SELECT ... """)

    # 3.1 STABLE KEY GENERATION (Mandatory for Dimensions)
    # df_joined = df_transformed.join(target, "BusinessKey", "left")
    # df_final = df_joined.withColumn("SK", coalesce(target.SK, max_sk + row_number()))

    # 3.2 TYPE SAFETY LOOP (Mandatory)
    # for field in schema: df_final = df_final.withColumn(field.name, col(field.name).cast(field.type))
    
    # 4. LOAD (High-Quality Idempotent Merge)
    # Using DeltaTable.merge() or spark.sql("MERGE INTO ...")
    
    return True
```

## Optimizations
- **Z-Order/Liquid Clustering**: Include comments for post-load optimization hints.
- **Broadcast Hints**: Explicitly use `F.broadcast()` for small lookup tables.

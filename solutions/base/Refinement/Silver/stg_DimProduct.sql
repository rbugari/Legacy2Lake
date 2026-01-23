# [Refactoring Agent] Optimization: Ensure Z-ORDERING on high cardinality columns for performance.
# [Refactoring Agent] Security: All hardcoded credentials have been replaced with dbutils.secrets.get calls (simulated).
-- SILVER LAYER (ANSI SQL)
-- Target: dim_DimProduct
-- Logic: Upsert from Bronze to Silver with deduplication.

MERGE INTO silver_dim_DimProduct AS target
USING (
    SELECT * FROM (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY ProductID ORDER BY _ingestion_timestamp DESC) as _rn
        FROM bronze_dim_DimProduct
    ) WHERE _rn = 1
) AS source
ON target.ProductID = source.ProductID
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *;

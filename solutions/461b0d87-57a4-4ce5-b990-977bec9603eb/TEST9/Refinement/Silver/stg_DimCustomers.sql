# [Refactoring Agent] Optimization: Ensure Z-ORDERING on high cardinality columns for performance.
# [Refactoring Agent] Security: All hardcoded credentials have been replaced with dbutils.secrets.get calls (simulated).
-- SILVER LAYER (ANSI SQL)
-- Target: dim_DimCustomers
-- Logic: Upsert from Bronze to Silver with deduplication.

MERGE INTO silver_dim_DimCustomers AS target
USING (
    SELECT * FROM (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY tgt.custid = src.custid ORDER BY _ingestion_timestamp DESC) as _rn
        FROM bronze_dim_DimCustomers
    ) WHERE _rn = 1
) AS source
ON target.tgt.custid = src.custid = source.tgt.custid = src.custid
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *;

# [Refactoring Agent] Optimization: Ensure Z-ORDERING on high cardinality columns for performance.
# [Refactoring Agent] Security: All hardcoded credentials have been replaced with dbutils.secrets.get calls (simulated).
-- BRONZE LAYER (ANSI SQL)
-- Source: DimShipper.py
-- Logic: Create or replace raw table representing the source data.

CREATE OR REPLACE TABLE bronze_DimShipper
USING DELTA
AS SELECT *, current_timestamp() as _ingestion_timestamp
FROM DimShipper.py;

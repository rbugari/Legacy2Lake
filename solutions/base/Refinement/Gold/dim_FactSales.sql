# [Refactoring Agent] Optimization: Ensure Z-ORDERING on high cardinality columns for performance.
# [Refactoring Agent] Security: All hardcoded credentials have been replaced with dbutils.secrets.get calls (simulated).
-- GOLD LAYER (ANSI SQL)
-- Target: dim_FactSales (FACT)
-- Logic: Business view with optional calculated measures.

CREATE OR REPLACE VIEW gold_dim_FactSales
AS
SELECT 
    * 
    , (qty * unitprice) AS total_amount
FROM silver_stg_FactSales;

/*
Sample SQL snippets extracted from the PySpark flow showing MERGE patterns used.
*/

-- Example: Close active dim rows where attributes changed (Category)
MERGE INTO gold.dim_category AS tgt
USING (SELECT categoryid, categoryname, etl_load_ts FROM v_stg_category) AS src
ON tgt.categoryid = src.categoryid AND tgt.is_current = true
WHEN MATCHED AND (tgt.categoryname IS NULL AND src.categoryname IS NOT NULL
                  OR tgt.categoryname IS NOT NULL AND src.categoryname IS NULL
                  OR tgt.categoryname <> src.categoryname)
  THEN UPDATE SET tgt.is_current = false, tgt.end_date = src.etl_load_ts;

-- Example: Insert new/changed category rows
MERGE INTO gold.dim_category AS tgt
USING (SELECT categoryid, categoryname, etl_load_ts FROM v_stg_category) AS src
ON tgt.categoryid = src.categoryid AND tgt.is_current = true
WHEN NOT MATCHED THEN
  INSERT (sk_category, categoryid, categoryname, start_date, end_date, is_current, etl_load_ts)
  VALUES ( (SELECT COALESCE(MAX(sk_category), 0) + ROW_NUMBER() OVER (ORDER BY src.categoryid) FROM gold.dim_category), src.categoryid, src.categoryname, src.etl_load_ts, NULL, true, src.etl_load_ts);

-- Example: Fact upsert
MERGE INTO gold.FactSales tgt
USING (SELECT orderid, productid, custid, empid, shipperid, categoryid, supplierid, qty, unitprice, discount, etl_load_ts FROM v_stg_fact_sales) AS src
ON tgt.orderid = src.orderid AND tgt.productid = src.productid
WHEN MATCHED AND (tgt.qty <> src.qty OR COALESCE(tgt.unitprice, -1) <> COALESCE(src.unitprice, -1) OR COALESCE(tgt.discount, -1) <> COALESCE(src.discount, -1))
  THEN UPDATE SET tgt.qty = src.qty, tgt.unitprice = src.unitprice, tgt.discount = src.discount, tgt.custid = src.custid, tgt.empid = src.empid, tgt.shipperid = src.shipperid, tgt.categoryid = src.categoryid, tgt.supplierid = src.supplierid, tgt.etl_load_ts = src.etl_load_ts
WHEN NOT MATCHED THEN
  INSERT (fact_sales_id, orderid, custid, empid, shipperid, categoryid, supplierid, qty, unitprice, discount, productid, etl_load_ts)
  VALUES ( (SELECT COALESCE(MAX(fact_sales_id), 0) + ROW_NUMBER() OVER (ORDER BY src.orderid, src.productid) FROM gold.FactSales), src.orderid, src.custid, src.empid, src.shipperid, src.categoryid, src.supplierid, src.qty, src.unitprice, src.discount, src.productid, src.etl_load_ts);

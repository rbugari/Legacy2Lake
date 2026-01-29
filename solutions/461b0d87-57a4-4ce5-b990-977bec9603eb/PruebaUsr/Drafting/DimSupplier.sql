/*
Generic MERGE templates used by the PySpark code above. These are provided as reference.
- Dimension MERGE (SCD2) template
MERGE INTO gold.dim_<DimName> as tgt
USING (SELECT * FROM stg_<DimName>) as src
ON tgt.<business_key> = src.<business_key> AND tgt.is_current = true
WHEN MATCHED AND src.attr_hash <> tgt.attr_hash
  THEN UPDATE SET tgt.end_date = current_timestamp(), tgt.is_current = false
WHEN NOT MATCHED
  THEN INSERT (<col list>) VALUES (<src.col list>)
WHEN NOT MATCHED BY SOURCE AND tgt.is_current = true
  THEN UPDATE SET tgt.end_date = current_timestamp(), tgt.is_current = false;

- Fact MERGE template
MERGE INTO gold.fact_sales as tgt
USING (SELECT * FROM stg_factsales) as src
ON tgt.orderid = src.orderid
WHEN MATCHED
  THEN UPDATE SET tgt.<cols> = src.<cols>
WHEN NOT MATCHED
  THEN INSERT (<col list>) VALUES (<src.col list>);
*/
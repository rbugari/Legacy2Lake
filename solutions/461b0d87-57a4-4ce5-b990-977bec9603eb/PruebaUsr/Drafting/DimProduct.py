# L2L MODERNIZATION TRACE
# Source: MSSQL Asset 'Northwind (extracted packages)'
# Component: Gold Dimensions & Fact (Transpiled Batch)
# Logic: Transpiled from SSIS packages (Dim*/FactSales)
# Refactoring: Consolidated Dim & Fact SCD2 + Full Refresh semantics using Delta MERGE
# Generated At: 2026-01-28T00:00:00Z

"""
Principal Engineer Transpilation for Dimensions (SCD2) and Fact (Full-refresh via MERGE)
This script implements high-fidelity casting, SCD2 for dimensions, COALESCE unknown handling
for facts, and idempotent MERGE semantics for Delta Lake (Databricks).
"""

from pyspark.sql import functions as F
from pyspark.sql import types as T
from delta.tables import DeltaTable
import logging
import traceback
import datetime

logger = logging.getLogger("l2l_transpiler")
logger.setLevel(logging.INFO)


def execute_task(spark, context: dict):
    """
    Principal Engineer Transpilation

    Args:
        spark: SparkSession (Databricks runtime assumed)
        context: dict with optional overrides (variables, schema prefixes)

    Returns:
        True on success, raises Exception on failure
    """
    try:
        # 1. PARAMETERS & CONFIG
        variables = context.get("variables", {})
        # Layer prefixes from global styling rules
        SILVER_PREFIX = context.get("silver_prefix", "stg_")
        GOLD_PREFIX = context.get("gold_prefix", "dim_")
        GOLD_FACT_PREFIX = context.get("gold_fact_prefix", "fact_")
        # Catalog/schema for targets
        TARGET_SCHEMA = context.get("target_schema", "gold")

        # Timestamp for batch
        batch_start_ts = datetime.datetime.utcnow().isoformat()

        # Source table mappings (assumes source data is already available in the metastore)
        src = {
            "categories": "Production.Categories",
            "customers": "Sales.Customers",
            "employees": "HR.Employees",
            "products": "Production.Products",
            "shippers": "Sales.Shippers",
            "suppliers": "Production.Suppliers",
            "orders": "Sales.Orders",
            "orderdetails": "Sales.OrderDetails"
        }

        # Default surrogate for unknown lookup results
        UNKNOWN_SURROGATE = -1

        # 2. EXTRACTION (Bronze / Raw assumed populated)
        # We load the source sets as DataFrames and normalize names for transformation
        df_categories = spark.table(src["categories"])
        df_customers = spark.table(src["customers"])
        df_employees = spark.table(src["employees"])  # will compute fullname
        df_products = spark.table(src["products"])    # full product record
        df_shippers = spark.table(src["shippers"])    # shipper
        df_suppliers = spark.table(src["suppliers"])  # supplier

        df_orders = spark.table(src["orders"])
        df_orderdetails = spark.table(src["orderdetails"])

        # 3. TRANSFORM (Intention-based logic)
        # For each dimension: create a standardized staging view with SCD2 metadata columns

        # Utility function for creating standardized SCD2 staging DataFrame
        def create_scd2_staging(df, business_key_col, attribute_cols, rename_map=None):
            """
            Create staging DF for SCD2 with start_date, end_date, is_current

            Args:
                df: source DataFrame
                business_key_col: str: column name in source representing business key
                attribute_cols: list[str]: columns to carry as attributes
                rename_map: dict(optional): mapping from source col to desired column names

            Returns:
                staging_df: DataFrame
            """
            # Apply renames first
            if rename_map:
                for src_col, tgt_col in rename_map.items():
                    if src_col in df.columns:
                        df = df.withColumnRenamed(src_col, tgt_col)
            # Build selection
            select_expr = [F.col(business_key_col).alias("business_key")] 
            for c in attribute_cols:
                if c in df.columns:
                    select_expr.append(F.col(c))
                else:
                    select_expr.append(F.lit(None).alias(c))

            now_ts = F.current_timestamp()
            staging = df.select(*select_expr) \
                .withColumn("start_date", now_ts) \
                .withColumn("end_date", F.to_timestamp(F.lit("9999-12-31 23:59:59"))) \
                .withColumn("is_current", F.lit(True))
            return staging

        # DimCategory
        dim_category_attrs = ["categoryname"]
        stg_categories = create_scd2_staging(df_categories, "categoryid", dim_category_attrs, {"categoryname": "categoryname"}) \
            .withColumnRenamed("categoryid", "category_id")

        # DimCustomer
        customer_attrs = ["contactname", "city", "country", "address", "phone", "postalcode"]
        stg_customers = create_scd2_staging(df_customers, "custid", customer_attrs) \
            .withColumnRenamed("custid", "customer_id")

        # DimEmployee (fullname)
        df_employees = df_employees.withColumn("fullname", F.concat_ws(" ", F.col("firstname"), F.col("lastname")))
        employee_attrs = ["fullname", "title", "city", "country", "address", "phone"]
        stg_employees = create_scd2_staging(df_employees, "empid", employee_attrs) \
            .withColumnRenamed("empid", "employee_id")

        # DimProduct (take all cols but normalize minimal set)
        product_attrs = [c for c in df_products.columns if c.lower() not in ("productid",)]
        stg_products = create_scd2_staging(df_products, "productid", product_attrs) \
            .withColumnRenamed("productid", "product_id")

        # DimShipper
        shipper_attrs = [c for c in df_shippers.columns if c.lower() not in ("shipperid",)]
        stg_shippers = create_scd2_staging(df_shippers, "shipperid", shipper_attrs) \
            .withColumnRenamed("shipperid", "shipper_id")

        # DimSupplier
        supplier_attrs = ["companyname", "address", "postalcode", "phone", "city", "country"]
        stg_suppliers = create_scd2_staging(df_suppliers, "supplierid", supplier_attrs) \
            .withColumnRenamed("supplierid", "supplier_id")

        # 3.1 STABLE KEY GENERATION (SCD2 SK assignment handled by DB auto-increment or surrogate generation)
        # We will rely on the target dim table having a surrogate primary key (sk) of type Long and
        # will not attempt to generate SK in the pipeline – the load will insert rows and the SK
        # will be created by the target table (assumption). If SK generation is required,
        # add logic to compute monotonic IDs based on max(SK)+row_number().

        # 3.2 TYPE SAFETY LOOP (Mandatory)
        # Define target schema expectations (high-fidelity). These are assumptions documented below.

        # Helper to cast DataFrame columns according to a provided schema mapping
        def enforce_casts(df, schema_map):
            """
            Cast every column in schema_map on df to the defined types.

            Args:
                df: DataFrame
                schema_map: dict {col_name: spark.sql.types.DataType}

            Returns:
                df_casted: DataFrame
            """
            for col_name, col_type in schema_map.items():
                if col_name in df.columns:
                    df = df.withColumn(col_name, F.col(col_name).cast(col_type))
                else:
                    # add missing column with null casted to target type
                    df = df.withColumn(col_name, F.lit(None).cast(col_type))
            return df

        # Assumed target schemas (High-fidelity). These should be replaced by actual DDL in production.
        # NOTE: All dims follow SCD2 columns: sk (Long), business_key (Long/String), attributes, start_date (Timestamp), end_date (Timestamp), is_current (Boolean)
        dim_common_schema = {
            "sk": T.LongType(),
            "business_key": T.LongType(),
            "start_date": T.TimestampType(),
            "end_date": T.TimestampType(),
            "is_current": T.BooleanType()
        }

        # Specific add-ons per dim (we keep String for textual fields)
        dim_category_schema = dict(dim_common_schema)
        dim_category_schema.update({"categoryname": T.StringType()})

        dim_customer_schema = dict(dim_common_schema)
        dim_customer_schema.update({
            "contactname": T.StringType(),
            "city": T.StringType(),
            "country": T.StringType(),
            "address": T.StringType(),
            "phone": T.StringType(),
            "postalcode": T.StringType(),
            "customer_id": T.LongType()
        })

        dim_employee_schema = dict(dim_common_schema)
        dim_employee_schema.update({
            "fullname": T.StringType(),
            "title": T.StringType(),
            "city": T.StringType(),
            "country": T.StringType(),
            "address": T.StringType(),
            "phone": T.StringType(),
            "employee_id": T.LongType()
        })

        dim_product_schema = dict(dim_common_schema)
        # Product: we keep a few core attributes; in real life map all DDL columns precisely
        dim_product_schema.update({
            "product_id": T.LongType(),
            "productname": T.StringType(),
            "supplierid": T.LongType(),
            "categoryid": T.LongType(),
            "quantityperunit": T.StringType(),
            "unitprice": T.DecimalType(18, 2),
            "unitsinstock": T.LongType(),
            "discontinued": T.BooleanType()
        })

        dim_shipper_schema = dict(dim_common_schema)
        dim_shipper_schema.update({"companyname": T.StringType(), "shipper_id": T.LongType()})

        dim_supplier_schema = dict(dim_common_schema)
        dim_supplier_schema.update({
            "companyname": T.StringType(),
            "address": T.StringType(),
            "postalcode": T.StringType(),
            "phone": T.StringType(),
            "city": T.StringType(),
            "country": T.StringType(),
            "supplier_id": T.LongType()
        })

        # Enforce casts on staging frames (align to target schema names)
        stg_categories = stg_categories.withColumnRenamed("business_key", "category_id")
        # For consistency across the pipeline rename business_key back to business_key
        stg_categories = stg_categories.withColumnRenamed("category_id", "business_key")
        stg_categories = enforce_casts(stg_categories, dim_category_schema)

        stg_customers = stg_customers.withColumnRenamed("customer_id", "business_key")
        stg_customers = enforce_casts(stg_customers, dim_customer_schema)

        stg_employees = stg_employees.withColumnRenamed("employee_id", "business_key")
        stg_employees = enforce_casts(stg_employees, dim_employee_schema)

        stg_products = stg_products.withColumnRenamed("product_id", "business_key")
        # Normalize some common product column names if present
        if "productname" not in stg_products.columns and "ProductName" in stg_products.columns:
            stg_products = stg_products.withColumnRenamed("ProductName", "productname")
        stg_products = enforce_casts(stg_products, dim_product_schema)

        stg_shippers = stg_shippers.withColumnRenamed("shipper_id", "business_key")
        stg_shippers = enforce_casts(stg_shippers, dim_shipper_schema)

        stg_suppliers = stg_suppliers.withColumnRenamed("supplier_id", "business_key")
        stg_suppliers = enforce_casts(stg_suppliers, dim_supplier_schema)

        # Register staging views for SQL MERGE usage
        stg_categories.createOrReplaceTempView("src_categories")
        stg_customers.createOrReplaceTempView("src_customers")
        stg_employees.createOrReplaceTempView("src_employees")
        stg_products.createOrReplaceTempView("src_products")
        stg_shippers.createOrReplaceTempView("src_shippers")
        stg_suppliers.createOrReplaceTempView("src_suppliers")

        # 4. LOAD (High-Quality Idempotent Merge)
        # Pattern used for SCD2 (two-step MERGE):
        # 1) MERGE to set old current rows to is_current = false when attributes changed
        # 2) MERGE to insert new rows (both new and changed)

        def build_attr_change_condition(target_alias, source_alias, attr_cols):
            conds = []
            for c in attr_cols:
                # Use COALESCE for null-safe comparison
                conds.append(f"COALESCE({target_alias}.{c}, '') <> COALESCE({source_alias}.{c}, '')")
            return " OR ".join(conds) if conds else "FALSE"

        # Generic SCD2 loader using SQL MERGE
        def scd2_merge(target_table_name, src_view_name, business_key_col_name, attr_columns, target_schema_map):
            target_fq = f"{TARGET_SCHEMA}.{target_table_name}"
            # 1) Step - expire changed current rows
            change_expr = build_attr_change_condition("tgt", "src", attr_columns)
            sql_expire = f"""
MERGE INTO {target_fq} tgt
USING (SELECT * FROM {src_view_name}) src
ON tgt.business_key = src.business_key AND tgt.is_current = true
WHEN MATCHED AND ({change_expr})
  THEN UPDATE SET tgt.is_current = false, tgt.end_date = src.start_date
"""
            logger.info(f"Executing expire MERGE for {target_fq}")
            spark.sql(sql_expire)

            # 2) Step - insert new and new-changed rows (rows not matched against current tgt)
            # Build insert column list from target_schema_map keys to preserve casting order
            insert_cols = list(target_schema_map.keys())
            # Map source columns to insert values: for SK we let DB assign (NULL), for business_key and attrs use src
            insert_values = []
            for c in insert_cols:
                if c == "sk":
                    insert_values.append("NULL")
                elif c in ("start_date", "end_date", "is_current"):
                    insert_values.append(f"src.{c}")
                elif c == "business_key":
                    insert_values.append(f"src.business_key")
                else:
                    insert_values.append(f"src.{c}")

            cols_sql = ",".join(insert_cols)
            vals_sql = ",".join(insert_values)

            sql_insert = f"""
MERGE INTO {target_fq} tgt
USING (SELECT * FROM {src_view_name}) src
ON tgt.business_key = src.business_key AND tgt.is_current = true
WHEN NOT MATCHED THEN
  INSERT ({cols_sql}) VALUES ({vals_sql})
"""
            logger.info(f"Executing insert MERGE for {target_fq}")
            spark.sql(sql_insert)

            # Post-merge: Ensure target types are correct (Delta will store by schema; cautionary step if needed)
            logger.info(f"SCD2 merge completed for {target_fq}")

        # Execute merges for each dimension
        # Target table names follow GOLD_PREFIX naming rules (Gold='dim_')
        scd2_merge(f"{GOLD_PREFIX}category", "src_categories", "business_key", ["categoryname"], dim_category_schema)
        scd2_merge(f"{GOLD_PREFIX}customer", "src_customers", "business_key", ["contactname", "city", "country", "address", "phone", "postalcode"], dim_customer_schema)
        scd2_merge(f"{GOLD_PREFIX}employee", "src_employees", "business_key", ["fullname", "title", "city", "country", "address", "phone"], dim_employee_schema)
        scd2_merge(f"{GOLD_PREFIX}product", "src_products", "business_key", ["productname", "supplierid", "categoryid", "unitprice"], dim_product_schema)
        scd2_merge(f"{GOLD_PREFIX}shipper", "src_shippers", "business_key", ["companyname"], dim_shipper_schema)
        scd2_merge(f"{GOLD_PREFIX}supplier", "src_suppliers", "business_key", ["companyname", "address", "city", "country"], dim_supplier_schema)

        # FACT: FactSales - Full refresh semantics implemented by MERGE with WHEN NOT MATCHED BY SOURCE THEN DELETE
        # Build a staging fact by joining orders, orderdetails and product -> then look up product SK in dim_product

        # Assemble fact staging
        df_order_master = df_orders.alias("o") \
            .join(df_orderdetails.alias("od"), F.col("o.orderid") == F.col("od.orderid"), "inner") \
            .join(df_products.alias("p"), F.col("od.productid") == F.col("p.productid"), "inner") \
            .select(
                F.col("o.orderid").alias("order_id"),
                F.col("o.custid").alias("custid"),
                F.col("o.empid").alias("empid"),
                F.col("o.shipperid").alias("shipperid"),
                F.col("p.categoryid").alias("categoryid"),
                F.col("p.supplierid").alias("supplierid"),
                F.col("od.qty").alias("quantity"),
                F.col("od.unitprice").alias("unit_price"),
                F.col("od.discount").alias("discount"),
                F.col("od.productid").alias("productid"),
                F.col("od.orderid").alias("order_line_id")
            )

        # Join with dimension product to get surrogate key. We assume dim_product table exists and has sk & business_key
        dim_product_table = f"{TARGET_SCHEMA}.{GOLD_PREFIX}product"
        df_dim_product = spark.table(dim_product_table).filter(F.col("is_current") == True).select(F.col("sk").alias("product_sk"), F.col("business_key").alias("productid"))

        # Broadcast small dim_product if it's small otherwise rely on optimizer. We'll add explicit broadcast hint to follow registry.
        df_fact_stg = df_order_master.join(F.broadcast(df_dim_product), on=["productid"], how="left") \
            .withColumn("product_sk", F.coalesce(F.col("product_sk"), F.lit(UNKNOWN_SURROGATE))) \
            .withColumn("start_date", F.current_timestamp())

        # Enforce casting for fact target. Assumed fact schema:
        fact_sales_schema = {
            "order_id": T.LongType(),
            "productid": T.LongType(),
            "product_sk": T.LongType(),
            "custid": T.LongType(),
            "empid": T.LongType(),
            "shipperid": T.LongType(),
            "categoryid": T.LongType(),
            "supplierid": T.LongType(),
            "quantity": T.LongType(),
            "unit_price": T.DecimalType(18, 2),
            "discount": T.DecimalType(18, 2),
            "order_line_id": T.LongType(),
            "start_date": T.TimestampType()
        }

        df_fact_stg = enforce_casts(df_fact_stg, fact_sales_schema)
        df_fact_stg.createOrReplaceTempView("src_fact_sales")

        # Perform MERGE for full-refresh: Upsert all rows and delete rows not present in source
        target_fact_table = f"{TARGET_SCHEMA}.{GOLD_FACT_PREFIX}sales"

        # Merge logic: match on composite key (order_id + order_line_id)
        sql_fact_merge = f"""
MERGE INTO {target_fact_table} tgt
USING (SELECT * FROM src_fact_sales) src
ON tgt.order_id = src.order_id AND tgt.order_line_id = src.order_line_id
WHEN MATCHED
  THEN UPDATE SET
    tgt.productid = src.productid,
    tgt.product_sk = src.product_sk,
    tgt.custid = src.custid,
    tgt.empid = src.empid,
    tgt.shipperid = src.shipperid,
    tgt.categoryid = src.categoryid,
    tgt.supplierid = src.supplierid,
    tgt.quantity = src.quantity,
    tgt.unit_price = src.unit_price,
    tgt.discount = src.discount,
    tgt.start_date = src.start_date
WHEN NOT MATCHED
  THEN INSERT (order_id, productid, product_sk, custid, empid, shipperid, categoryid, supplierid, quantity, unit_price, discount, order_line_id, start_date)
  VALUES (src.order_id, src.productid, src.product_sk, src.custid, src.empid, src.shipperid, src.categoryid, src.supplierid, src.quantity, src.unit_price, src.discount, src.order_line_id, src.start_date)
WHEN NOT MATCHED BY SOURCE
  THEN DELETE
"""
        logger.info(f"Executing MERGE for fact table {target_fact_table}")
        spark.sql(sql_fact_merge)

        # Post-load tuning hints (comments only) - consider running OPTIMIZE / ZORDER on heavy-read columns
        # Example: spark.sql(f"OPTIMIZE {TARGET_SCHEMA}.{GOLD_FACT_PREFIX}sales ZORDER BY (product_sk, order_id)")

        logger.info("Transpilation and load completed successfully")
        return True

    except Exception as e:
        logger.error("Error in transpiled job: %s", str(e))
        logger.error(traceback.format_exc())
        raise


# If run as a module inside Databricks notebook, user would call:
# execute_task(spark, {})

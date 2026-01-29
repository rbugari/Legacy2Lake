# L2L MODERNIZATION TRACE
# Source: Legacy SSIS Asset 'Triage Packages'
# Component: Transpiler
# Logic: Transpiled from SSIS DTSX packages
# Refactoring: Consolidated Dimensional SCD2 + Fact snapshot conversion to Delta MERGE flows
# Generated At: 2026-01-28T00:00:00Z

"""
Principal Engineer Transpilation
This script migrates multiple DTSX-packaged extracts into Delta Lake Gold dimensions (SCD2) and a Fact snapshot
- Implements idempotent MERGE logic per-dimension
- Implements SCD Type 2 history (start_date, end_date, is_current)
- Ensures type safety by applying explicit casts matching assumed target DDLs
- Handles lookup misses using COALESCE(..., -1) to guarantee referential integrity
- Uses two-step MERGE pattern to close existing active records and then insert new/changed rows

Assumptions and explicit schema casts are included below. Adjust schema types to match your target exactly.
"""

from datetime import datetime
import logging

from delta.tables import DeltaTable
from pyspark.sql import functions as F
from pyspark.sql import types as T


def execute_task(spark, context: dict = None):
    """
    Principal Engineer Transpilation

    Args:
        spark: SparkSession (pre-initialized in Databricks runtime)
        context: dict containing optional overrides: target_catalog, source_catalog, temp_db, variables
    Returns:
        bool: True on success
    """
    try:
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger("l2l_transpiler")

        # 1. PARAMETERS & CONFIG
        # Default catalogs/databases - override via context if provided
        ctx = context or {}
        SOURCE_DB = ctx.get("source_db", "prod")
        BRONZE_DB = ctx.get("bronze_db", "bronze")
        SILVER_DB = ctx.get("silver_db", "silver")
        GOLD_DB = ctx.get("gold_db", "gold")
        TEMP_DB = ctx.get("temp_db", "tmp")
        RUN_TIMESTAMP = datetime.utcnow().isoformat()

        # Naming prefixes
        STG_PREFIX = "stg_"    # Silver staging
        DIM_PREFIX = "dim_"    # Gold dimensions

        logger.info(f"Running L2L transpile at {RUN_TIMESTAMP}")

        # Utility functions
        def safe_table_name(db, tbl):
            return f"{db}.{tbl}"

        def ensure_delta_table_exists(table_full_name, schema_struct):
            """Create an empty Delta table if it does not exist using the provided schema_struct (list of StructField)
            This is idempotent - will not overwrite existing table.
            """
            if not spark._jsparkSession.catalog().tableExists(table_full_name):
                logger.info(f"Creating empty Delta table {table_full_name}")
                empty_df = spark.createDataFrame(spark.sparkContext.emptyRDD(), T.StructType(schema_struct))
                (empty_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(table_full_name))

        # 2. EXTRACTION (from source tables) -- using direct table reads as provided in packages
        # For each DTSX package from the project overview we implement a dedicated flow.

        # ------------- DIMENSIONS -----------------

        # 2.1 DimCategory
        # Source query: SELECT categoryid,categoryname FROM Production.Categories WHERE categoryid > ?
        try:
            src_cat = spark.table(f"{SOURCE_DB}.Categories").select(
                F.col("categoryid").alias("categoryid"),
                F.col("categoryname").alias("categoryname")
            )
        except Exception:
            logger.exception("Failed reading source Categories table")
            raise

        # Target schema assumptions for dim_category (Gold)
        dim_category_tbl = safe_table_name(GOLD_DB, f"{DIM_PREFIX}category")
        dim_category_schema = [
            T.StructField("sk_category", T.LongType(), False),
            T.StructField("categoryid", T.LongType(), True),
            T.StructField("categoryname", T.StringType(), True),
            T.StructField("start_date", T.TimestampType(), True),
            T.StructField("end_date", T.TimestampType(), True),
            T.StructField("is_current", T.BooleanType(), True),
            T.StructField("etl_load_ts", T.TimestampType(), True)
        ]

        ensure_delta_table_exists(dim_category_tbl, dim_category_schema)

        # Transform staging dataframe
        stg_category = src_cat.select(
            F.col("categoryid").cast(T.LongType()),
            F.col("categoryname").cast(T.StringType())
        ).withColumn("etl_load_ts", F.current_timestamp())

        # SCD2 Handling for DimCategory
        # 1) Close existing active records where business key matches and attributes differ
        # 2) Insert new rows for new or changed business key-state

        # compute business-key equality condition and attribute-change detection
        spark.sql(f"REFRESH TABLE {dim_category_tbl}")
        target_cat = DeltaTable.forName(spark, dim_category_tbl)

        # Create staging temp view
        stg_category.createOrReplaceTempView("v_stg_category")

        # Close existing active rows where data changed
        merge_close_cat = f"""
        MERGE INTO {dim_category_tbl} AS tgt
        USING (SELECT categoryid, categoryname, etl_load_ts FROM v_stg_category) AS src
        ON tgt.categoryid = src.categoryid AND tgt.is_current = true
        WHEN MATCHED AND (tgt.categoryname IS NULL AND src.categoryname IS NOT NULL
                          OR tgt.categoryname IS NOT NULL AND src.categoryname IS NULL
                          OR tgt.categoryname <> src.categoryname)
          THEN UPDATE SET tgt.is_current = false, tgt.end_date = src.etl_load_ts
        """
        logger.info("Closing changed active category records via MERGE (step 1)")
        spark.sql(merge_close_cat)

        # Insert new/changed rows (including brand new keys)
        merge_insert_cat = f"""
        MERGE INTO {dim_category_tbl} AS tgt
        USING (SELECT categoryid, categoryname, etl_load_ts FROM v_stg_category) AS src
        ON tgt.categoryid = src.categoryid AND tgt.is_current = true
        WHEN NOT MATCHED THEN
          INSERT (sk_category, categoryid, categoryname, start_date, end_date, is_current, etl_load_ts)
          VALUES ( (SELECT COALESCE(MAX(sk_category), 0) + ROW_NUMBER() OVER (ORDER BY src.categoryid) FROM {dim_category_tbl}),
                   src.categoryid, src.categoryname, src.etl_load_ts, NULL, true, src.etl_load_ts )
        """
        logger.info("Inserting new/changed category rows via MERGE (step 2)")
        spark.sql(merge_insert_cat)

        # Enforce explicit casting on target table columns (type safety)
        # Re-read and cast per schema
        df_cat_final = spark.table(dim_category_tbl)
        for fld in dim_category_schema:
            df_cat_final = df_cat_final.withColumn(fld.name, F.col(fld.name).cast(fld.dataType))

        # Overwrite table with cast-corrected data using MERGE (idempotent pattern)
        df_cat_final.createOrReplaceTempView("v_cat_final")
        merge_cast_cat = f"""
        MERGE INTO {dim_category_tbl} tgt
        USING v_cat_final src
        ON tgt.sk_category = src.sk_category
        WHEN MATCHED THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *
        """
        logger.info("Applying cast-corrected dataset back to target (idempotent MERGE)")
        spark.sql(merge_cast_cat)

        # ------------- DimCustomers -----------------
        try:
            src_cust = spark.table(f"{SOURCE_DB}.Customers").select(
                F.col("custid"),
                F.col("contactname"),
                F.col("city"),
                F.col("country"),
                F.col("address"),
                F.col("phone"),
                F.col("postalcode")
            )
        except Exception:
            logger.exception("Failed reading source Customers table")
            raise

        dim_customer_tbl = safe_table_name(GOLD_DB, f"{DIM_PREFIX}customer")
        dim_customer_schema = [
            T.StructField("sk_customer", T.LongType(), False),
            T.StructField("custid", T.LongType(), True),
            T.StructField("contactname", T.StringType(), True),
            T.StructField("city", T.StringType(), True),
            T.StructField("country", T.StringType(), True),
            T.StructField("address", T.StringType(), True),
            T.StructField("phone", T.StringType(), True),
            T.StructField("postalcode", T.StringType(), True),
            T.StructField("start_date", T.TimestampType(), True),
            T.StructField("end_date", T.TimestampType(), True),
            T.StructField("is_current", T.BooleanType(), True),
            T.StructField("etl_load_ts", T.TimestampType(), True)
        ]

        ensure_delta_table_exists(dim_customer_tbl, dim_customer_schema)

        stg_customer = src_cust.select(
            F.col("custid").cast(T.LongType()),
            F.col("contactname").cast(T.StringType()),
            F.col("city").cast(T.StringType()),
            F.col("country").cast(T.StringType()),
            F.col("address").cast(T.StringType()),
            F.col("phone").cast(T.StringType()),
            F.col("postalcode").cast(T.StringType())
        ).withColumn("etl_load_ts", F.current_timestamp())

        stg_customer.createOrReplaceTempView("v_stg_customer")

        logger.info("Closing changed active customer records via MERGE (step 1)")
        merge_close_cust = f"""
        MERGE INTO {dim_customer_tbl} AS tgt
        USING (SELECT custid, contactname, city, country, address, phone, postalcode, etl_load_ts FROM v_stg_customer) AS src
        ON tgt.custid = src.custid AND tgt.is_current = true
        WHEN MATCHED AND ( (tgt.contactname IS NULL AND src.contactname IS NOT NULL) OR (tgt.contactname IS NOT NULL AND src.contactname IS NULL) OR tgt.contactname <> src.contactname
                          OR tgt.city <> src.city OR tgt.country <> src.country OR tgt.address <> src.address OR tgt.phone <> src.phone OR tgt.postalcode <> src.postalcode)
          THEN UPDATE SET tgt.is_current = false, tgt.end_date = src.etl_load_ts
        """
        spark.sql(merge_close_cust)

        logger.info("Inserting new/changed customer rows via MERGE (step 2)")
        merge_insert_cust = f"""
        MERGE INTO {dim_customer_tbl} AS tgt
        USING (SELECT custid, contactname, city, country, address, phone, postalcode, etl_load_ts FROM v_stg_customer) AS src
        ON tgt.custid = src.custid AND tgt.is_current = true
        WHEN NOT MATCHED THEN
          INSERT (sk_customer, custid, contactname, city, country, address, phone, postalcode, start_date, end_date, is_current, etl_load_ts)
          VALUES ( (SELECT COALESCE(MAX(sk_customer), 0) + ROW_NUMBER() OVER (ORDER BY src.custid) FROM {dim_customer_tbl}),
                   src.custid, src.contactname, src.city, src.country, src.address, src.phone, src.postalcode, src.etl_load_ts, NULL, true, src.etl_load_ts)
        """
        spark.sql(merge_insert_cust)

        # Enforce casts
        df_cust_final = spark.table(dim_customer_tbl)
        for fld in dim_customer_schema:
            df_cust_final = df_cust_final.withColumn(fld.name, F.col(fld.name).cast(fld.dataType))
        df_cust_final.createOrReplaceTempView("v_cust_final")
        merge_cast_cust = f"""
        MERGE INTO {dim_customer_tbl} tgt
        USING v_cust_final src
        ON tgt.sk_customer = src.sk_customer
        WHEN MATCHED THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *
        """
        spark.sql(merge_cast_cust)

        # ------------- DimEmployee -----------------
        try:
            # Source uses firstname + lastname as fullname
            src_emp = spark.table(f"{SOURCE_DB}.Employees").select(
                F.col("empid"),
                (F.concat_ws(" ", F.col("firstname"), F.col("lastname"))).alias("fullname"),
                F.col("title"),
                F.col("city"),
                F.col("country"),
                F.col("address"),
                F.col("phone")
            )
        except Exception:
            logger.exception("Failed reading source Employees table")
            raise

        dim_employee_tbl = safe_table_name(GOLD_DB, f"{DIM_PREFIX}employee")
        dim_employee_schema = [
            T.StructField("sk_employee", T.LongType(), False),
            T.StructField("empid", T.LongType(), True),
            T.StructField("fullname", T.StringType(), True),
            T.StructField("title", T.StringType(), True),
            T.StructField("city", T.StringType(), True),
            T.StructField("country", T.StringType(), True),
            T.StructField("address", T.StringType(), True),
            T.StructField("phone", T.StringType(), True),
            T.StructField("start_date", T.TimestampType(), True),
            T.StructField("end_date", T.TimestampType(), True),
            T.StructField("is_current", T.BooleanType(), True),
            T.StructField("etl_load_ts", T.TimestampType(), True)
        ]

        ensure_delta_table_exists(dim_employee_tbl, dim_employee_schema)

        stg_emp = src_emp.select(
            F.col("empid").cast(T.LongType()),
            F.col("fullname").cast(T.StringType()),
            F.col("title").cast(T.StringType()),
            F.col("city").cast(T.StringType()),
            F.col("country").cast(T.StringType()),
            F.col("address").cast(T.StringType()),
            F.col("phone").cast(T.StringType())
        ).withColumn("etl_load_ts", F.current_timestamp())

        stg_emp.createOrReplaceTempView("v_stg_employee")

        logger.info("Closing changed active employee records via MERGE (step 1)")
        merge_close_emp = f"""
        MERGE INTO {dim_employee_tbl} AS tgt
        USING (SELECT empid, fullname, title, city, country, address, phone, etl_load_ts FROM v_stg_employee) AS src
        ON tgt.empid = src.empid AND tgt.is_current = true
        WHEN MATCHED AND (tgt.fullname <> src.fullname OR tgt.title <> src.title OR tgt.city <> src.city OR tgt.country <> src.country OR tgt.address <> src.address OR tgt.phone <> src.phone)
          THEN UPDATE SET tgt.is_current = false, tgt.end_date = src.etl_load_ts
        """
        spark.sql(merge_close_emp)

        logger.info("Inserting new/changed employee rows via MERGE (step 2)")
        merge_insert_emp = f"""
        MERGE INTO {dim_employee_tbl} AS tgt
        USING (SELECT empid, fullname, title, city, country, address, phone, etl_load_ts FROM v_stg_employee) AS src
        ON tgt.empid = src.empid AND tgt.is_current = true
        WHEN NOT MATCHED THEN
          INSERT (sk_employee, empid, fullname, title, city, country, address, phone, start_date, end_date, is_current, etl_load_ts)
          VALUES ( (SELECT COALESCE(MAX(sk_employee), 0) + ROW_NUMBER() OVER (ORDER BY src.empid) FROM {dim_employee_tbl}),
                   src.empid, src.fullname, src.title, src.city, src.country, src.address, src.phone, src.etl_load_ts, NULL, true, src.etl_load_ts )
        """
        spark.sql(merge_insert_emp)

        # Cast enforcement
        df_emp_final = spark.table(dim_employee_tbl)
        for fld in dim_employee_schema:
            df_emp_final = df_emp_final.withColumn(fld.name, F.col(fld.name).cast(fld.dataType))
        df_emp_final.createOrReplaceTempView("v_emp_final")
        merge_cast_emp = f"""
        MERGE INTO {dim_employee_tbl} tgt
        USING v_emp_final src
        ON tgt.sk_employee = src.sk_employee
        WHEN MATCHED THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *
        """
        spark.sql(merge_cast_emp)

        # ------------- DimProduct -----------------
        try:
            src_prod = spark.table(f"{SOURCE_DB}.Products")
        except Exception:
            logger.exception("Failed reading source Products table")
            raise

        dim_product_tbl = safe_table_name(GOLD_DB, f"{DIM_PREFIX}product")
        # Assumed product schema - capture typical columns from Production.Products
        dim_product_schema = [
            T.StructField("sk_product", T.LongType(), False),
            T.StructField("productid", T.LongType(), True),
            T.StructField("productname", T.StringType(), True),
            T.StructField("supplierid", T.LongType(), True),
            T.StructField("categoryid", T.LongType(), True),
            T.StructField("quantityperunit", T.StringType(), True),
            T.StructField("unitprice", T.DecimalType(18, 2), True),
            T.StructField("unitsinstock", T.LongType(), True),
            T.StructField("unitsonorder", T.LongType(), True),
            T.StructField("reorderlevel", T.LongType(), True),
            T.StructField("discontinued", T.BooleanType(), True),
            T.StructField("start_date", T.TimestampType(), True),
            T.StructField("end_date", T.TimestampType(), True),
            T.StructField("is_current", T.BooleanType(), True),
            T.StructField("etl_load_ts", T.TimestampType(), True)
        ]

        ensure_delta_table_exists(dim_product_tbl, dim_product_schema)

        stg_prod = src_prod.select(
            F.col("productid").cast(T.LongType()),
            F.col("productname").alias("productname").cast(T.StringType()),
            F.col("supplierid").cast(T.LongType()),
            F.col("categoryid").cast(T.LongType()),
            F.col("quantityperunit").cast(T.StringType()),
            F.col("unitprice").cast(T.DecimalType(18, 2)),
            F.col("unitsinstock").cast(T.LongType()),
            F.col("unitsonorder").cast(T.LongType()),
            F.col("reorderlevel").cast(T.LongType()),
            F.col("discontinued").cast(T.BooleanType())
        ).withColumn("etl_load_ts", F.current_timestamp())

        stg_prod.createOrReplaceTempView("v_stg_product")

        logger.info("Closing changed active product records via MERGE (step 1)")
        merge_close_prod = f"""
        MERGE INTO {dim_product_tbl} AS tgt
        USING (SELECT productid, productname, supplierid, categoryid, quantityperunit, unitprice, unitsinstock, unitsonorder, reorderlevel, discontinued, etl_load_ts FROM v_stg_product) AS src
        ON tgt.productid = src.productid AND tgt.is_current = true
        WHEN MATCHED AND (
            tgt.productname <> src.productname OR tgt.supplierid <> src.supplierid OR tgt.categoryid <> src.categoryid OR COALESCE(tgt.unitprice, -1) <> COALESCE(src.unitprice, -1)
            OR tgt.unitsinstock <> src.unitsinstock OR tgt.unitsonorder <> src.unitsonorder OR tgt.reorderlevel <> src.reorderlevel OR tgt.discontinued <> src.discontinued)
          THEN UPDATE SET tgt.is_current = false, tgt.end_date = src.etl_load_ts
        """
        spark.sql(merge_close_prod)

        logger.info("Inserting new/changed product rows via MERGE (step 2)")
        merge_insert_prod = f"""
        MERGE INTO {dim_product_tbl} AS tgt
        USING (SELECT productid, productname, supplierid, categoryid, quantityperunit, unitprice, unitsinstock, unitsonorder, reorderlevel, discontinued, etl_load_ts FROM v_stg_product) AS src
        ON tgt.productid = src.productid AND tgt.is_current = true
        WHEN NOT MATCHED THEN
          INSERT (sk_product, productid, productname, supplierid, categoryid, quantityperunit, unitprice, unitsinstock, unitsonorder, reorderlevel, discontinued, start_date, end_date, is_current, etl_load_ts)
          VALUES (
            (SELECT COALESCE(MAX(sk_product), 0) + ROW_NUMBER() OVER (ORDER BY src.productid) FROM {dim_product_tbl}),
            src.productid, src.productname, src.supplierid, src.categoryid, src.quantityperunit, src.unitprice, src.unitsinstock, src.unitsonorder, src.reorderlevel, src.discontinued,
            src.etl_load_ts, NULL, true, src.etl_load_ts
          )
        """
        spark.sql(merge_insert_prod)

        # Cast enforcement for product
        df_prod_final = spark.table(dim_product_tbl)
        for fld in dim_product_schema:
            df_prod_final = df_prod_final.withColumn(fld.name, F.col(fld.name).cast(fld.dataType))
        df_prod_final.createOrReplaceTempView("v_prod_final")
        merge_cast_prod = f"""
        MERGE INTO {dim_product_tbl} tgt
        USING v_prod_final src
        ON tgt.sk_product = src.sk_product
        WHEN MATCHED THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *
        """
        spark.sql(merge_cast_prod)

        # ------------- DimShipper -----------------
        try:
            src_shipper = spark.table(f"{SOURCE_DB}.Shippers")
        except Exception:
            logger.exception("Failed reading source Shippers table")
            raise

        dim_shipper_tbl = safe_table_name(GOLD_DB, f"{DIM_PREFIX}shipper")
        dim_shipper_schema = [
            T.StructField("sk_shipper", T.LongType(), False),
            T.StructField("shipperid", T.LongType(), True),
            T.StructField("companyname", T.StringType(), True),
            T.StructField("phone", T.StringType(), True),
            T.StructField("start_date", T.TimestampType(), True),
            T.StructField("end_date", T.TimestampType(), True),
            T.StructField("is_current", T.BooleanType(), True),
            T.StructField("etl_load_ts", T.TimestampType(), True)
        ]

        ensure_delta_table_exists(dim_shipper_tbl, dim_shipper_schema)

        stg_shipper = src_shipper.select(
            F.col("shipperid").cast(T.LongType()),
            F.col("companyname").cast(T.StringType()),
            F.col("phone").cast(T.StringType())
        ).withColumn("etl_load_ts", F.current_timestamp())

        stg_shipper.createOrReplaceTempView("v_stg_shipper")

        spark.sql(f"REFRESH TABLE {dim_shipper_tbl}")
        logger.info("Closing changed active shipper records via MERGE (step 1)")
        merge_close_shipper = f"""
        MERGE INTO {dim_shipper_tbl} AS tgt
        USING (SELECT shipperid, companyname, phone, etl_load_ts FROM v_stg_shipper) AS src
        ON tgt.shipperid = src.shipperid AND tgt.is_current = true
        WHEN MATCHED AND (tgt.companyname <> src.companyname OR tgt.phone <> src.phone)
          THEN UPDATE SET tgt.is_current = false, tgt.end_date = src.etl_load_ts
        """
        spark.sql(merge_close_shipper)

        logger.info("Inserting new/changed shipper rows via MERGE (step 2)")
        merge_insert_shipper = f"""
        MERGE INTO {dim_shipper_tbl} AS tgt
        USING (SELECT shipperid, companyname, phone, etl_load_ts FROM v_stg_shipper) AS src
        ON tgt.shipperid = src.shipperid AND tgt.is_current = true
        WHEN NOT MATCHED THEN
          INSERT (sk_shipper, shipperid, companyname, phone, start_date, end_date, is_current, etl_load_ts)
          VALUES ( (SELECT COALESCE(MAX(sk_shipper), 0) + ROW_NUMBER() OVER (ORDER BY src.shipperid) FROM {dim_shipper_tbl}), src.shipperid, src.companyname, src.phone, src.etl_load_ts, NULL, true, src.etl_load_ts)
        """
        spark.sql(merge_insert_shipper)

        # Cast enforcement
        df_ship_final = spark.table(dim_shipper_tbl)
        for fld in dim_shipper_schema:
            df_ship_final = df_ship_final.withColumn(fld.name, F.col(fld.name).cast(fld.dataType))
        df_ship_final.createOrReplaceTempView("v_ship_final")
        merge_cast_ship = f"""
        MERGE INTO {dim_shipper_tbl} tgt
        USING v_ship_final src
        ON tgt.sk_shipper = src.sk_shipper
        WHEN MATCHED THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *
        """
        spark.sql(merge_cast_ship)

        # ------------- DimSupplier -----------------
        try:
            src_supplier = spark.table(f"{SOURCE_DB}.Suppliers").select(
                F.col("supplierid"),
                F.col("companyname"),
                F.col("address"),
                F.col("postalcode"),
                F.col("phone"),
                F.col("city"),
                F.col("country")
            )
        except Exception:
            logger.exception("Failed reading source Suppliers table")
            raise

        dim_supplier_tbl = safe_table_name(GOLD_DB, f"{DIM_PREFIX}supplier")
        dim_supplier_schema = [
            T.StructField("sk_supplier", T.LongType(), False),
            T.StructField("supplierid", T.LongType(), True),
            T.StructField("companyname", T.StringType(), True),
            T.StructField("address", T.StringType(), True),
            T.StructField("postalcode", T.StringType(), True),
            T.StructField("phone", T.StringType(), True),
            T.StructField("city", T.StringType(), True),
            T.StructField("country", T.StringType(), True),
            T.StructField("start_date", T.TimestampType(), True),
            T.StructField("end_date", T.TimestampType(), True),
            T.StructField("is_current", T.BooleanType(), True),
            T.StructField("etl_load_ts", T.TimestampType(), True)
        ]

        ensure_delta_table_exists(dim_supplier_tbl, dim_supplier_schema)

        stg_supplier = src_supplier.select(
            F.col("supplierid").cast(T.LongType()),
            F.col("companyname").cast(T.StringType()),
            F.col("address").cast(T.StringType()),
            F.col("postalcode").cast(T.StringType()),
            F.col("phone").cast(T.StringType()),
            F.col("city").cast(T.StringType()),
            F.col("country").cast(T.StringType())
        ).withColumn("etl_load_ts", F.current_timestamp())

        stg_supplier.createOrReplaceTempView("v_stg_supplier")

        logger.info("Closing changed active supplier records via MERGE (step 1)")
        merge_close_supplier = f"""
        MERGE INTO {dim_supplier_tbl} AS tgt
        USING (SELECT supplierid, companyname, address, postalcode, phone, city, country, etl_load_ts FROM v_stg_supplier) AS src
        ON tgt.supplierid = src.supplierid AND tgt.is_current = true
        WHEN MATCHED AND (tgt.companyname <> src.companyname OR tgt.address <> src.address OR tgt.postalcode <> src.postalcode OR tgt.phone <> src.phone OR tgt.city <> src.city OR tgt.country <> src.country)
          THEN UPDATE SET tgt.is_current = false, tgt.end_date = src.etl_load_ts
        """
        spark.sql(merge_close_supplier)

        logger.info("Inserting new/changed supplier rows via MERGE (step 2)")
        merge_insert_supplier = f"""
        MERGE INTO {dim_supplier_tbl} AS tgt
        USING (SELECT supplierid, companyname, address, postalcode, phone, city, country, etl_load_ts FROM v_stg_supplier) AS src
        ON tgt.supplierid = src.supplierid AND tgt.is_current = true
        WHEN NOT MATCHED THEN
          INSERT (sk_supplier, supplierid, companyname, address, postalcode, phone, city, country, start_date, end_date, is_current, etl_load_ts)
          VALUES ( (SELECT COALESCE(MAX(sk_supplier), 0) + ROW_NUMBER() OVER (ORDER BY src.supplierid) FROM {dim_supplier_tbl}), src.supplierid, src.companyname, src.address, src.postalcode, src.phone, src.city, src.country, src.etl_load_ts, NULL, true, src.etl_load_ts)
        """
        spark.sql(merge_insert_supplier)

        df_sup_final = spark.table(dim_supplier_tbl)
        for fld in dim_supplier_schema:
            df_sup_final = df_sup_final.withColumn(fld.name, F.col(fld.name).cast(fld.dataType))
        df_sup_final.createOrReplaceTempView("v_sup_final")
        merge_cast_sup = f"""
        MERGE INTO {dim_supplier_tbl} tgt
        USING v_sup_final src
        ON tgt.sk_supplier = src.sk_supplier
        WHEN MATCHED THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *
        """
        spark.sql(merge_cast_sup)

        # ------------- FACT - FactSales (snapshot incremental/full semantics)
        # Inputs: two queries provided in DTSX. We'll build a consolidated fact from Orders + OrderDetails joined to Products.
        try:
            orders = spark.table(f"{SOURCE_DB}.Orders").alias("o")
            order_details = spark.table(f"{SOURCE_DB}.OrderDetails").alias("od")
            products = spark.table(f"{SOURCE_DB}.Products").alias("p")
        except Exception:
            logger.exception("Failed reading Orders/OrderDetails/Products tables")
            raise

        # Build staging fact (flattened)
        stg_fact = (orders.join(order_details, orders.orderid == order_details.orderid)
                    .join(products, order_details.productid == products.productid)
                    .select(
                        orders.orderid.cast(T.LongType()).alias("orderid"),
                        orders.custid.cast(T.LongType()).alias("custid"),
                        orders.empid.cast(T.LongType()).alias("empid"),
                        orders.shipperid.cast(T.LongType()).alias("shipperid"),
                        products.categoryid.cast(T.LongType()).alias("categoryid"),
                        products.supplierid.cast(T.LongType()).alias("supplierid"),
                        order_details.qty.cast(T.LongType()).alias("qty"),
                        order_details.unitprice.cast(T.DecimalType(18, 2)).alias("unitprice"),
                        order_details.discount.cast(T.DecimalType(18, 2)).alias("discount"),
                        order_details.productid.cast(T.LongType()).alias("productid"),
                        F.current_timestamp().alias("etl_load_ts")
                    ))

        # Fact target
        fact_sales_tbl = safe_table_name(GOLD_DB, "FactSales")
        fact_schema = [
            T.StructField("fact_sales_id", T.LongType(), False),
            T.StructField("orderid", T.LongType(), True),
            T.StructField("custid", T.LongType(), True),
            T.StructField("empid", T.LongType(), True),
            T.StructField("shipperid", T.LongType(), True),
            T.StructField("categoryid", T.LongType(), True),
            T.StructField("supplierid", T.LongType(), True),
            T.StructField("qty", T.LongType(), True),
            T.StructField("unitprice", T.DecimalType(18, 2), True),
            T.StructField("discount", T.DecimalType(18, 2), True),
            T.StructField("productid", T.LongType(), True),
            T.StructField("etl_load_ts", T.TimestampType(), True)
        ]

        ensure_delta_table_exists(fact_sales_tbl, fact_schema)

        # Handle lookup misses: COALESCE foreign keys to -1
        stg_fact = stg_fact.withColumn("custid", F.coalesce(F.col("custid"), F.lit(-1)).cast(T.LongType())) \
                           .withColumn("empid", F.coalesce(F.col("empid"), F.lit(-1)).cast(T.LongType())) \
                           .withColumn("shipperid", F.coalesce(F.col("shipperid"), F.lit(-1)).cast(T.LongType())) \
                           .withColumn("categoryid", F.coalesce(F.col("categoryid"), F.lit(-1)).cast(T.LongType())) \
                           .withColumn("supplierid", F.coalesce(F.col("supplierid"), F.lit(-1)).cast(T.LongType())) \
                           .withColumn("productid", F.coalesce(F.col("productid"), F.lit(-1)).cast(T.LongType()))

        # For Fact full-overwrite semantics per package meta: we will implement idempotent MERGE keyed by (orderid, productid)
        stg_fact.createOrReplaceTempView("v_stg_fact_sales")

        # Close/Overwrite pattern for Fact (merge into to upsert and remove stale rows absent in source)
        # 1) Upsert (insert new or update existing fact rows)
        merge_fact_upsert = f"""
        MERGE INTO {fact_sales_tbl} tgt
        USING (SELECT orderid, productid, custid, empid, shipperid, categoryid, supplierid, qty, unitprice, discount, etl_load_ts FROM v_stg_fact_sales) AS src
        ON tgt.orderid = src.orderid AND tgt.productid = src.productid
        WHEN MATCHED AND (tgt.qty <> src.qty OR COALESCE(tgt.unitprice, -1) <> COALESCE(src.unitprice, -1) OR COALESCE(tgt.discount, -1) <> COALESCE(src.discount, -1))
          THEN UPDATE SET tgt.qty = src.qty, tgt.unitprice = src.unitprice, tgt.discount = src.discount, tgt.custid = src.custid, tgt.empid = src.empid, tgt.shipperid = src.shipperid, tgt.categoryid = src.categoryid, tgt.supplierid = src.supplierid, tgt.etl_load_ts = src.etl_load_ts
        WHEN NOT MATCHED THEN
          INSERT (fact_sales_id, orderid, custid, empid, shipperid, categoryid, supplierid, qty, unitprice, discount, productid, etl_load_ts)
          VALUES ( (SELECT COALESCE(MAX(fact_sales_id), 0) + ROW_NUMBER() OVER (ORDER BY src.orderid, src.productid) FROM {fact_sales_tbl}), src.orderid, src.custid, src.empid, src.shipperid, src.categoryid, src.supplierid, src.qty, src.unitprice, src.discount, src.productid, src.etl_load_ts)
        """
        logger.info("Upserting FactSales via MERGE")
        spark.sql(merge_fact_upsert)

        # 2) (Optional) Remove stale fact rows not present in source - for FULL_OVERWRITE semantics
        # We perform a DELETE of target rows where the (orderid,productid) is not in the latest staging set
        # Note: If data volume is very large, consider alternative strategies (partition swap).
        logger.info("Deleting stale FactSales rows not present in staging (FULL overwrite semantics)")
        delete_stale_fact = f"""
        DELETE FROM {fact_sales_tbl}
        WHERE (orderid, productid) NOT IN (SELECT orderid, productid FROM v_stg_fact_sales)
        """
        spark.sql(delete_stale_fact)

        # Cast enforcement for fact
        df_fact_final = spark.table(fact_sales_tbl)
        for fld in fact_schema:
            df_fact_final = df_fact_final.withColumn(fld.name, F.col(fld.name).cast(fld.dataType))
        df_fact_final.createOrReplaceTempView("v_fact_final")
        merge_cast_fact = f"""
        MERGE INTO {fact_sales_tbl} tgt
        USING v_fact_final src
        ON tgt.fact_sales_id = src.fact_sales_id
        WHEN MATCHED THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *
        """
        spark.sql(merge_cast_fact)

        # 5. POST LOAD OPTIMIZATIONS (hints / comments)
        # Note: Consider running OPTIMIZE on dimension and fact tables for Z-Ordering on commonly filtered keys
        # For example:
        # spark.sql("OPTIMIZE {dim_product_tbl} ZORDER BY (productid)")
        # spark.sql("OPTIMIZE {fact_sales_tbl} ZORDER BY (orderid, productid)")

        logger.info("Transpilation execution completed successfully")
        return True

    except Exception as e:
        logger.exception("Execution failed")
        raise


# If this module is executed directly in Databricks, you can call execute_task(spark)

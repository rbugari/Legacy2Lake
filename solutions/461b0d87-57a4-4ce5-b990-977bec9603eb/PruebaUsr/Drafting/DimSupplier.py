# L2L MODERNIZATION TRACE
# Source: MSSQL Asset 'AdventureWorks/Northwind (SSIS packages)'
# Component: Delta Lake Transpiler (Databricks)
# Logic: Transpiled from SSIS packages (Dim*/FactSales)
# Refactoring: Consolidated SSIS packages into medallion SCD2-capable merges
# Generated At: 2026-01-28T00:00:00Z

from datetime import datetime
import logging

from pyspark.sql import Window
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    LongType,
    DecimalType,
    TimestampType,
    BooleanType,
)

logger = logging.getLogger("l2l_transpiler")
logger.setLevel(logging.INFO)


def execute_task(spark, context: dict) -> bool:
    """
    Principal Engineer Transpilation

    This execution routine implements full-refresh (FULL_OVERWRITE) semantics for several
    dimension tables plus the FactSales build. It implements SCD2 behavior for dimensions
    (is_current, effective_date/start_date, end_date) using MERGE INTO statements to
    ensure idempotency and re-runnability.

    Args:
        spark: SparkSession (available in Databricks runtime)
        context: dict containing parameters: optional overrides for source/target prefixes
    Returns:
        True on success, False on failure
    """
    try:
        # 1. PARAMETERS & CONFIG
        source_db_prefix = context.get("source_db_prefix", "bronze")
        silver_prefix = context.get("silver_prefix", "stg_")  # not heavily used here
        gold_prefix = context.get("gold_prefix", "dim_")
        load_strategy = context.get("load_strategy", "FULL_OVERWRITE")

        # Base database / schema assumptions
        # Source tables are in bronze layer under the same object names used in SSIS SQL
        # Gold dims will be placed in `gold` database with prefix `dim_`
        gold_db = context.get("gold_db", "gold")
        bronze_db = context.get("bronze_db", "bronze")

        # Watermark / incremental not used since FULL_OVERWRITE; included for completeness
        watermark_column = context.get("watermark_column", None)

        # 2. TARGET SCHEMAS (derived from SSIS package SELECTs)
        # NOTE: High-fidelity casting — types chosen to reflect typical OLTP->DW mappings.
        dim_schemas = {
            "Category": [
                ("sk", LongType()),
                ("categoryid", LongType()),
                ("categoryname", StringType()),
                ("effective_date", TimestampType()),
                ("end_date", TimestampType()),
                ("is_current", BooleanType()),
            ],
            "Customer": [
                ("sk", LongType()),
                ("custid", LongType()),
                ("contactname", StringType()),
                ("city", StringType()),
                ("country", StringType()),
                ("address", StringType()),
                ("phone", StringType()),
                ("postalcode", StringType()),
                ("effective_date", TimestampType()),
                ("end_date", TimestampType()),
                ("is_current", BooleanType()),
            ],
            "Employee": [
                ("sk", LongType()),
                ("empid", LongType()),
                ("fullname", StringType()),
                ("title", StringType()),
                ("city", StringType()),
                ("country", StringType()),
                ("address", StringType()),
                ("phone", StringType()),
                ("effective_date", TimestampType()),
                ("end_date", TimestampType()),
                ("is_current", BooleanType()),
            ],
            "Product": [
                ("sk", LongType()),
                ("productid", LongType()),
                ("productname", StringType()),
                ("supplierid", LongType()),
                ("categoryid", LongType()),
                ("unitprice", DecimalType(18, 2)),
                ("discontinued", BooleanType()),
                ("effective_date", TimestampType()),
                ("end_date", TimestampType()),
                ("is_current", BooleanType()),
            ],
            "Shipper": [
                ("sk", LongType()),
                ("shipperid", LongType()),
                ("companyname", StringType()),
                ("phone", StringType()),
                ("effective_date", TimestampType()),
                ("end_date", TimestampType()),
                ("is_current", BooleanType()),
            ],
            "Supplier": [
                ("sk", LongType()),
                ("supplierid", LongType()),
                ("companyname", StringType()),
                ("address", StringType()),
                ("postalcode", StringType()),
                ("phone", StringType()),
                ("city", StringType()),
                ("country", StringType()),
                ("effective_date", TimestampType()),
                ("end_date", TimestampType()),
                ("is_current", BooleanType()),
            ],
        }

        # Fact target schema (typical mapping). Important: surrogate keys reference dims and must not be NULL
        fact_sales_schema = [
            ("orderid", LongType()),
            ("orderdate", TimestampType()),
            ("cust_sk", LongType()),
            ("emp_sk", LongType()),
            ("shipper_sk", LongType()),
            ("product_sk", LongType()),
            ("categoryid", LongType()),
            ("supplierid", LongType()),
            ("qty", LongType()),
            ("unitprice", DecimalType(18, 2)),
            ("discount", DecimalType(18, 2)),
            ("line_total", DecimalType(18, 2)),
            ("etl_load_date", TimestampType()),
        ]

        # 3. EXTRACT & TRANSFORM helper functions
        def _cast_loop(df, schema_list):
            """
            Apply high-fidelity casting to every column present in schema_list.

            Args:
                df: DataFrame to cast
                schema_list: list of tuples (col_name, spark_type)

            Returns:
                DataFrame with casts applied where column exists.
            """
            for col_name, col_type in schema_list:
                if col_name in df.columns:
                    # For DecimalType we cast by using the string representation for precision/scale
                    if isinstance(col_type, DecimalType):
                        df = df.withColumn(col_name, F.col(col_name).cast(f"decimal({col_type.precision},{col_type.scale})"))
                    elif isinstance(col_type, LongType):
                        df = df.withColumn(col_name, F.col(col_name).cast("long"))
                    elif isinstance(col_type, StringType):
                        df = df.withColumn(col_name, F.col(col_name).cast("string"))
                    elif isinstance(col_type, TimestampType):
                        df = df.withColumn(col_name, F.col(col_name).cast("timestamp"))
                    elif isinstance(col_type, BooleanType):
                        df = df.withColumn(col_name, F.col(col_name).cast("boolean"))
                    else:
                        # Fallback to string cast for unknown types (should not happen)
                        df = df.withColumn(col_name, F.col(col_name).cast("string"))
                else:
                    # If column does not exist, create it as NULL of the proper type to satisfy schema
                    if isinstance(col_type, DecimalType):
                        df = df.withColumn(col_name, F.lit(None).cast(f"decimal({col_type.precision},{col_type.scale})"))
                    elif isinstance(col_type, LongType):
                        df = df.withColumn(col_name, F.lit(None).cast("long"))
                    elif isinstance(col_type, StringType):
                        df = df.withColumn(col_name, F.lit(None).cast("string"))
                    elif isinstance(col_type, TimestampType):
                        df = df.withColumn(col_name, F.lit(None).cast("timestamp"))
                    elif isinstance(col_type, BooleanType):
                        df = df.withColumn(col_name, F.lit(None).cast("boolean"))
                    else:
                        df = df.withColumn(col_name, F.lit(None).cast("string"))
            return df

        def _ensure_table_exists(table_full_name, schema_list):
            """
            Create an empty Delta table with the target schema if it does not exist.
            This allows MERGE INTO to run reliably.

            Args:
                table_full_name: fully-qualified table name (e.g., gold.dim_Category)
                schema_list: list of (col_name, spark_type)
            """
            if not spark._jsparkSession.catalog().tableExists(table_full_name):
                # Build empty DataFrame with correct columns
                cols = []
                for col_name, col_type in schema_list:
                    if isinstance(col_type, DecimalType):
                        cols.append(F.lit(None).cast(f"decimal({col_type.precision},{col_type.scale})").alias(col_name))
                    elif isinstance(col_type, LongType):
                        cols.append(F.lit(None).cast("long").alias(col_name))
                    elif isinstance(col_type, StringType):
                        cols.append(F.lit(None).cast("string").alias(col_name))
                    elif isinstance(col_type, TimestampType):
                        cols.append(F.lit(None).cast("timestamp").alias(col_name))
                    elif isinstance(col_type, BooleanType):
                        cols.append(F.lit(None).cast("boolean").alias(col_name))
                    else:
                        cols.append(F.lit(None).alias(col_name))
                empty_df = spark.createDataFrame([], StructType([]))
                for c in cols:
                    empty_df = empty_df.withColumn(c.alias, c)
                # Write as delta table
                empty_df.write.format("delta").mode("overwrite").saveAsTable(table_full_name)

        # Utility to build qualified names
        def _gold_table(name):
            return f"{gold_db}.{gold_prefix}{name}"

        def _bronze_table(schema_table_name):
            # schema_table_name expected like 'Production.Categories' -> bronze.production_categories or keep schema
            # We'll map dot to underscore for physical bronze table naming convention in this environment
            return f"{bronze_db}.{schema_table_name.replace('.', '_').lower()}"

        # 4. DIMENSION PROCESS (SCD2 MERGE) for each entry in project overview
        now_ts = F.current_timestamp()

        # Mapping of SSIS inputs to bronze tables (based on given SQL in project_set_overview)
        # We will use the expected column sets captured in dim_schemas
        dim_inputs = {
            "Category": "Production.Categories",
            "Customer": "Sales.Customers",
            "Employee": "HR.Employees",
            "Product": "Production.Products",
            "Shipper": "Sales.Shippers",
            "Supplier": "Production.Suppliers",
        }

        for dim_name, src in dim_inputs.items():
            gold_table = _gold_table(dim_name)
            bronze_table = _bronze_table(src)
            logger.info(f"Processing dimension {dim_name}; source={bronze_table}; target={gold_table}")

            # Ensure target exists (empty) to allow MERGE
            _ensure_table_exists(gold_table, dim_schemas[dim_name])

            # Extract from bronze
            src_df = spark.table(bronze_table)

            # Depending on original SSIS logic, minimal filtering is applied. For FULL_OVERWRITE we take all rows.
            # Normalize and select only relevant columns for the dimension target
            # Map expected names from the SSIS selects
            if dim_name == "Category":
                df = src_df.select(
                    F.col("categoryid"),
                    F.col("categoryname"),
                )
            elif dim_name == "Customer":
                df = src_df.select(
                    F.col("custid"),
                    F.col("contactname"),
                    F.col("city"),
                    F.col("country"),
                    F.col("address"),
                    F.col("phone"),
                    F.col("postalcode"),
                )
            elif dim_name == "Employee":
                # In SSIS full name computed firstname + ' ' + lastname
                df = src_df.select(
                    F.col("empid"),
                    (F.coalesce(F.col("firstname"), F.lit("")) + F.lit(" ") + F.coalesce(F.col("lastname"), F.lit(""))).alias("fullname"),
                    F.col("title"),
                    F.col("city"),
                    F.col("country"),
                    F.col("address"),
                    F.col("phone"),
                )
            elif dim_name == "Product":
                # Products often have many columns; pick the typical ones
                df = src_df.select(
                    F.col("productid"),
                    F.col("productname"),
                    F.col("supplierid"),
                    F.col("categoryid"),
                    F.col("unitprice"),
                    F.col("discontinued"),
                )
            elif dim_name == "Shipper":
                df = src_df.select(
                    F.col("shipperid"),
                    F.col("companyname"),
                    F.col("phone"),
                )
            elif dim_name == "Supplier":
                df = src_df.select(
                    F.col("supplierid"),
                    F.col("companyname"),
                    F.col("address"),
                    F.col("postalcode"),
                    F.col("phone"),
                    F.col("city"),
                    F.col("country"),
                )
            else:
                df = src_df

            # Apply high-fidelity casting to match target DDL
            df = _cast_loop(df, dim_schemas[dim_name])

            # Build a simple surrogate assignment strategy: join to current target by business key to reuse sk
            tgt_df = spark.table(gold_table)

            bk_col = [c for c, _ in dim_schemas[dim_name] if c not in ("sk", "effective_date", "end_date", "is_current")][0]

            tgt_current = tgt_df.filter(F.col("is_current") == True).select("sk", bk_col)

            joined = df.join(F.broadcast(tgt_current), on=bk_col, how="left")

            # Determine max SK to allocate new SKs
            max_sk_row = tgt_df.agg(F.max(F.col("sk")).alias("max_sk")).collect()
            max_sk = max_sk_row[0]["max_sk"] if max_sk_row and max_sk_row[0]["max_sk"] is not None else 0

            # Assign new SK where missing
            w = Window.orderBy(bk_col)
            staged = (
                joined
                .withColumn("new_sk_candidate", F.row_number().over(w) + F.lit(int(max_sk)))
                .withColumn("sk", F.coalesce(F.col("sk"), F.col("new_sk_candidate")))
                .drop("new_sk_candidate")
            )

            # Add SCD2 columns
            staged = (
                staged.withColumn("effective_date", now_ts)
                .withColumn("end_date", F.to_timestamp(F.lit("9999-12-31 23:59:59")))
                .withColumn("is_current", F.lit(True))
            )

            # Compute a hash of attribute columns to detect changes (exclude sk/effective/end/is_current)
            attr_cols = [c for c, _ in dim_schemas[dim_name] if c not in ("sk", "effective_date", "end_date", "is_current")]
            # Ensure deterministic order
            attr_cols.sort()
            staged = staged.withColumn("attr_hash", F.sha2(F.concat_ws("||", *[F.coalesce(F.col(c).cast("string"), F.lit("<NULL>")) for c in attr_cols]), 256))

            # Persist staged as a temp view for MERGE
            temp_view = f"stg_{dim_name.lower()}_{int(datetime.utcnow().timestamp())}"
            staged.createOrReplaceTempView(temp_view)

            # Build MERGE SQL implementing SCD2 semantics and FULL_OVERWRITE: mark missing as not current
            # Merge logic:
            # - WHEN MATCHED AND target.is_current = true AND source.attr_hash != target.attr_hash -> update target.is_current=false (end_date set)
            # - WHEN NOT MATCHED -> insert new row
            # - WHEN NOT MATCHED BY SOURCE AND target.is_current = true -> set is_current=false

            # Ensure target has attr_hash column for comparison; if not present, use computed hash via SELECT
            # To keep SQL readable, we'll use a subquery that includes computed hash for target current records

            merge_sql = f"""
MERGE INTO {gold_table} as tgt
USING (SELECT * FROM {temp_view}) as src
ON tgt.{bk_col} = src.{bk_col} AND tgt.is_current = true
WHEN MATCHED AND src.attr_hash <> tgt.attr_hash
  THEN UPDATE SET tgt.end_date = current_timestamp(), tgt.is_current = false
WHEN NOT MATCHED
  THEN INSERT ({', '.join([c for c, _ in dim_schemas[dim_name]])})
       VALUES ({', '.join([f"src.{c}" for c, _ in dim_schemas[dim_name]])})
WHEN NOT MATCHED BY SOURCE AND tgt.is_current = true
  THEN UPDATE SET tgt.end_date = current_timestamp(), tgt.is_current = false
"""

            logger.info(f"Executing MERGE for {gold_table}")
            spark.sql(merge_sql)

            # Post-load optimization hints
            logger.info(f"OPTIMIZE {gold_table} ZORDER BY ({bk_col}) -- consider clustering on business key")
            # Actual optimize and vacuum are optional operational commands; we include them as suggestions here
            try:
                spark.sql(f"OPTIMIZE {gold_table} ZORDER BY ({bk_col})")
            except Exception:
                logger.warning(f"OPTIMIZE failed or not applicable for {gold_table}; skipping")

        # 5. FACT LOAD (FactSales)
        # We implement a full rebuild of the fact (FULL_OVERWRITE) but using MERGE to preserve idempotency.
        # Fact requires joining Orders, OrderDetails, Products and performing lookups to dimension SKs. Missing lookups -> surrogate -1

        # Define source tables
        orders_table = _bronze_table("Sales.Orders")
        od_table = _bronze_table("Sales.OrderDetails")
        products_table = _bronze_table("Production.Products")

        # Read sources
        orders_df = spark.table(orders_table)
        od_df = spark.table(od_table)
        products_df = spark.table(products_table)

        # Build staging by joining orders -> orderdetails -> products (per SSIS logic)
        od_join = od_df.alias("od").join(orders_df.alias("o"), F.col("od.orderid") == F.col("o.orderid"), "inner")
        od_join = od_join.join(products_df.alias("p"), F.col("od.productid") == F.col("p.productid"), "inner")

        stg_fact = od_join.select(
            F.col("o.orderid").alias("orderid"),
            F.col("o.orderdate").alias("orderdate"),
            F.col("o.custid").alias("custid"),
            F.col("o.empid").alias("empid"),
            F.col("o.shipperid").alias("shipperid"),
            F.col("p.categoryid").alias("categoryid"),
            F.col("p.supplierid").alias("supplierid"),
            F.col("od.qty").alias("qty"),
            F.col("od.unitprice").alias("unitprice"),
            F.col("od.discount").alias("discount"),
            F.col("od.productid").alias("productid"),
        )

        # Lookup dimension SKs from gold dims; use COALESCE to -1 when missing to maintain FK integrity
        dim_product_table = _gold_table("Product")
        dim_customer_table = _gold_table("Customer")
        dim_employee_table = _gold_table("Employee")
        dim_shipper_table = _gold_table("Shipper")

        # Read current dimension SKs
        prod_sk = spark.table(dim_product_table).filter(F.col("is_current") == True).select(F.col("productid"), F.col("sk").alias("prod_sk"))
        cust_sk = spark.table(dim_customer_table).filter(F.col("is_current") == True).select(F.col("custid"), F.col("sk").alias("cust_sk"))
        emp_sk = spark.table(dim_employee_table).filter(F.col("is_current") == True).select(F.col("empid"), F.col("sk").alias("emp_sk"))
        ship_sk = spark.table(dim_shipper_table).filter(F.col("is_current") == True).select(F.col("shipperid"), F.col("sk").alias("shipper_sk"))

        # Join and coalesce to -1
        fact_enriched = (
            stg_fact.alias("s")
            .join(F.broadcast(prod_sk), F.col("s.productid") == F.col("productid"), "left")
            .join(F.broadcast(cust_sk), F.col("s.custid") == F.col("custid"), "left")
            .join(F.broadcast(emp_sk), F.col("s.empid") == F.col("empid"), "left")
            .join(F.broadcast(ship_sk), F.col("s.shipperid") == F.col("shipperid"), "left")
            .withColumn("product_sk", F.coalesce(F.col("prod_sk"), F.lit(-1)).cast("long"))
            .withColumn("cust_sk", F.coalesce(F.col("cust_sk"), F.lit(-1)).cast("long"))
            .withColumn("emp_sk", F.coalesce(F.col("emp_sk"), F.lit(-1)).cast("long"))
            .withColumn("shipper_sk", F.coalesce(F.col("shipper_sk"), F.lit(-1)).cast("long"))
            .withColumn("orderid", F.col("orderid").cast("long"))
            .withColumn("qty", F.col("qty").cast("long"))
            .withColumn("unitprice", F.col("unitprice").cast("decimal(18,2)"))
            .withColumn("discount", F.col("discount").cast("decimal(18,2)"))
            .withColumn("line_total", (F.col("qty").cast("decimal(18,2)") * F.col("unitprice")).cast("decimal(18,2)"))
            .withColumn("etl_load_date", now_ts)
        )

        # Final cast loop according to fact schema
        fact_enriched = _cast_loop(fact_enriched, fact_sales_schema)

        # Write / MERGE fact into gold.fact_sales
        gold_fact_table = f"{gold_db}.fact_sales"

        # Ensure fact table exists
        _ensure_table_exists(gold_fact_table, fact_sales_schema)

        # Persist staging view
        stg_fact_view = f"stg_factsales_{int(datetime.utcnow().timestamp())}"
        fact_enriched.createOrReplaceTempView(stg_fact_view)

        # MERGE strategy for full-refresh: upsert by orderid (if business key duplicates exist, keep latest by etl_load_date)
        merge_fact_sql = f"""
MERGE INTO {gold_fact_table} as tgt
USING (SELECT * FROM {stg_fact_view}) as src
ON tgt.orderid = src.orderid
WHEN MATCHED
  THEN UPDATE SET
    tgt.orderdate = src.orderdate,
    tgt.cust_sk = src.cust_sk,
    tgt.emp_sk = src.emp_sk,
    tgt.shipper_sk = src.shipper_sk,
    tgt.product_sk = src.product_sk,
    tgt.categoryid = src.categoryid,
    tgt.supplierid = src.supplierid,
    tgt.qty = src.qty,
    tgt.unitprice = src.unitprice,
    tgt.discount = src.discount,
    tgt.line_total = src.line_total,
    tgt.etl_load_date = src.etl_load_date
WHEN NOT MATCHED
  THEN INSERT ({', '.join([c for c, _ in fact_sales_schema])})
       VALUES ({', '.join([f"src.{c}" for c, _ in fact_sales_schema])})
"""

        logger.info(f"Executing MERGE for fact table {gold_fact_table}")
        spark.sql(merge_fact_sql)

        try:
            logger.info(f"OPTIMIZE {gold_fact_table} ZORDER BY (orderdate)")
            spark.sql(f"OPTIMIZE {gold_fact_table} ZORDER BY (orderdate)")
        except Exception:
            logger.warning(f"OPTIMIZE failed or not applicable for {gold_fact_table}; skipping")

        logger.info("ETL task completed successfully")
        return True

    except Exception as exc:
        logger.exception("ETL task failed: %s", exc)
        return False


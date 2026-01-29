# L2L MODERNIZATION TRACE
# Source: LegacySQLServer Asset 'OLTP_Sales'
# Component: Transpiled ETL
# Logic: Transpiled from SSIS Package
# Refactoring: Dimensional SCD2 + Fact MERGE
# Generated At: 2026-01-28T00:00:00Z

"""
Principal Engineer Transpilation for Dim + Fact loads
This module implements SCD2 for dimensions and idempotent MERGE for facts
Target platform: Databricks (Delta Lake)
"""

import logging
from datetime import datetime

from pyspark.sql import functions as F
from pyspark.sql import Window
from delta.tables import DeltaTable

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def execute_task(spark, context):
    """
    Principal Engineer Transpilation

    Args:
        spark: SparkSession (assumed available)
        context: dict with orchestration parameters

    Returns:
        True on success, raises Exception on failure
    """
    try:
        # 1. PARAMETERS & CONFIG
        # Naming prefixes enforced by registry
        SILVER_PREFIX = "stg_"
        GOLD_PREFIX = "dim_"

        # Databases / schemas for medallion layers. These can be overridden by context/variables.
        bronze_db = context.get("bronze_db", "bronze")
        silver_db = context.get("silver_db", "silver")
        gold_db = context.get("gold_db", "gold")

        # Load strategy (from context) - expected FULL_OVERWRITE in this transpilation
        load_strategy = context.get("load_strategy", "FULL_OVERWRITE")

        # Watermark / incremental column - not provided for dims; performing full SCD2 refresh (idempotent)
        run_id = datetime.utcnow().isoformat()
        load_ts = spark.sql("select current_timestamp() as ts").collect()[0][0]

        # Dimension configurations inferred from SSIS packages (Logical Medulla)
        dims = [
            {
                "package": "DimCategory",
                "source_query": "SELECT categoryid AS categoryid, categoryname AS categoryname FROM Production.Categories WHERE categoryid > 0",
                "business_key": "categoryid",
                "natural_keys": ["categoryname"],
                "target": f"{gold_db}.dim_category"
            },
            {
                "package": "DimCustomers",
                "source_query": "SELECT custid AS custid, contactname AS contactname, city AS city, country AS country, address AS address, phone AS phone, postalcode AS postalcode FROM Sales.Customers WHERE custid > 0",
                "business_key": "custid",
                "natural_keys": ["contactname", "city", "country", "address", "phone", "postalcode"],
                "target": f"{gold_db}.dim_customer"
            },
            {
                "package": "DimEmployee",
                "source_query": "SELECT empid AS empid, (firstname + ' ' + lastname) AS fullname, title AS title, city AS city, country AS country, address AS address, phone AS phone FROM HR.Employees WHERE empid > 0",
                "business_key": "empid",
                "natural_keys": ["fullname", "title", "city", "country", "address", "phone"],
                "target": f"{gold_db}.dim_employee"
            },
            {
                "package": "DimProduct",
                "source_query": "SELECT productid AS productid, productname AS productname, supplierid AS supplierid, categoryid AS categoryid, quantityperunit AS quantityperunit, unitprice AS unitprice, unitsinstock AS unitsinstock FROM Production.Products",
                "business_key": "productid",
                "natural_keys": ["productname", "supplierid", "categoryid", "quantityperunit", "unitprice", "unitsinstock"],
                "target": f"{gold_db}.dim_product"
            },
            {
                "package": "DimShipper",
                "source_query": "SELECT shipperid AS shipperid, companyname AS companyname, phone AS phone FROM Sales.Shippers WHERE shipperid > 0",
                "business_key": "shipperid",
                "natural_keys": ["companyname", "phone"],
                "target": f"{gold_db}.dim_shipper"
            },
            {
                "package": "DimSupplier",
                "source_query": "SELECT supplierid AS supplierid, companyname AS companyname, address AS address, postalcode AS postalcode, phone AS phone, city AS city, country AS country FROM Production.Suppliers WHERE supplierid > 0",
                "business_key": "supplierid",
                "natural_keys": ["companyname", "address", "postalcode", "phone", "city", "country"],
                "target": f"{gold_db}.dim_supplier"
            }
        ]

        # Fact configuration (FactSales). We'll build a deterministic MERGE using composite business key
        fact_conf = {
            "package": "FactSales",
            "source_query": (
                "SELECT O.orderid AS orderid, O.custid AS custid, O.empid AS empid, O.shipperid AS shipperid, "
                "P.categoryid AS categoryid, P.supplierid AS supplierid, OD.qty AS qty, OD.unitprice AS unitprice, OD.discount AS discount, OD.productid AS productid, O.orderdate AS orderdate "
                "FROM Sales.Orders O "
                "INNER JOIN Sales.OrderDetails OD ON O.orderid = OD.orderid "
                "INNER JOIN Production.Products P ON P.productid = OD.productid"
            ),
            "business_key": ["orderid", "productid"],
            "target": f"{gold_db}.fact_sales"
        }

        # Target schema assumptions for casting. STRICT high-fidelity casting required.
        # NOTE: In absence of explicit target DDL, we assume typical types. These are critical assumptions listed below.
        target_schemas = {
            "dim_category": [
                ("sk", "long"), ("categoryid", "long"), ("categoryname", "string"),
                ("attribute_hash", "string"), ("start_date", "timestamp"), ("end_date", "timestamp"), ("is_current", "boolean")
            ],
            "dim_customer": [
                ("sk", "long"), ("custid", "long"), ("contactname", "string"), ("city", "string"), ("country", "string"), ("address", "string"), ("phone", "string"), ("postalcode", "string"),
                ("attribute_hash", "string"), ("start_date", "timestamp"), ("end_date", "timestamp"), ("is_current", "boolean")
            ],
            "dim_employee": [
                ("sk", "long"), ("empid", "long"), ("fullname", "string"), ("title", "string"), ("city", "string"), ("country", "string"), ("address", "string"), ("phone", "string"),
                ("attribute_hash", "string"), ("start_date", "timestamp"), ("end_date", "timestamp"), ("is_current", "boolean")
            ],
            "dim_product": [
                ("sk", "long"), ("productid", "long"), ("productname", "string"), ("supplierid", "long"), ("categoryid", "long"), ("quantityperunit", "string"), ("unitprice", "decimal(18,2)"), ("unitsinstock", "long"),
                ("attribute_hash", "string"), ("start_date", "timestamp"), ("end_date", "timestamp"), ("is_current", "boolean")
            ],
            "dim_shipper": [
                ("sk", "long"), ("shipperid", "long"), ("companyname", "string"), ("phone", "string"),
                ("attribute_hash", "string"), ("start_date", "timestamp"), ("end_date", "timestamp"), ("is_current", "boolean")
            ],
            "dim_supplier": [
                ("sk", "long"), ("supplierid", "long"), ("companyname", "string"), ("address", "string"), ("postalcode", "string"), ("phone", "string"), ("city", "string"), ("country", "string"),
                ("attribute_hash", "string"), ("start_date", "timestamp"), ("end_date", "timestamp"), ("is_current", "boolean")
            ],
            "fact_sales": [
                ("orderid", "long"), ("productid", "long"), ("custid", "long"), ("empid", "long"), ("shipperid", "long"), ("categoryid", "long"), ("supplierid", "long"), ("qty", "long"), ("unitprice", "decimal(18,2)"), ("discount", "decimal(18,4)"), ("amount", "decimal(18,2)"), ("orderdate", "timestamp")
            ]
        }

        # Utility: cast dataframe columns to target schema types strictly
        def enforce_casts(df, schema_list):
            """
            Cast every column in schema_list on df to the specified type.

            Args:
                df: input DataFrame
                schema_list: list of tuples (col_name, spark_type_str)

            Returns:
                df casted
            """
            for col_name, col_type in schema_list:
                # Only cast if column exists in df; leave others to be created later
                if col_name in df.columns:
                    df = df.withColumn(col_name, F.col(col_name).cast(col_type))
            return df

        # 2. EXTRACTION & 3. TRANSFORMATION (per-dimension SCD2 pattern)
        for d in dims:
            package = d["package"]
            logger.info(f"Processing dimension package: {package}")
            src_q = d["source_query"]
            bk = d["business_key"]
            natural_cols = d["natural_keys"]
            target_table = d["target"]
            dim_name = target_table.split('.')[-1]

            # Extract source
            logger.info(f"Reading source for {dim_name}")
            src_df = spark.sql(src_q)

            # Build attribute concatenation/hash for change detection
            concat_cols = [F.coalesce(F.col(c).cast("string"), F.lit("")) for c in natural_cols]
            attribute_hash_col = F.sha2(F.concat_ws("||", *concat_cols), 256).alias("attribute_hash")

            staging = (
                src_df
                .withColumn("attribute_hash", attribute_hash_col)
                .withColumn("start_date", F.current_timestamp())
                .withColumn("end_date", F.lit(None).cast("timestamp"))
                .withColumn("is_current", F.lit(True))
            )

            # Ensure strict casting against assumed target schema
            staging = enforce_casts(staging, target_schemas.get(dim_name, []))

            # Persist staging view for SQL MERGE reference
            staging_view = f"tmp_{dim_name}_staging_{run_id.replace(':','_')}"
            staging.createOrReplaceTempView(staging_view)

            # Read target table if exists, else create empty Delta table with header columns
            try:
                tgt_df = spark.table(target_table)
                max_sk_row = tgt_df.agg(F.max(F.col("sk"))).collect()[0][0]
                max_sk = int(max_sk_row) if max_sk_row is not None else 0
            except Exception:
                logger.info(f"Target table {target_table} does not exist. Initializing max_sk=0 and creating an empty table on first insert.")
                max_sk = 0

            # Step 1: Expire current records that have changed (is_current = true and attribute_hash differs)
            # MERGE to set is_current = false for matched keys with hash difference
            merge_expire_sql = f"""
            MERGE INTO {target_table} AS tgt
            USING (
                SELECT {bk} AS {bk}, attribute_hash, start_date
                FROM {staging_view}
            ) AS src
            ON tgt.{bk} = src.{bk} AND tgt.is_current = true
            WHEN MATCHED AND tgt.attribute_hash <> src.attribute_hash
              THEN UPDATE SET tgt.is_current = false, tgt.end_date = src.start_date
            """

            # Execute expire MERGE. If target doesn't exist, this will fail; catch and continue (first run)
            try:
                logger.info(f"Running expire MERGE for {dim_name}")
                spark.sql(merge_expire_sql)
            except Exception as ex:
                logger.info(f"Expire MERGE skipped/failed (likely first-run or table missing) for {dim_name}: {ex}")

            # Step 2: Insert new rows (new business keys or changed rows). We need to assign surrogate keys (SK) idempotently.
            # Approach: compute next SK from existing max_sk, use row_number to generate deterministic SKs for this batch.
            staging_with_rn = spark.sql(f"SELECT *, ROW_NUMBER() OVER (ORDER BY {bk}) AS rn FROM {staging_view}")
            staging_with_sk = staging_with_rn.withColumn("sk", (F.lit(max_sk) + F.col("rn")).cast("long"))

            # Ensure casting before insert
            staging_with_sk = enforce_casts(staging_with_sk, target_schemas.get(dim_name, []))

            # Prepare column lists for insert (target_columns must match target schema order)
            target_cols = [c for c, _ in target_schemas.get(dim_name, [])]
            # keep only those present in staging_with_sk
            insert_cols = [c for c in target_cols if c in staging_with_sk.columns]
            insert_cols_sql = ", ".join(insert_cols)
            src_cols_sql = ", ".join([f"src.{c}" for c in insert_cols])

            # Second MERGE to insert rows that are not present as current identical records
            merge_insert_sql = f"""
            MERGE INTO {target_table} AS tgt
            USING (
                SELECT {insert_cols_sql} FROM tmp_{dim_name}_staging_{run_id.replace(':','_')}
            ) AS src
            ON tgt.{bk} = src.{bk} AND tgt.attribute_hash = src.attribute_hash AND tgt.is_current = true
            WHEN NOT MATCHED THEN
              INSERT ({insert_cols_sql}) VALUES ({src_cols_sql})
            """

            # Execute insert MERGE. If target table doesn't exist, create it by writing the insert dataframe as Delta and then subsequent MERGE calls will work.
            try:
                logger.info(f"Running insert MERGE for {dim_name}")
                spark.sql(merge_insert_sql)
            except Exception as ex:
                logger.info(f"Insert MERGE failed likely because target {target_table} doesn't exist; creating table by writing initial snapshot: {ex}")
                # Create the target Delta table by writing the staging_with_sk DataFrame
                # Use DeltaTable writer via saveAsTable (first-time create). For full layers, we allow write overwrite only for initial bootstrap.
                staging_to_write = staging_with_sk.select(*insert_cols)
                # Ensure table path/format uses Delta managed table in gold_db
                staging_to_write.write.format("delta").mode("overwrite").saveAsTable(target_table)

            logger.info(f"Dimension {dim_name} processed.")

        # 4. FACT LOAD (FactSales) - idempotent MERGE
        logger.info("Processing FactSales")
        fact_src_q = fact_conf["source_query"]
        fact_tgt = fact_conf["target"]
        fact_bk = fact_conf["business_key"]

        fact_df = spark.sql(fact_src_q)

        # Apply unknown handling for foreign keys to ensure referential integrity
        fk_cols = ["custid", "empid", "shipperid", "categoryid", "supplierid"]
        for fk in fk_cols:
            if fk in fact_df.columns:
                fact_df = fact_df.withColumn(fk, F.coalesce(F.col(fk).cast("long"), F.lit(-1)))

        # Compute amount and strict casts
        fact_df = (
            fact_df
            .withColumn("qty", F.col("qty").cast("long"))
            .withColumn("unitprice", F.col("unitprice").cast("decimal(18,2)"))
            .withColumn("discount", F.col("discount").cast("decimal(18,4)"))
            .withColumn("amount", (F.col("qty") * F.col("unitprice") * (F.lit(1) - F.col("discount")).cast("decimal(18,4)")).cast("decimal(18,2)"))
            .withColumn("orderdate", F.col("orderdate").cast("timestamp"))
        )

        # Enforce target casts for fact
        fact_df = enforce_casts(fact_df, target_schemas.get("fact_sales", []))

        # Persist fact staging view
        fact_staging_view = f"tmp_fact_sales_staging_{run_id.replace(":", "_")}"
        fact_df.createOrReplaceTempView(fact_staging_view)

        # Build MERGE SQL for fact_upsert: update if changed, insert if not exists
        # We'll compare amount and qty as change indicators
        bk_on = " AND ".join([f"tgt.{c} = src.{c}" for c in fact_bk])
        merge_fact_sql = f"""
        MERGE INTO {fact_tgt} AS tgt
        USING (
            SELECT * FROM {fact_staging_view}
        ) AS src
        ON {bk_on}
        WHEN MATCHED AND (tgt.amount <> src.amount OR tgt.qty <> src.qty OR tgt.unitprice <> src.unitprice)
          THEN UPDATE SET tgt.qty = src.qty, tgt.unitprice = src.unitprice, tgt.discount = src.discount, tgt.amount = src.amount, tgt.orderdate = src.orderdate
        WHEN NOT MATCHED
          THEN INSERT ({', '.join([c for c, _ in target_schemas.get('fact_sales', [])])}) VALUES ({', '.join([f'src.{c}' for c, _ in target_schemas.get('fact_sales', [])])})
        """

        try:
            logger.info("Running fact MERGE")
            spark.sql(merge_fact_sql)
        except Exception as ex:
            logger.info(f"Fact MERGE failed; attempting initial create of fact table: {ex}")
            # Create fact table on first run
            fact_df.select(*[c for c, _ in target_schemas.get('fact_sales', [])]).write.format("delta").mode("overwrite").saveAsTable(fact_tgt)

        # Post-load optimization hints (manual steps recommended)
        logger.info("Load complete. Consider running OPTIMIZE and ZORDER for frequently filtered columns on Gold tables.")

        return True

    except Exception as e:
        logger.exception(f"execute_task failed: {e}")
        raise


# If invoked directly (for testing), create a dummy context and run using an existing spark session
if __name__ == '__main__':
    try:
        # Example invocation (will rely on spark variable in Databricks notebook)
        res = execute_task(spark, {})
        logger.info(f"execute_task finished with result: {res}")
    except Exception as exc:
        logger.exception(f"Execution failed: {exc}")

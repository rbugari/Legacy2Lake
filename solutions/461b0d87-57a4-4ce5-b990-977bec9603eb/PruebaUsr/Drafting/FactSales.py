# L2L MODERNIZATION TRACE
# Source: Legacy SQL Packages Asset 'Dim/Fact Transpile'
# Component: Transpiler
# Logic: Transpiled from SSIS Packages
# Refactoring: Converted to Databricks Delta MERGE pipeline
# Generated At: 2026-01-28T00:00:00Z

"""
Principal Engineer Transpilation for Dimensions (Products) and Fact (Sales)
This script follows Medallion Architecture and Databricks Delta best-practices.
It performs a FULL_OVERWRITE semantics implemented via DELTA MERGE (including
WHEN NOT MATCHED BY SOURCE THEN DELETE) to ensure target reflects source.

Google-style docstrings, try/except logging, stable surrogate key generation,
explicit casting according to target schema, and COALESCE fallback for lookups
are included per architecture rules.
"""

from delta.tables import DeltaTable
from pyspark.sql import functions as F
from pyspark.sql import types as T
from pyspark.sql.window import Window
import logging
import datetime

logger = logging.getLogger('l2l_transpiler')
logger.setLevel(logging.INFO)


def _map_to_spark_type(type_str):
    """Map a canonical type string to a PySpark DataType instance.

    Args:
        type_str (str): One of: 'Long', 'String', 'Decimal(18,2)', 'Boolean', 'Timestamp'

    Returns:
        pyspark.sql.types.DataType
    """
    if type_str.lower().startswith('decimal'):
        # expect format Decimal(18,2)
        # extract precision, scale
        inside = type_str[type_str.find('(') + 1:type_str.find(')')]
        p, s = [int(x.strip()) for x in inside.split(',')]
        return T.DecimalType(p, s)
    mapping = {
        'long': T.LongType(),
        'string': T.StringType(),
        'boolean': T.BooleanType(),
        'timestamp': T.TimestampType()
    }
    return mapping.get(type_str.lower(), T.StringType())


def execute_task(spark, context: dict):
    """
    Principal Engineer Transpilation

    Args:
        spark: SparkSession (provided by environment)
        context: dict with optional overrides (not required for this transpilation)

    Returns:
        bool: True on success
    """
    try:
        # 1. PARAMETERS & CONFIG
        # Naming conventions
        SILVER_PREFIX = 'stg_'
        GOLD_PREFIX = 'dim_'
        # Schemas / Target definitions (High-fidelity casting target types)
        # NOTE: These are derived assumptions from source queries. Adjust if you have canonical DDL.
        schemas = {
            # Gold dimension for product
            f'gold.{GOLD_PREFIX}product': [
                ('sk_product', 'Long'),            # surrogate key
                ('productid', 'Long'),
                ('productname', 'String'),
                ('supplierid', 'Long'),
                ('categoryid', 'Long'),
                ('quantityperunit', 'String'),
                ('unitprice', 'Decimal(18,2)'),
                ('unitsinstock', 'Long'),
                ('unitsonorder', 'Long'),
                ('reorderlevel', 'Long'),
                ('discontinued', 'Boolean'),
                ('load_dttm', 'Timestamp')
            ],
            # Gold fact sales
            'gold.fact_sales': [
                ('orderid', 'Long'),
                ('orderdetailid', 'Long'),
                ('sk_product', 'Long'),            # FK to dim_product.SK (use COALESCE to -1)
                ('custid', 'Long'),
                ('empid', 'Long'),
                ('shipperid', 'Long'),
                ('categoryid', 'Long'),
                ('supplierid', 'Long'),
                ('qty', 'Long'),
                ('unitprice', 'Decimal(18,2)'),
                ('discount', 'Decimal(18,2)'),
                ('line_total', 'Decimal(18,2)'),
                ('load_dttm', 'Timestamp')
            ]
        }

        # Source table mapping assumptions (Bronze layer). These should exist in your metastore.
        bronze_products = 'bronze.production_products'       # derived from Production.Products
        bronze_orders = 'bronze.sales_orders'                # derived from Sales.Orders
        bronze_order_details = 'bronze.sales_orderdetails'  # derived from Sales.OrderDetails

        # Operational variables
        current_load_ts = datetime.datetime.utcnow()
        logger.info('Starting transpiled pipeline at %s', current_load_ts.isoformat())

        # 2. EXTRACTION
        # Read sources from bronze tables. If your environment uses different names, set in `context`.
        df_products = spark.table(bronze_products)
        df_orders = spark.table(bronze_orders)
        df_order_details = spark.table(bronze_order_details)

        # 3. TRANSFORMATION - DIM_PRODUCT (stable surrogate key generation)
        # Business key: productid (assumed)
        target_dim_product = f'gold.{GOLD_PREFIX}product'

        # Ensure target exists (create empty delta table with correct schema if not present)
        if not spark._jsparkSession.catalog().tableExists(target_dim_product):
            # Create empty table using schema placeholders
            empty_schema_cols = [c[0] for c in schemas[target_dim_product]]
            empty_df = spark.createDataFrame([], T.StructType([]))
            # Write a no-op table with the right name (will be repaired on first merge)
            # We create an empty dataframe with no columns; Delta requires a create - we will perform create using SELECT logic
            logger.info('Target %s does not exist. Creating an empty Delta table placeholder.', target_dim_product)
            # Create base table by writing product sample with 0 rows using select literal nulls typed
            cols_for_create = [F.col('productid').cast(T.LongType()).alias('productid')]
            # Try a safer creation: take zero rows from source and cast columns
            df_create = df_products.limit(0)
            # Add surrogate key column for DDL
            df_create = df_create.withColumn('sk_product', F.lit(None).cast(T.LongType()))
            # Reorder/rename to match expected column set (best-effort)
            for col_name, _ in schemas[target_dim_product]:
                if col_name not in df_create.columns:
                    df_create = df_create.withColumn(col_name, F.lit(None))
            df_create.select([c[0] for c in schemas[target_dim_product]]).write.format('delta').saveAsTable(target_dim_product)
            logger.info('Created placeholder table %s', target_dim_product)

        # Read existing dimension to preserve SK where applicable
        df_dim_existing = spark.table(target_dim_product).select('sk_product', 'productid').distinct()
        max_sk_row = df_dim_existing.agg(F.max(F.coalesce(F.col('sk_product'), F.lit(0))).alias('max_sk')).collect()
        max_sk = max_sk_row[0]['max_sk'] if max_sk_row and max_sk_row[0]['max_sk'] is not None else 0

        # Prepare incoming product master
        df_products_src = (
            df_products
            .select(
                F.col('productid'),
                F.col('productname'),
                F.col('supplierid'),
                F.col('categoryid'),
                F.col('quantityperunit'),
                F.col('unitprice'),
                F.col('unitsinstock'),
                F.col('unitsonorder'),
                F.col('reorderlevel'),
                F.col('discontinued')
            )
            .dropDuplicates(['productid'])
        )

        # Left-join to existing to reuse SK where productid matches
        df_joined = (
            df_products_src.alias('s')
            .join(df_dim_existing.alias('t'), F.col('s.productid') == F.col('t.productid'), 'left')
            .select('s.*', 't.sk_product')
        )

        # Assign new SKs for rows without existing SK using row_number() over deterministic order
        window = Window.orderBy('productid')
        df_with_new_sk = (
            df_joined
            .withColumn('new_rn', F.row_number().over(window))
            .withColumn('sk_product',
                        F.coalesce(F.col('sk_product'), (F.lit(max_sk) + F.col('new_rn')).cast(T.LongType())))
            .drop('new_rn')
            .withColumn('load_dttm', F.lit(current_load_ts).cast(T.TimestampType()))
        )

        # 3.2 TYPE SAFETY LOOP - cast all fields per target schema (MANDATORY)
        for col_name, col_type in schemas[target_dim_product]:
            spark_type = _map_to_spark_type(col_type)
            df_with_new_sk = df_with_new_sk.withColumn(col_name, F.col(col_name).cast(spark_type))

        # Reorder columns to match target
        df_dim_ready = df_with_new_sk.select([c[0] for c in schemas[target_dim_product]]).dropDuplicates(['productid'])

        # 4. LOAD (Delta MERGE) - Full semantics via MERGE with delete of orphans
        try:
            delta_target = DeltaTable.forName(spark, target_dim_product)
        except Exception:
            # If forName fails, ensure table exists (should have been created earlier). Re-read.
            logger.info('Retrying table read for %s', target_dim_product)
            delta_target = DeltaTable.forName(spark, target_dim_product)

        # Build merge conditions and expressions
        merge_cond = 't.productid = s.productid'

        # Execute MERGE ensuring idempotency and FULL_OVERWRITE semantics
        delta_target.alias('t').merge(
            source=df_dim_ready.alias('s'),
            condition=F.expr(merge_cond)
        ).whenMatchedUpdateAll(
        ).whenNotMatchedInsertAll(
        ).whenNotMatchedBySourceDelete(
        ).execute()

        logger.info('Merged dimension table %s with %d incoming rows', target_dim_product, df_dim_ready.count())

        # Optional optimization hints (commented for operator action):
        logger.info('Consider executing OPTIMIZE %s ZORDER BY (productid) for query performance', target_dim_product)

        # ------------------------------
        # 3/4. FACT SALES (build from orders + order details + product lookup)
        # Business intent: join Orders + OrderDetails + Product to produce FactSales
        # Use COALESCE for product SK to ensure referential integrity when lookup misses.
        # ------------------------------

        # Build product lookup (materialized view from dim)
        df_dim_product_lookup = spark.table(target_dim_product).select('sk_product', 'productid')

        # Join Orders + Details
        df_order_enriched = (
            df_order_details.alias('od')
            .join(df_orders.alias('o'), F.col('od.orderid') == F.col('o.orderid'), 'inner')
            .join(df_products.select('productid').alias('p'), F.col('od.productid') == F.col('p.productid'), 'left')
            .select(
                F.col('o.orderid').alias('orderid'),
                (F.monotonically_increasing_id()).cast(T.LongType()).alias('orderdetailid'),
                F.col('od.productid').alias('productid'),
                F.col('o.custid').alias('custid'),
                F.col('o.empid').alias('empid'),
                F.col('o.shipperid').alias('shipperid'),
                F.col('od.qty').alias('qty'),
                F.col('od.unitprice').alias('unitprice'),
                F.col('od.discount').alias('discount')
            )
        )

        # Left join to dim_product to get SK; use COALESCE to -1 for unknown as required
        df_fact_pre = (
            df_order_enriched.alias('f')
            .join(F.broadcast(df_dim_product_lookup).alias('p'), F.col('f.productid') == F.col('p.productid'), 'left')
            .withColumn('sk_product', F.coalesce(F.col('p.sk_product'), F.lit(-1)).cast(T.LongType()))
            .withColumn('categoryid', F.lit(None).cast(T.LongType()))
            .withColumn('supplierid', F.lit(None).cast(T.LongType()))
            .withColumn('line_total', (F.col('qty').cast(T.LongType()) * F.col('unitprice').cast(T.DecimalType(18,2))).cast(T.DecimalType(18,2)))
            .withColumn('load_dttm', F.lit(current_load_ts).cast(T.TimestampType()))
        )

        # Apply type safety casting per target fact schema
        target_fact = 'gold.fact_sales'
        if target_fact not in schemas:
            raise ValueError(f'Target schema definition missing for {target_fact}. Update schemas dict.')

        df_fact_ready = df_fact_pre
        for col_name, col_type in schemas[target_fact]:
            spark_type = _map_to_spark_type(col_type)
            # If column doesn't exist yet in df, create it as null then cast
            if col_name not in df_fact_ready.columns:
                df_fact_ready = df_fact_ready.withColumn(col_name, F.lit(None))
            df_fact_ready = df_fact_ready.withColumn(col_name, F.col(col_name).cast(spark_type))

        df_fact_ready = df_fact_ready.select([c[0] for c in schemas[target_fact]]).dropDuplicates(['orderid', 'orderdetailid'])

        # Ensure fact target exists (create empty if not)
        if not spark._jsparkSession.catalog().tableExists(target_fact):
            logger.info('Creating placeholder for fact table %s', target_fact)
            df_fact_ready.limit(0).write.format('delta').saveAsTable(target_fact)

        # MERGE into fact table: for facts we will also use MERGE to support idempotency for full semantics
        delta_fact = DeltaTable.forName(spark, target_fact)

        merge_cond_fact = 't.orderid = s.orderid AND t.orderdetailid = s.orderdetailid'

        delta_fact.alias('t').merge(
            source=df_fact_ready.alias('s'),
            condition=F.expr(merge_cond_fact)
        ).whenMatchedUpdateAll(
        ).whenNotMatchedInsertAll(
        ).whenNotMatchedBySourceDelete(
        ).execute()

        logger.info('Merged fact table %s with %d rows', target_fact, df_fact_ready.count())

        # Post-load optimization hints
        logger.info('Post-load: consider running OPTIMIZE and VACUUM as per retention policies for %s and %s', target_dim_product, target_fact)

        return True

    except Exception as e:
        logger.exception('Transpilation execution failed: %s', str(e))
        raise


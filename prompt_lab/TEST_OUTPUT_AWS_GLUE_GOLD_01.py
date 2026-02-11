import sys
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql import functions as F
from pyspark.sql.window import Window

args = getResolvedOptions(sys.argv, [
    'JOB_NAME', 
    'S3_BUCKET',
    'SILVER_CUSTOMERS_PATH',
    'SILVER_PRODUCTS_PATH',
    'SILVER_SALES_PATH',
    'GOLD_CUSTOMERS_PATH',
    'GOLD_PRODUCTS_PATH',
    'GOLD_FACT_SALES_PATH',
    'GOLD_DAILY_SALES_SUMMARY_PATH'
])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# PARAMETERS & PATHS
S3_SILVER_CUSTOMERS = args['SILVER_CUSTOMERS_PATH']
S3_SILVER_PRODUCTS = args['SILVER_PRODUCTS_PATH']
S3_SILVER_SALES = args['SILVER_SALES_PATH']
S3_GOLD_CUSTOMERS = args['GOLD_CUSTOMERS_PATH']
S3_GOLD_PRODUCTS = args['GOLD_PRODUCTS_PATH']
S3_GOLD_FACT_SALES = args['GOLD_FACT_SALES_PATH']
S3_GOLD_DAILY_SALES = args['GOLD_DAILY_SALES_SUMMARY_PATH']

# EXTRACTION
customers_df = spark.read.parquet(S3_SILVER_CUSTOMERS)
products_df = spark.read.parquet(S3_SILVER_PRODUCTS)
sales_df = spark.read.parquet(S3_SILVER_SALES)

# DIMENSION: CUSTOMERS
window_customer = Window.orderBy(F.col('customer_id')).rowsBetween(Window.unboundedPreceding, 0)
cust_tier_expr = F.when(F.col('total_lifetime_value') > 10000, F.lit('Gold')) \
    .when(F.col('total_lifetime_value') > 5000, F.lit('Silver')) \
    .otherwise(F.lit('Bronze'))
dim_customers_df = customers_df \
    .withColumn('customer_key', F.row_number().over(window_customer).cast('long')) \
    .withColumn('customer_tier', cust_tier_expr) \
    .withColumn('_gold_created_at', F.current_timestamp()) \
    .withColumn('_grain_level', F.lit('customer')) \
    .withColumn('_last_updated', F.current_timestamp())

# DIMENSION: PRODUCTS
window_product = Window.orderBy(F.col('product_id')).rowsBetween(Window.unboundedPreceding, 0)
dim_products_df = products_df \
    .withColumn('product_key', F.row_number().over(window_product).cast('long')) \
    .withColumn('_gold_created_at', F.current_timestamp()) \
    .withColumn('_grain_level', F.lit('product')) \
    .withColumn('_last_updated', F.current_timestamp())

# MATERIALIZE DIMENSIONS
(dim_customers_df
    .select(
        'customer_key',
        'customer_id',
        'customer_name',
        'customer_email',
        'customer_segment',
        'customer_tier',
        'country',
        '_gold_created_at',
        '_grain_level',
        '_last_updated'
    )
    .write.mode('overwrite')
    .parquet(S3_GOLD_CUSTOMERS)
)
(dim_products_df
    .select(
        'product_key',
        'product_id',
        'product_name',
        'category',
        'subcategory',
        'unit_price',
        '_gold_created_at',
        '_grain_level',
        '_last_updated'
    )
    .write.mode('overwrite')
    .parquet(S3_GOLD_PRODUCTS)
)

# FACT: SALES
sales_customers_df = sales_df.join(
    dim_customers_df.select('customer_id', 'customer_key'), 'customer_id', 'left'
)
sales_products_df = sales_customers_df.join(
    dim_products_df.select('product_id', 'product_key'), 'product_id', 'left'
)
fact_sales_df = sales_products_df \
    .withColumn('sale_amount', F.col('sale_amount').cast('decimal(18,2)')) \
    .withColumn('quantity', F.col('quantity').cast('int')) \
    .withColumn('discount', F.col('discount').cast('decimal(18,2)')) \
    .withColumn('net_amount', (F.col('sale_amount') - F.col('discount')).cast('decimal(18,2)')) \
    .withColumn('_gold_created_at', F.current_timestamp()) \
    .withColumn('_grain_level', F.lit('sale')) \
    .withColumn('_last_updated', F.current_timestamp())

# IDENTITY/PRIMARY KEY EMULATION (for Glue/Athena, create surrogate key)
window_sale = Window.orderBy(F.col('sale_id')).rowsBetween(Window.unboundedPreceding, 0)
fact_sales_df = fact_sales_df.withColumn('sale_key', F.row_number().over(window_sale).cast('long'))

# MATERIALIZE FACT TABLE
(fact_sales_df
    .select(
        'sale_key',
        'sale_id',
        'customer_key',
        'product_key',
        'sale_date',
        'sale_amount',
        'quantity',
        'discount',
        'net_amount',
        '_gold_created_at',
        '_grain_level',
        '_last_updated'
    )
    .write.mode('overwrite')
    .parquet(S3_GOLD_FACT_SALES)
)

# AGGREGATE VIEW: Daily Sales Summary
agg_df = fact_sales_df \
    .groupBy(
        'sale_date',
        'customer_key'
    ) \
    .agg(
        F.countDistinct('sale_id').alias('total_sales'),
        F.sum('sale_amount').alias('gross_sales'),
        F.sum('discount').alias('total_discounts'),
        F.sum('net_amount').alias('net_sales'),
        F.avg('net_amount').alias('avg_sale_value')
    )

# Enrich with customer segment and country for QuickSight
agg_qs_df = agg_df \
    .join(dim_customers_df.select('customer_key', 'customer_segment', 'country'), 'customer_key', 'left') \
    .withColumn('_gold_created_at', F.current_timestamp()) \
    .withColumn('_grain_level', F.lit('daily')) \
    .withColumn('_last_updated', F.current_timestamp())

(agg_qs_df
    .select(
        'sale_date',
        'customer_segment',
        'country',
        'total_sales',
        'gross_sales',
        'total_discounts',
        'net_sales',
        'avg_sale_value',
        '_gold_created_at',
        '_grain_level',
        '_last_updated'
    )
    .write.mode('overwrite')
    .partitionBy('sale_date')
    .parquet(S3_GOLD_DAILY_SALES)
)

job.commit()
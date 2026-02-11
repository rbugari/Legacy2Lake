from pyspark.sql import functions as F
from pyspark.sql.window import Window

# Parameters & Config
S3_ROOT = variables.get('S3_ROOT', 's3://your-bucket')
ENV = variables.get('ENV', 'prod')

# Extraction (Bronze/Silver Layer)
df_customer = spark.read.format('delta').load(f"{S3_ROOT}/{ENV}/silver/Unified_Customer_Profile__dll")
df_order = spark.read.format('delta').load(f"{S3_ROOT}/{ENV}/silver/Order_History__dll")

# Transformation (Gold Layer)
# Calculate lifetime value
order_agg = df_order.groupBy('CustomerId') \
    .agg(F.sum('OrderAmount').alias('lifetime_value'),
         F.count('*').alias('total_orders'),
         F.max('OrderDate').alias('last_order_date'))

# Engagement Score: weighted score based on recency and frequency
current_date = F.current_timestamp()
recency_days = F.datediff(current_date, order_agg['last_order_date'])
engagement_score = F.expr('100 - LEAST(100, recency_days) + total_orders * 2')

df_gold = df_customer.join(order_agg, df_customer['CustomerId'] == order_agg['CustomerId'], 'left') \
    .withColumn('lifetime_value', F.coalesce(order_agg['lifetime_value'], F.lit(0.0))) \
    .withColumn('engagement_score', F.coalesce(engagement_score, F.lit(0))) \
    .withColumn('churn_risk', F.when(recency_days > 180, F.lit('High'))
                                 .when(recency_days > 90, F.lit('Medium'))
                                 .otherwise(F.lit('Low'))) \
    .withColumn('segment',
                F.when(F.col('lifetime_value') > 10000, F.lit('high_value'))
                 .when((F.col('lifetime_value') < 1000) & (F.col('churn_risk') == 'High'), F.lit('dormant'))
                 .when(F.col('churn_risk') == 'High', F.lit('at_risk'))
                 .otherwise(F.lit('active'))) \
    .select(
        df_customer['CustomerId'].alias('CustomerId'),
        'lifetime_value',
        'engagement_score',
        'churn_risk',
        'segment',
        df_customer['Email'],
        df_customer['FirstName'],
        df_customer['LastName'],
        df_customer['CreatedDate']
    )
    
# Salesforce Data Cloud expects UTC timestamps
df_gold = df_gold.withColumn('CreatedDate', F.from_utc_timestamp('CreatedDate', 'UTC'))

# Load (Upsert/Merge) to Salesforce Data Cloud DLI (Gold)
# Ingestion via API or save to S3 landing for ingestion
output_path = f"{S3_ROOT}/{ENV}/gold/Customer_LTV_Segments__dli"
df_gold.write.mode('overwrite').format('delta').save(output_path)

# Optionally, trigger Salesforce Data Cloud Ingestion API (outside Spark) after delta write is complete

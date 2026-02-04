# Example: Transpiled Customer Data Load
# Original SSIS: "Data Flow Task - Load DimCustomer"

from pyspark.sql import SparkSession
import os

# This would ideally be in a shared 'config.py' or 'mounts.py'
PATHS = {
    "bronze": "/mnt/raw/source_system/customer_data",
    "silver": "/mnt/silver/sales/dim_customer"
}

def execute_load_dim_customer(spark: SparkSession, context: dict):
    """
    Transpiled by Legacy2Lake Agent C
    Target: Spark 3.5 (Databricks 15.4 LTS)
    Preference: Spark SQL for transformations
    """
    try:
        # 1. Extraction (Bridge)
        bronze_path = PATHS["bronze"]
        df_raw = spark.read.format("parquet").load(bronze_path)
        df_raw.createOrReplaceTempView("stg_customer")
        
        # 2. Transformation (Human-Readable Spark SQL)
        # Using SQL as requested for better understanding and similarity to original logic
        transformed_df = spark.sql("""
            SELECT 
                CAST(CustomerID AS INT) as customer_sk,
                UPPER(FirstName) as first_name,
                UPPER(LastName) as last_name,
                EmailAddress as email,
                CURRENT_TIMESTAMP() as load_date
            FROM stg_customer
            WHERE CustomerID IS NOT NULL
        """)
        
        # 3. Loading (Bridge)
        silver_path = PATHS["silver"]
        transformed_df.write \
            .format("delta") \
            .mode("overwrite") \
            .save(silver_path)
            
        print(f"Successfully loaded {transformed_df.count()} records to {silver_path}")
        return True
        
    except Exception as e:
        print(f"Error in Load DimCustomer: {str(e)}")
        return False

if __name__ == "__main__":
    # Local Spark test simulation
    spark = SparkSession.builder.appName("ShiftT-Test").getOrCreate()
    execute_load_dim_customer(spark, {})

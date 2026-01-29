# Medallion Architecture Configuration
import os

class Config:
    CATALOG = "main_catalog"
    
    # Schemas
    SCHEMA_BRONZE = "bronze_raw"
    SCHEMA_SILVER = "silver_curated"
    SCHEMA_GOLD = "gold_business"
    
    # Paths (if using external locations)
    PATH_BRONZE = "/mnt/datalake/bronze"
    PATH_SILVER = "/mnt/datalake/silver"
    PATH_GOLD = "/mnt/datalake/gold"
    
    @staticmethod
    def get_jdbc_url(secret_scope, secret_key):
        return dbutils.secrets.get(scope=secret_scope, key=secret_key)

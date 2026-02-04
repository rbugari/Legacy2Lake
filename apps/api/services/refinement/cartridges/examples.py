"""
Example Usage of Technology Cartridges

This module demonstrates how to use each cartridge type
for code generation in the Legacy2Lake migration platform.
"""

from pathlib import Path
from typing import Dict, Any

# Import all cartridges
from .pyspark_cartridge import PySparkCartridge
from .snowflake_cartridge import SnowflakeCartridge
from .dbt_cartridge import DbtCartridge
from .ms_fabric_cartridge import MSFabricCartridge

def example_pyspark_usage():
    """
    Example: Generate PySpark/Databricks migration code
    """
    print("=" * 60)
    print("Example 1: PySpark/Databricks Cartridge")
    print("=" * 60)
    
    # Initialize cartridge
    cartridge = PySparkCartridge(
        project_id="migration_pyspark_001",
        design_registry={
            "naming": {
                "bronze_schema": "bronze_raw",
                "silver_schema": "silver_curated",
                "gold_schema": "gold_business"
            },
            "paths": {
                "bronze_path": "/mnt/datalake/bronze",
                "silver_path": "/mnt/datalake/silver",
                "gold_path": "/mnt/datalake/gold"
            }
        }
    )
    
    # Sample table metadata
    table_metadata = {
        "source_path": "legacy/customers.py",
        "output_table_name": "dim_customer",
        "pk_columns": ["customer_id"],
        "table_type": "DIMENSION",
        "original_code": """
# Legacy PySpark code
df = spark.read.format("csv").option("header", "true").load("s3://legacy/customers.csv")
df = df.select("customer_id", "name", "email", "created_date")
"""
    }
    
    # Generate scaffolding
    print("\n1. Generating scaffolding files...")
    scaffold = cartridge.generate_scaffolding()
    for filename, content in scaffold.items():
        print(f"   - {filename} ({len(content)} bytes)")
    
    # Generate Bronze layer
    print("\n2. Generating Bronze layer code...")
    bronze_code = cartridge.generate_bronze(table_metadata)
    print(f"   Generated {len(bronze_code)} characters of Python code")
    print(f"   Preview:\n{bronze_code[:200]}...")
    
    # Generate Silver layer
    print("\n3. Generating Silver layer code...")
    silver_code = cartridge.generate_silver(table_metadata)
    print(f"   Generated {len(silver_code)} characters with MERGE logic")
    
    # Generate Gold layer
    print("\n4. Generating Gold layer code...")
    gold_code = cartridge.generate_gold(table_metadata)
    print(f"   Generated {len(gold_code)} characters for business layer")
    
    print("\n✅ PySpark cartridge example complete!\n")


def example_snowflake_usage():
    """
    Example: Generate Snowflake/Snowpark migration code
    """
    print("=" * 60)
    print("Example 2: Snowflake Cartridge")
    print("=" * 60)
    
    cartridge = SnowflakeCartridge(
        project_id="migration_snowflake_001",
        design_registry={
            "naming": {
                "bronze_schema": "BRONZE_RAW",
                "silver_schema": "SILVER_CURATED",
                "gold_schema": "GOLD_BUSINESS"
            }
        }
    )
    
    table_metadata = {
        "source_path": "legacy/orders.csv",
        "output_table_name": "FACT_ORDERS",
        "pk_columns": ["order_id", "line_number"],  # Composite PK
        "table_type": "FACT"
    }
    
    print("\n1. Generating Bronze SQL...")
    bronze_sql = cartridge.generate_bronze_sql(table_metadata)
    print(f"   Generated COPY INTO statement ({len(bronze_sql)} chars)")
    
    print("\n2. Generating Silver Snowpark code...")
    silver_code = cartridge.generate_silver(table_metadata)
    print(f"   Generated Snowpark code with composite PK MERGE")
    print(f"   PKs: {table_metadata['pk_columns']}")
    
    print("\n3. Generating orchestration (Snowflake Tasks)...")
    orchestration = cartridge.generate_orchestration([
        {"table_name": "ORDERS"},
        {"table_name": "CUSTOMERS"}
    ])
    print(f"   Generated {len(orchestration)} characters of SQL Tasks")
    
    print("\n✅ Snowflake cartridge example complete!\n")


def example_dbt_usage():
    """
    Example: Generate dbt models
    """
    print("=" * 60)
    print("Example 3: dbt Cartridge")
    print("=" * 60)
    
    cartridge = DbtCartridge(
        project_id="migration_dbt_001",
        design_registry={
            "naming": {
                "bronze_schema": "bronze",
                "silver_schema": "silver",
                "gold_schema": "gold",
                "silver_prefix": "stg_"
            }
        }
    )
    
    table_metadata = {
        "source_path": "products.sql",
        "output_table_name": "dim_product",
        "pk_columns": ["product_id"],
        "columns": [
            {"name": "product_id", "type": "integer", "nullable": False},
            {"name": "category", "type": "enum", "values": ["electronics", "clothing", "food"]},
            {"name": "price", "type": "decimal", "nullable": False}
        ]
    }
    
    print("\n1. Generating dbt_project.yml...")
    scaffold = cartridge.generate_scaffolding()
    print(f"   Generated {len(scaffold)} configuration files")
    
    print("\n2. Generating Bronze model (staging)...")
    bronze_sql = cartridge.generate_bronze(table_metadata)
    print(f"   SQL model with CTE structure")
    
    print("\n3. Generating Silver model (with tests)...")
    silver_sql = cartridge.generate_silver(table_metadata)
    print(f"   Incremental model with window function deduplication")
    print(f"   Unique key: {table_metadata['pk_columns']}")
    
    # Use test generator
    print("\n4. Generating schema tests...")
    try:
        from .dbt_test_generator import DbtTestGenerator
        tests = DbtTestGenerator.generate_schema_tests(table_metadata)
        print(f"   Generated schema.yml with not_null, unique, accepted_values tests")
    except ImportError:
        print("   (Test generator not available)")
    
    print("\n✅ dbt cartridge example complete!\n")


def example_fabric_usage():
    """
    Example: Generate Microsoft Fabric code
    """
    print("=" * 60)
    print("Example 4: MS Fabric Cartridge")
    print("=" * 60)
    
    cartridge = MSFabricCartridge(
        project_id="migration_fabric_001",
        design_registry={
            "naming": {
                "bronze_schema": "bronze",
                "silver_schema": "silver",
                "gold_schema": "gold"
            }
        }
    )
    
    table_metadata = {
        "source_path": "sales.parquet",
        "output_table_name": "FACT_SALES",
        "pk_columns": ["sale_id"],
        "table_type": "FACT"
    }
    
    print("\n1. Generating Fabric configuration...")
    scaffold = cartridge.generate_scaffolding()
    print(f"   Generated fabric_config.py and fabric_utils.py")
    
    print("\n2. Generating Bronze Notebook...")
    bronze_notebook = cartridge.generate_bronze(table_metadata)
    print(f"   PySpark notebook for Lakehouse ingestion")
    
    print("\n3. Generating Silver T-SQL...")
    silver_sql = cartridge.generate_silver_sql(table_metadata)
    print(f"   T-SQL MERGE for Fabric Warehouse")
    
    print("\n4. Generating Semantic Model (TMDL)...")
    semantic = cartridge.generate_semantic_model(table_metadata)
    print(f"   TMDL definition for Power BI")
    print(f"   Includes measure: 'Total Records'")
    
    print("\n5. Generating Pipeline orchestration...")
    pipeline = cartridge.generate_orchestration([
        {"table_name": "SALES"},
        {"table_name": "PRODUCTS"}
    ])
    print(f"   Fabric Pipeline JSON with dependencies")
    
    print("\n✅ MS Fabric cartridge example complete!\n")


def example_multi_table_processing():
    """
    Example: Process multiple tables with same cartridge
    """
    print("=" * 60)
    print("Example 5: Multi-Table Processing")
    print("=" * 60)
    
    cartridge = PySparkCartridge(
        project_id="batch_migration",
        design_registry={"naming": {}}
    )
    
    # Multiple tables
    tables = [
        {
            "source_path": "customers.py",
            "output_table_name": "dim_customer",
            "pk_columns": ["customer_id"],
            "table_type": "DIMENSION"
        },
        {
            "source_path": "orders.py",
            "output_table_name": "fact_orders",
            "pk_columns": ["order_id"],
            "table_type": "FACT"
        },
        {
            "source_path": "products.py",
            "output_table_name": "dim_product",
            "pk_columns": ["product_id"],
            "table_type": "DIMENSION"
        }
    ]
    
    print(f"\nProcessing {len(tables)} tables...")
    
    for i, table in enumerate(tables, 1):
        print(f"\n{i}. {table['output_table_name']} ({table['table_type']})")
        bronze = cartridge.generate_bronze(table)
        silver = cartridge.generate_silver(table)
        gold = cartridge.generate_gold(table)
        print(f"   ✓ Bronze: {len(bronze)} chars")
        print(f"   ✓ Silver: {len(silver)} chars")
        print(f"   ✓ Gold: {len(gold)} chars")
    
    print("\n✅ Batch processing complete!\n")


if __name__ == "__main__":
    """Run all examples"""
    print("\n" + "=" * 60)
    print("   Legacy2Lake Cartridge Examples")
    print("=" * 60 + "\n")
    
    # Run each example
    example_pyspark_usage()
    example_snowflake_usage()
    example_dbt_usage()
    example_fabric_usage()
    example_multi_table_processing()
    
    print("=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)

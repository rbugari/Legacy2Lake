"""
Quick diagnostic script to test CartridgeFactory selection logic
Sprint 0 Day 4 - Bug diagnosis
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'api'))

print("="*80)
print("🔍 CARTRIDGE FACTORY SELECTION TEST")
print("="*80)

# Test imports
print("\n1. Testing imports...")
try:
    from services.refinement.cartridges.factory import CartridgeFactory
    print("   ✅ CartridgeFactory imported")
except Exception as e:
    print(f"   ❌ Failed to import CartridgeFactory: {e}")
    sys.exit(1)

try:
    from  services.refinement.cartridges.pyspark_cartridge import PySparkCartridge
    print("   ✅ PySparkCartridge imported")
except Exception as e:
    print(f"   ❌ Failed to import PySparkCartridge: {e}")

try:
    from services.refinement.cartridges.snowflake_cartridge import SnowflakeCartridge
    print("   ✅ SnowflakeCartridge imported")
except Exception as e:
    print(f"   ❌ Failed to import SnowflakeCartridge: {e}")
    print(f"      This might be the problem!")

try:
    from services.refinement.cartridges.dbt_cartridge import DbtCartridge
    print("   ✅ DbtCartridge imported")
except Exception as e:
    print(f"   ❌ Failed to import DbtCartridge: {e}")

print("\n2. Testing CartridgeFactory.get_cartridge()...")

# Mock data
test_cases = [
    {"tech": "pyspark", "name": "PySpark"},
    {"tech": "snowflake", "name": "Snowflake"},
    {"tech": "dbt", "name": "dbt"},
    {"tech": "fabric", "name": "MS Fabric"},
    {"tech": "bigquery", "name": "GCP BigQuery"},
    {"tech": "redshift", "name": "AWS Glue"},
]

mock_registry = {}
mock_project_id = "test-project"

for test in test_cases:
    tech_id = test["tech"]
    tech_name = test["name"]
    
    print(f"\n   Testing: {tech_name} (tech_id='{tech_id}')")
    
    try:
        cartridge = CartridgeFactory.get_cartridge(
            project_id=mock_project_id,
            registry=mock_registry,
            target_tech=tech_id
        )
        
        cartridge_class = cartridge.__class__.__name__
        expected = f"{tech_name.split()[0]}Cartridge" if tech_id != "pyspark" else "PySparkCartridge"
        
        if "PySpark" in cartridge_class and tech_id != "pyspark":
            print(f"   ❌ WRONG! Got {cartridge_class}, expected {expected}")
        elif cartridge_class == "PySparkCartridge" and tech_id == "pyspark":
            print(f"   ✅ Correct: {cartridge_class}")
        else:
            print(f"   ✅ Correct: {cartridge_class}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*80)
print("🏁 DIAGNOSIS COMPLETE")
print("="*80)

"""
Check utm_system_catalog for dbt, GCP, Salesforce entries
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 80)
print("Checking utm_system_catalog for dbt, GCP, Salesforce")
print("=" * 80)

tech_ids = ["dbt", "gcp", "salesforce", "pyspark", "snowflake"]

for tech_id in tech_ids:
    print(f"\n🔍 Checking: {tech_id}")
    try:
        result = client.table("utm_system_catalog").select("*").eq("tech_id", tech_id).execute()
        
        if result.data:
            print(f"  ✅ Found {len(result.data)} entries")
            for entry in result.data:
                print(f"     - ID: {entry.get('id')}")
                print(f"     - tech_name: {entry.get('tech_name')}")
                print(f"     - category: {entry.get('category')}")
                config = entry.get('config', {})
                if config:
                    print(f"     - config keys: {list(config.keys())}")
        else:
            print(f"  ❌ NO ENTRIES FOUND")
    except Exception as e:
        print(f"  💥 ERROR: {e}")

print("\n" + "=" * 80)

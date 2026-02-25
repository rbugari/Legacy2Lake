"""
Script to check utm_table_impacts table directly
"""
import os
from supabase import create_client

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

project_id = "ec771d1a-4fe4-4499-970d-54e28de4d926"

print("=" * 80)
print("Checking utm_table_impacts table")
print("=" * 80)

# Check if table has any records for this project
response = client.table("utm_table_impacts").select("*").eq("project_id", project_id).execute()

print(f"\nTotal records found: {len(response.data)}")

if response.data:
    print("\nSample records:")
    for record in response.data[:5]:
        print(f"  - Table: {record.get('schema_name')}.{record.get('table_name')}")
        print(f"    Asset: {record.get('asset_id')}")
        print(f"    Operation: {record.get('operation')}")
        print(f"    Columns: {len(record.get('columns_affected', []))} columns")
        print()
else:
    print("\n⚠️ No records found in utm_table_impacts for this project!")
    print("\nChecking utm_objects to see available assets:")
    objects_response = client.table("utm_objects").select("object_id, source_name, type, category").eq("project_id", project_id).execute()
    print(f"\nFound {len(objects_response.data)} assets:")
    for obj in objects_response.data:
        print(f"  - {obj.get('source_name')} ({obj.get('type')}) - Category: {obj.get('category')}")

print("\n" + "=" * 80)

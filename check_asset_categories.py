"""
Check asset categories in database
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

project_id = "ec771d1a-4fe4-4499-970d-54e28de4d926"

# Get assets with category
result = client.table("utm_objects") \
    .select("object_id, source_name, category, source_tech") \
    .eq("project_id", project_id) \
    .execute()

print(f"\n{'='*80}")
print(f"Assets in project {project_id}")
print(f"{'='*80}\n")

if not result.data:
    print("❌ No assets found")
else:
    print(f"Found {len(result.data)} assets:\n")
    for asset in result.data:
        category = asset.get("category") or "NULL"
        print(f"  • {asset['source_name']}")
        print(f"    - category: {category}")
        print(f"    - source_tech: {asset.get('source_tech', 'NULL')}")
        print()

# Check utm_asset_columns
columns_result = client.table("utm_asset_columns") \
    .select("asset_id, column_name, utm_objects!asset_id(source_name, category)") \
    .eq("project_id", project_id) \
    .limit(5) \
    .execute()

print(f"\n{'='*80}")
print(f"Sample columns with asset info (first 5)")
print(f"{'='*80}\n")

if columns_result.data:
    for col in columns_result.data:
        asset_obj = col.get("utm_objects", {})
        asset_name = asset_obj.get("source_name", "Unknown") if isinstance(asset_obj, dict) else "Unknown"
        asset_category = asset_obj.get("category", "NULL") if isinstance(asset_obj, dict) else "NULL"
        print(f"  • Column: {col['column_name']}")
        print(f"    - Asset: {asset_name}")
        print(f"    - Category: {asset_category}")
        print()
else:
    print("❌ No columns found in utm_asset_columns")

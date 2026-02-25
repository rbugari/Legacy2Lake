"""
Check which assets have columns in utm_asset_columns
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

project_id = "ec771d1a-4fe4-4499-970d-54e28de4d926"

# Get all columns grouped by asset
columns_result = client.table("utm_asset_columns") \
    .select("asset_id, column_name, utm_objects!asset_id(source_name, category)") \
    .eq("project_id", project_id) \
    .execute()

# Group by asset
asset_columns = defaultdict(list)
asset_info = {}

for col in columns_result.data:
    asset_id = col['asset_id']
    asset_obj = col.get("utm_objects", {})
    asset_name = asset_obj.get("source_name", "Unknown") if isinstance(asset_obj, dict) else "Unknown"
    asset_category = asset_obj.get("category", "NULL") if isinstance(asset_obj, dict) else "NULL"
    
    asset_columns[asset_name].append(col['column_name'])
    asset_info[asset_name] = {
        'category': asset_category,
        'asset_id': asset_id
    }

print(f"\n{'='*80}")
print(f"Assets with columns in utm_asset_columns")
print(f"{'='*80}\n")

for asset_name in sorted(asset_columns.keys()):
    info = asset_info[asset_name]
    columns = asset_columns[asset_name]
    print(f"📦 {asset_name}")
    print(f"   Category: {info['category']}")
    print(f"   Columns: {len(columns)}")
    print(f"   Sample: {', '.join(columns[:5])}")
    print()

# Check SQL files specifically
print(f"\n{'='*80}")
print(f"SQL Files (category='soporte')")
print(f"{'='*80}\n")

for asset_name, info in asset_info.items():
    if info['category'] == 'soporte':
        columns = asset_columns[asset_name]
        print(f"🗃️  {asset_name}")
        print(f"   Columns: {len(columns)}")
        if len(columns) > 0:
            print(f"   All columns: {', '.join(columns)}")
        else:
            print(f"   ⚠️  NO COLUMNS FOUND")
        print()

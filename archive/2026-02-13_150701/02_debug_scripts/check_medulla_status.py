"""Check if assets have logical_medulla and test extraction"""
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

# Check project ttt
project_id = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"

print("="*70)
print("🔍 Checking assets for logical_medulla")
print("="*70)

result = supabase.table("utm_objects").select("object_id, source_name, metadata, source_connection, transformations").eq("project_id", project_id).execute()

if result.data:
    print(f"\n📦 Found {len(result.data)} assets:")
    for asset in result.data:
        name = asset.get("source_name") or "Unknown"
        metadata = asset.get("metadata") or {}
        has_medulla = "logical_medulla" in metadata
        has_connections = "connections" in metadata
        has_origin = asset.get("source_connection") is not None
        has_transforms = asset.get("transformations") is not None
        
        print(f"\n  • {name}")
        print(f"    - logical_medulla: {'✅ YES' if has_medulla else '❌ NO'}")
        print(f"    - connections: {'✅ YES' if has_connections else '❌ NO'}")
        print(f"    - source_connection (Sprint 8.5): {'✅ POPULATED' if has_origin else '⚠️  NULL'}")
        print(f"    - transformations (Sprint 8.5): {'✅ POPULATED' if has_transforms else '⚠️  NULL'}")
        
        if has_medulla:
            medulla = metadata["logical_medulla"]
            comp_count = len(medulla.get("components", []))
            print(f"    - medulla components: {comp_count}")
else:
    print("\n❌ No assets found for this project")

print("\n" + "="*70)

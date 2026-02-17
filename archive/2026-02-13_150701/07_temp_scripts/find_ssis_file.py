"""
Find where SSIS file is stored
"""
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

tenant_id = "daac0ee6-3b28-412d-8acd-43ec51149188"

print("="*70)
print("🔍 Finding SSIS Files")
print("="*70)

# Find DimCustomers.dtsx
result = supabase.table("utm_objects").select("object_id, project_id, source_name, source_path, metadata").eq("source_name", "DimCustomers.dtsx").execute()

if result.data:
    for obj in result.data:
        print(f"\n📦 Asset: {obj['source_name']}")
        print(f"   Project ID: {obj['project_id']}")
        print(f"   Object ID: {obj['object_id']}")
        print(f"   Source Path: {obj['source_path']}")
        
        metadata = obj.get('metadata', {})
        connections = metadata.get('connections', [])
        print(f"   Connections: {len(connections)}")
        
        if connections:
            for conn in connections:
                print(f"      - {conn.get('name')}: {conn.get('connection_string', '')[:60]}...")
        
        # Check if file exists
        source_path = obj['source_path']
        if source_path:
            from pathlib import Path
            file_exists = Path(source_path).exists()
            print(f"   File exists: {file_exists}")
            if file_exists:
                print(f"   ✅ Can re-parse this file")
else:
    print("\n❌ DimCustomers.dtsx not found in utm_objects")

print("\n" + "="*70)

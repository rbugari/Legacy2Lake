"""
Download SSIS file from Supabase Storage, re-parse with updated parser, and update DB
"""
import os
import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

# Import SSISCartridge
from apps.utm.cartridges.ssis.parser import SSISCartridge

project_id = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"
bucket_name = "utm-projects"

print("="*70)
print("🔄 Re-parse SSIS from Storage with Updated Parser")
print("="*70)

# Find SSIS file in DB
result = supabase.table("utm_objects").select("*").eq("project_id", project_id).eq("source_name", "DimCustomers.dtsx").single().execute()

if not result.data:
    print("\n❌ DimCustomers.dtsx not found")
    exit(1)

asset = result.data
source_path = asset['source_path']
object_id = asset['object_id']

print(f"\n📦 Asset: {asset['source_name']}")
print(f"   Storage path: {source_path}")

# Download file from Supabase Storage
print("\n⬇️  Downloading from Storage...")
try:
    data = supabase.storage.from_(bucket_name).download(source_path)
    content = data.decode('utf-8')
    print(f"   ✅ Downloaded {len(content)} bytes")
except Exception as e:
    print(f"   ❌ Error downloading: {e}")
    exit(1)

# Parse with updated SSISCartridge
print("\n🔍 Parsing with updated SSISCartridge...")
try:
    parser = SSISCartridge()
    meta_obj = parser.parse(content, name="DimCustomers.dtsx")
    
    summary = meta_obj.metadata.get("summary", {})
    connections = summary.get("connection_managers", [])
    
    print(f"\n✅ Parser results:")
    print(f"   Connections found: {len(connections)}")
    
    if connections:
        for conn in connections:
            conn_str = conn.get('connection_string', '')
            print(f"\n   📡 Connection: {conn.get('name')}")
            print(f"      ID: {conn.get('id')}")
            print(f"      String type: {type(conn_str)}")
            print(f"      String length: {len(conn_str) if isinstance(conn_str, str) else 'N/A'}")
            print(f"      First 100 chars: {str(conn_str)[:100]}...")
    else:
        print("\n   ⚠️ NO CONNECTIONS FOUND")
        print(f"   Summary keys: {list(summary.keys())}")
        print(f"   Connection_managers type: {type(summary.get('connection_managers'))}")
        print(f"   Connection_managers value: {summary.get('connection_managers')}")
    
    # Build new metadata
    medulla = {
        "data_flow_logic": meta_obj.components,
        "control_flow_topology": meta_obj.metadata.get("control_flow_topology"),
        "constraints": meta_obj.metadata.get("constraints")
    }
    
    new_metadata = asset.get('metadata', {})
    new_metadata['logical_medulla'] = medulla
    new_metadata['connections'] = connections
    
    # Update DB
    print("\n💾 Updating database...")
    supabase.table("utm_objects").update({"metadata": new_metadata}).eq("object_id", object_id).execute()
    print("   ✅ Database updated")
    
except Exception as e:
    print(f"\n❌ Parser error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "="*70)
print("✅ Re-parse complete!")
print("="*70)
print("\n💡 Now check connections with:")
print("   python check_discovery_result.py")
print("\n" + "="*70)

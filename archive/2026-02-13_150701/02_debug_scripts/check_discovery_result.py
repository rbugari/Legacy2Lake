"""
Check what Discovery extracted after reset
"""
import os
import json
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

project_id = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"

print("="*70)
print("🔍 Discovery Result After Reset")
print("="*70)

# Check assets
result = supabase.table("utm_objects").select("object_id, source_name, metadata, source_connection, source_type").eq("project_id", project_id).execute()

if not result.data:
    print("\n❌ NO ASSETS FOUND - Discovery not executed?")
    exit(1)

for asset in result.data:
    print(f"\n📦 Asset: {asset['source_name']}")
    
    metadata = asset.get("metadata", {})
    
    # Check connections in metadata
    connections = metadata.get("connections", [])
    print(f"   📡 Connections in metadata: {len(connections)}")
    
    if connections:
        for conn in connections:
            print(f"      - {conn.get('name', 'Unknown')}: {conn.get('connection_string', 'No string')[:50]}...")
    else:
        print("      ⚠️ EMPTY - Parser not extracting connections!")
    
    # Check medulla
    medulla = metadata.get("logical_medulla", {})
    data_flow = medulla.get("data_flow_logic", [])
    print(f"   🧠 Medulla data_flow_logic: {len(data_flow)} components")
    
    # Check Sprint 8.5 columns
    source_conn = asset.get("source_connection")
    source_type = asset.get("source_type")
    print(f"   📊 source_connection: {len(json.loads(source_conn)) if source_conn and source_conn != 'null' else 0} items")
    print(f"   🏷️ source_type: {source_type}")

print("\n" + "="*70)
print("❌ DIAGNOSIS: Connections array empty = Parser bug NOT fixed")
print("="*70)
print("\n💡 SOLUTION:")
print("   1. Backend needs RESTART to load updated parser.py")
print("   2. Re-run Discovery to extract connections correctly")
print("   3. Re-run Triage to populate Sprint 8.5 columns")
print("\n" + "="*70)

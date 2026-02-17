"""
Parse test SSIS file and update DB with connections
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
test_file = r"c:\proyectos_dev\UTM\test_ssis_with_connections.dtsx"

print("="*70)
print("🧪 Parse Test SSIS and Update DB")
print("="*70)

# Parse test SSIS
print(f"\n1️⃣  Parsing test SSIS: {Path(test_file).name}")
try:
    parser = SSISCartridge()
    meta_obj = parser.parse(test_file)
    
    summary = meta_obj.metadata.get("summary", {})
    connections = summary.get("connection_managers", [])
    
    print(f"\n   ✅ Parse successful!")
    print(f"   Connections found: {len(connections)}")
    
    if connections:
        for i, conn in enumerate(connections, 1):
            conn_str = conn.get('connection_string', '')
            print(f"\n   📡 Connection {i}: {conn.get('name')}")
            print(f"      ID: {conn.get('id')}")
            print(f"      String type: {type(conn_str).__name__}")
            print(f"      String length: {len(conn_str) if isinstance(conn_str, str) else 'N/A'}")
            if isinstance(conn_str, str):
                print(f"      Preview: {conn_str[:80]}...")
            else:
                print(f"      ⚠️  NOT A STRING: {conn_str}")
    else:
        print("\n   ❌ NO CONNECTIONS EXTRACTED")
        print(f"   Summary: {json.dumps(summary, indent=2)}")
        exit(1)
    
except Exception as e:
    print(f"\n   ❌ Parse error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Find DimCustomers.dtsx in DB
print(f"\n2️⃣  Finding DimCustomers.dtsx in database...")
result = supabase.table("utm_objects").select("*").eq("project_id", project_id).eq("source_name", "DimCustomers.dtsx").execute()

if not result.data:
    print("   ❌ Not found - creating new record...")
    # Create new record
    new_asset = {
        "project_id": project_id,
        "source_name": "DimCustomers.dtsx",
        "source_path": f"test/{project_id}/DimCustomers.dtsx",
        "metadata": {}
    }
    result = supabase.table("utm_objects").insert(new_asset).execute()
    asset = result.data[0]
    object_id = asset['object_id']
    print(f"   ✅ Created with ID: {object_id}")
else:
    asset = result.data[0]
    object_id = asset['object_id']
    print(f"   ✅ Found: {object_id}")

# Build medulla from parsed data
medulla = {
    "data_flow_logic": meta_obj.components,
    "control_flow_topology": meta_obj.metadata.get("control_flow_topology"),
    "constraints": meta_obj.metadata.get("constraints")
}

# Update metadata with connections
print(f"\n3️⃣  Updating metadata...")
new_metadata = asset.get('metadata', {})
new_metadata['logical_medulla'] = medulla
new_metadata['connections'] = connections

supabase.table("utm_objects").update({"metadata": new_metadata}).eq("object_id", object_id).execute()
print(f"   ✅ Metadata updated with {len(connections)} connections")

# Verify
print(f"\n4️⃣  Verifying...")
verify = supabase.table("utm_objects").select("metadata").eq("object_id", object_id).single().execute()
saved_connections = verify.data['metadata'].get('connections', [])
print(f"   ✅ Verified: {len(saved_connections)} connections in DB")

for conn in saved_connections:
    print(f"      - {conn.get('name')}")

print("\n" + "="*70)
print("✅ SUCCESS! Connections extracted and saved")
print("="*70)
print(f"\n💡 Next steps:")
print(f"   1. Run Triage to populate Sprint 8.5 columns")
print(f"   2. Check Origin tab at http://localhost:3005/workspace?project={project_id}&stage=2")
print("\n" + "="*70)

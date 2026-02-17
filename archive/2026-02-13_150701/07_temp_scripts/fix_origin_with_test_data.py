"""
Manually insert test connections into metadata to validate Origin tab works
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
print("🔧 Manually inserting test connections for validation")
print("="*70)

# Get asset
result = supabase.table("utm_objects").select("object_id, source_name, metadata").eq("project_id", project_id).eq("source_name", "DimCustomers.dtsx").single().execute()

asset = result.data
object_id = asset["object_id"]
metadata = asset.get("metadata", {})

print(f"\n📦 Asset: {asset['source_name']}")
print(f"   Current connections: {len(metadata.get('connections', []))}")

# Add test connections (simulating what parser should extract)
test_connections = [
    {
        "name": "SourceConnection",
        "id": "conn-001",
        "connection_string": "Data Source=SQL-PROD-SERVER;Initial Catalog=AdventureWorks;Provider=SQLNCLI11.1;Integrated Security=SSPI;"
    },
    {
        "name": "DestinationConnection",
        "id": "conn-002",
        "connection_string": "Data Source=DW-SQL-01;Initial Catalog=DataWarehouse_DW;Provider=SQLOLEDB;Integrated Security=SSPI;"
    }
]

metadata["connections"] = test_connections

print(f"\n✅ Adding {len(test_connections)} test connections")
for conn in test_connections:
    print(f"   - {conn['name']}: {conn['connection_string'][:60]}...")

# Update metadata
supabase.table("utm_objects").update({"metadata": metadata}).eq("object_id", object_id).execute()
print("\n💾 Updated metadata in DB")

# Now re-run origin extraction
print("\n🔄 Running origin extraction with new connections...")

import sys
import asyncio
sys.path.insert(0, os.path.dirname(__file__))

# Import extraction functions
from apps.api.routers.triage import (
    _extract_origin_from_medulla,
    _calculate_complexity
)

async def extract_and_persist():
    medulla = metadata.get("logical_medulla", {})
    connections = test_connections
    
    # Extract origin
    from apps.api.routers.triage import _extract_origin_from_medulla, _extract_transformations_from_medulla, _extract_queries_from_medulla
    origin = await _extract_origin_from_medulla(medulla, connections)
    transformations = await _extract_transformations_from_medulla(medulla)
    queries =await _extract_queries_from_medulla(medulla)
    
    from apps.api.routers.triage import _calculate_complexity
    complexity = _calculate_complexity(transformations)
    
    print(f"\n✅ Origin extracted:")
    print(f"   - Source Type: {origin['source_type']}")
    print(f"   - Server: {origin['server']}")
    print(f"   - Database: {origin['database']}")
    print(f"   - Connections: {len(origin['connections'])}")
    
    # Persist
    updates = {
        "source_connection": json.dumps(origin.get("connections", [])),
        "source_type": origin.get("source_type"),
        "source_query": queries[0].get("query") if queries else None,
        "transformations": json.dumps(transformations),
        "complexity_score": complexity,
        "data_flow_analysis": json.dumps({
            "origin": origin,
            "queries": queries,
            "transformations_count": len(transformations)
        })
    }
    
    supabase.table("utm_objects").update(updates).eq("object_id", object_id).execute()
    print("\n💾 Persisted to utm_objects")
    
    return origin

origin = asyncio.run(extract_and_persist())

print("\n" + "="*70)
print("✅ Complete! Now test in UI:")
print("="*70)
print(f"\n📍 Go to: http://localhost:3005/workspace?project={project_id}&stage=2")
print("\n🔍 Click 'Origin' tab → Should show:")
print(f"   • Server: {origin['server']}")
print(f"   • Database: {origin['database']}")
print(f"   • {len(origin['connections'])} connections")
print("\n" + "="*70)

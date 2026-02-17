"""
Run Triage extraction logic directly (bypass API)
"""
import os
import sys
from pathlib import Path
import json
import re

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

project_id = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"

# Sprint 8.5 extraction functions (inline - from triage.py lines 21-140)
def _parse_connection_string(conn_string):
    parsed = {"type": "OLEDB", "server": None, "database": None}
    
    if "ODBC" in conn_string.upper():
        parsed["type"] = "ODBC"
    
    server_match = re.search(r'Data Source=([^;]+)', conn_string, re.IGNORECASE)
    if server_match:
        parsed["server"] = server_match.group(1).strip()
    
    db_match = re.search(r'Initial Catalog=([^;]+)', conn_string, re.IGNORECASE)
    if db_match:
        parsed["database"] = db_match.group(1).strip()
    
    return parsed

def _extract_origin_from_medulla(metadata):
    connections = metadata.get("connections", [])
    medulla = metadata.get("logical_medulla", {})
    
    origin_connections = []
    for conn in connections:
        if conn.get("connection_string"):
            parsed = _parse_connection_string(conn["connection_string"])
            origin_connections.append({
                "name": conn.get("name"),
                "id": conn.get("id"),
                "type": parsed["type"],
                "server": parsed["server"],
                "database": parsed["database"]
            })
    
    # Extract server/database from first connection
    server = None
    database = None
    source_type = None
    
    if origin_connections:
        first_conn = origin_connections[0]
        server = first_conn["server"]
        database = first_conn["database"]
        source_type = f"SQL Server ({first_conn['type']})"
    
    return {
        "source_type": source_type,
        "server": server,
        "database": database,
        "connections": origin_connections
    }

def _extract_queries_from_medulla(medulla):
    queries = []
    for comp in medulla.get("data_flow_logic", []):
        sql = comp.get("raw_properties", {}).get("SqlCommand", "")
        if sql and sql.strip():
            queries.append({
                "component_type": comp.get("type"),
                "component_name": comp.get("name"),
                "query": sql
            })
    return queries

print("="*70)
print("🚀 Running Triage Extraction Logic")
print("="*70)

# Get asset with connections
result = supabase.table("utm_objects").select("*").eq("project_id", project_id).eq("source_name", "DimCustomers.dtsx").single().execute()

if not result.data:
    print("\n❌ Asset not found")
    exit(1)

asset = result.data
object_id = asset['object_id']
metadata = asset.get('metadata', {})

print(f"\n📦 Asset: {asset['source_name']}")
print(f"   Object ID: {object_id}")

# Extract origin
print(f"\n1️⃣  Extracting origin...")
origin_analysis = _extract_origin_from_medulla(metadata)
print(f"   ✅ Origin extracted:")
print(f"      Server: {origin_analysis['server']}")
print(f"      Database: {origin_analysis['database']}")
print(f"      Connections: {len(origin_analysis['connections'])}")

# Extract queries
print(f"\n2️⃣  Extracting queries...")
medulla = metadata.get("logical_medulla", {})
queries = _extract_queries_from_medulla(medulla)
print(f"   ✅ Queries extracted: {len(queries)}")

# Build data_flow_analysis
data_flow_analysis = {
    "origin": origin_analysis,
    "queries": queries,
    "transformations_count": 0
}

# Persist to Sprint 8.5 columns
print(f"\n3️⃣  Persisting to Sprint 8.5 columns...")
updates = {
    "source_connection": json.dumps(origin_analysis["connections"]),
    "source_type": origin_analysis["source_type"],
    "source_query": queries[0]["query"] if queries else None,
    "data_flow_analysis": json.dumps(data_flow_analysis)
}

supabase.table("utm_objects").update(updates).eq("object_id", object_id).execute()
print(f"   ✅ Persisted successfully")

print("\n" + "="*70)
print("✅ Triage extraction complete!")
print("="*70)
print(f"\n💡 Now test endpoints:")
print(f"   Invoke-RestMethod -Uri 'http://localhost:8085/projects/{project_id}/origin-analysis'")
print(f"   Invoke-RestMethod -Uri 'http://localhost:8085/projects/{project_id}/source-queries'")
print("\n" + "="*70)

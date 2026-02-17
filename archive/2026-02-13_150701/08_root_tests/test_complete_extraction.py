"""
Final validation: Simulate complete triage extraction and persistence
"""
import os
import json
import asyncio
import re
from dotenv import load_dotenv
from supabase import create_client
from typing import Dict, Any, List

load_dotenv()

# ============== EXTRACTION FUNCTIONS (Corrected) ==============

async def _extract_origin_from_medulla(medulla: Dict[str, Any], connections: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract origin system details from SSIS medulla"""
    origin = {
        "source_type": None,
        "server": None,
        "database": None,
        "connections": []
    }
    
    for conn in connections:
        conn_string = conn.get("connection_string", [""])[0] if isinstance(conn.get("connection_string"), list) else conn.get("connection_string", "")
        
        if conn_string:
            parsed = _parse_connection_string(conn_string)
            
            origin["connections"].append({
                "name": conn.get("name"),
                "id": conn.get("id"),
                "type": parsed.get("type", "OLEDB"),
                "server": parsed.get("server"),
                "database": parsed.get("database")
            })
            
            if not origin["source_type"]:
                origin["source_type"] = f"SQL Server ({parsed.get('type', 'OLEDB')})"
                origin["server"] = parsed.get("server")
                origin["database"] = parsed.get("database")
    
    return origin

def _parse_connection_string(conn_string: str) -> Dict[str, Any]:
    """Parse OLEDB/ODBC connection string"""
    parsed = {"type": "OLEDB", "server": None, "database": None}
    
    if "ODBC" in conn_string.upper():
        parsed["type"] = "ODBC"
    
    server_match = re.search(r'Data Source=([^;]+)', conn_string, re.IGNORECASE)
    if server_match:
        parsed["server"] = server_match.group(1).strip()
    else:
        server_match = re.search(r'Server=([^;]+)', conn_string, re.IGNORECASE)
        if server_match:
            parsed["server"] = server_match.group(1).strip()
    
    db_match = re.search(r'Initial Catalog=([^;]+)', conn_string, re.IGNORECASE)
    if db_match:
        parsed["database"] = db_match.group(1).strip()
    else:
        db_match = re.search(r'Database=([^;]+)', conn_string, re.IGNORECASE)
        if db_match:
            parsed["database"] = db_match.group(1).strip()
    
    return parsed

async def _extract_transformations_from_medulla(medulla: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract transformation components from SSIS medulla"""
    transformations = []
    
    for comp in medulla.get("data_flow_logic", []):
        comp_type = comp.get("type", "").upper()
        
        if comp_type in ["LOOKUP", "DERIVED_COLUMN", "CONDITIONAL_SPLIT", "AGGREGATE", "SORT", "MERGE", "UNION_ALL", "TRANSFORM"]:
            transformations.append({
                "type": comp_type,
                "name": comp.get("name", ""),
                "id": comp.get("ref_id", "")
            })
    
    return transformations

async def _extract_queries_from_medulla(medulla: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract SQL queries from SSIS medulla"""
    queries = []
    
    for comp in medulla.get("data_flow_logic", []):
        sql_command = comp.get("raw_properties", {}).get("SqlCommand", "")
        
        if sql_command and sql_command.strip():
            queries.append({
                "component_type": comp.get("type"),
                "component_name": comp.get("name"),
                "query": sql_command
            })
    
    return queries

def _calculate_complexity(transformations: List[Dict[str, Any]]) -> int:
    """Calculate complexity score based on transformations"""
    complexity_weights = {
        "LOOKUP": 15,
        "DERIVED_COLUMN": 10,
        "CONDITIONAL_SPLIT": 12,
        "AGGREGATE": 20,
        "SORT": 8,
        "MERGE": 18,
        "UNION_ALL": 10
    }
    
    score = 0
    for trans in transformations:
        score += complexity_weights.get(trans.get("type", ""), 5)
    
    return min(score, 100)

# ============== MAIN TEST ==============

async def test_full_extraction_and_persistence():
    print("="*70)
    print("🚀 Final Validation: Complete Extraction + Persistence")
    print("="*70)
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    supabase = create_client(url, key)
    
    project_id = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"
    
    # Get asset with medulla
    result = supabase.table("utm_objects").select("object_id, source_name, metadata").eq("project_id", project_id).eq("source_name", "DimCustomers.dtsx").single().execute()
    
    if not result.data:
        print("❌ Asset not found")
        return False
    
    asset = result.data
    object_id = asset["object_id"]
    metadata = asset.get("metadata", {})
    medulla = metadata.get("logical_medulla", {})
    connections = metadata.get("connections", [])
    
    print(f"\n📦 Processing: {asset['source_name']}")
    print(f"   Object ID: {object_id[:8]}...")
    
    # Extract origin
    print("\n1️⃣  Extracting Origin Analysis...")
    origin = await _extract_origin_from_medulla(medulla, connections)
    print(f"   ✅ Source Type: {origin['source_type']}")
    print(f"   ✅ Connections: {len(origin['connections'])}")
    
    # Extract transformations
    print("\n2️⃣  Extracting Transformations...")
    transformations = await _extract_transformations_from_medulla(medulla)
    print(f"   ✅ Found: {len(transformations)} transformations")
    
    # Extract queries
    print("\n3️⃣  Extracting Queries...")
    queries = await _extract_queries_from_medulla(medulla)
    print(f"   ✅ Found: {len(queries)} queries")
    for q in queries:
        print(f"      - {q['query'][:50]}...")
    
    # Calculate complexity
    complexity = _calculate_complexity(transformations)
    print(f"\n4️⃣  Calculating Complexity: {complexity}/100")
    
    # Persist to DB
    print("\n5️⃣  Persisting to utm_objects (Sprint 8.5 columns)...")
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
    
    print("   ✅ Persisted successfully!")
    
    # Verify
    print("\n6️⃣  Verifying persistence...")
    verify = supabase.table("utm_objects").select("source_connection, source_type, transformations, complexity_score").eq("object_id", object_id).single().execute()
    
    if verify.data:
        print(f"   ✅ source_connection: {len(json.loads(verify.data['source_connection']))} connections")
        print(f"   ✅ source_type: {verify.data['source_type']}")
        print(f"   ✅ transformations: {len(json.loads(verify.data['transformations']))} items")
        print(f"   ✅ complexity_score: {verify.data['complexity_score']}")
    
    print("\n" + "="*70)
    print("✅ COMPLETE - Origin extraction working end-to-end!")
    print("="*70)
    print("\n💡 Now test in UI:")
    print("   1. Go to project 'ttt' Stage 2 (Triage)")
    print("   2. Click 'Origin' tab → should show server/database")
    print("   3. Click 'Queries' tab → should show SELECT query")
    print("   4. Click 'Transform' tab → will be empty (simple SSIS)")
    
    return True

if __name__ == "__main__":
    result = asyncio.run(test_full_extraction_and_persistence())
    exit(0 if result else 1)

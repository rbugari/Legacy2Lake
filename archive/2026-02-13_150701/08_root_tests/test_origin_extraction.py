"""
Test Origin Extraction Logic in Triage
Validates that Sprint 8.5 data gets extracted during triage phase
"""
import asyncio
import json
import re
from typing import Dict, Any, List

# Copy the extraction functions directly (standalone test)

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
    
    for comp in medulla.get("components", []):
        comp_type = comp.get("component_type", "").upper()
        
        if comp_type in ["LOOKUP", "DERIVED_COLUMN", "CONDITIONAL_SPLIT", "AGGREGATE", "SORT", "MERGE", "UNION_ALL"]:
            transformations.append({
                "type": comp_type,
                "name": comp.get("name", ""),
                "id": comp.get("refId", "")
            })
    
    return transformations

async def _extract_queries_from_medulla(medulla: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract SQL queries from SSIS medulla"""
    queries = []
    
    for comp in medulla.get("components", []):
        sql_command = comp.get("properties", {}).get("SqlCommand")
        
        if sql_command:
            queries.append({
                "component_type": comp.get("component_type"),
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
    
    return min(score, 100)  # Cap at 100

# Mock SSIS medulla data (típico de Discovery)
MOCK_MEDULLA = {
    "components": [
        {
            "refId": "Package\\Data Flow Task\\OLE DB Source",
            "name": "OLE DB Source - DimCustomer",
            "component_type": "OLEDB_SOURCE",
            "properties": {
                "SqlCommand": "SELECT CustomerID, Name, City FROM DimCustomer WHERE IsActive = 1"
            }
        },
        {
            "refId": "Package\\Data Flow Task\\Lookup",
            "name": "Lookup - Geography",
            "component_type": "LOOKUP"
        },
        {
            "refId": "Package\\Data Flow Task\\Derived Column",
            "name": "Calculate Full Name",
            "component_type": "DERIVED_COLUMN"
        },
        {
            "refId": "Package\\Data Flow Task\\Conditional Split",
            "name": "Split By Region",
            "component_type": "CONDITIONAL_SPLIT"
        }
    ]
}

MOCK_CONNECTIONS = [
    {
        "name": "SourceDB",
        "id": "conn-001",
        "connection_string": "Data Source=SQL-PROD-01;Initial Catalog=AdventureWorks;Provider=SQLNCLI11.1;Integrated Security=SSPI;"
    },
    {
        "name": "DestDB",
        "id": "conn-002",
        "connection_string": "Server=DW-SERVER;Database=DataWarehouse;Provider=SQLOLEDB;Integrated Security=SSPI;"
    }
]

async def test_origin_extraction():
    print("="*60)
    print("🧪 Testing Origin Extraction Logic (Sprint 8.5)")
    print("="*60)
    
    # Test 1: Extract Origin
    print("\n1️⃣  Testing _extract_origin_from_medulla()...")
    origin = await _extract_origin_from_medulla(MOCK_MEDULLA, MOCK_CONNECTIONS)
    
    print(f"   ✅ Source Type: {origin['source_type']}")
    print(f"   ✅ Server: {origin['server']}")
    print(f"   ✅ Database: {origin['database']}")
    print(f"   ✅ Connections: {len(origin['connections'])} found")
    
    for conn in origin['connections']:
        print(f"      - {conn['name']}: {conn['server']} / {conn['database']}")
    
    assert origin['source_type'] is not None, "❌ source_type is None"
    assert origin['server'] == "SQL-PROD-01", f"❌ Expected SQL-PROD-01, got {origin['server']}"
    assert origin['database'] == "AdventureWorks", f"❌ Expected AdventureWorks, got {origin['database']}"
    
    # Test 2: Extract Transformations
    print("\n2️⃣  Testing _extract_transformations_from_medulla()...")
    transformations = await _extract_transformations_from_medulla(MOCK_MEDULLA)
    
    print(f"   ✅ Total Transformations: {len(transformations)}")
    for trans in transformations:
        print(f"      - {trans['type']}: {trans['name']}")
    
    assert len(transformations) == 3, f"❌ Expected 3 transformations, got {len(transformations)}"
    assert transformations[0]['type'] == "LOOKUP", "❌ First transformation should be LOOKUP"
    
    # Test 3: Extract Queries
    print("\n3️⃣  Testing _extract_queries_from_medulla()...")
    queries = await _extract_queries_from_medulla(MOCK_MEDULLA)
    
    print(f"   ✅ Total Queries: {len(queries)}")
    for query in queries:
        print(f"      - {query['component_type']}: {query['query'][:50]}...")
    
    assert len(queries) == 1, f"❌ Expected 1 query, got {len(queries)}"
    assert "SELECT CustomerID" in queries[0]['query'], "❌ Query content incorrect"
    
    # Test 4: Calculate Complexity
    print("\n4️⃣  Testing _calculate_complexity()...")
    complexity = _calculate_complexity(transformations)
    
    print(f"   ✅ Complexity Score: {complexity}/100")
    print(f"      - LOOKUP: 15 points")
    print(f"      - DERIVED_COLUMN: 10 points")
    print(f"      - CONDITIONAL_SPLIT: 12 points")
    print(f"      = Total: {complexity} points")
    
    assert complexity == 37, f"❌ Expected 37, got {complexity}"
    
    # Final Validation
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED - Origin extraction logic works!")
    print("="*60)
    print("\n📋 Summary:")
    print(f"   • Origin: {origin['server']} / {origin['database']}")
    print(f"   • Transformations: {len(transformations)} components")
    print(f"   • Queries: {len(queries)} SQL statements")
    print(f"   • Complexity: {complexity}/100")
    print("\n💡 Next: Run real triage to persist this data to utm_objects")
    
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(test_origin_extraction())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

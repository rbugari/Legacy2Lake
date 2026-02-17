"""
Test Sprint 8.5: Origin Analysis Implementation
Valida que el an\u00e1lisis de origen SSIS se extraiga y persista correctamente
"""
import asyncio
import json
from apps.api.services.agent_c_service import AgentCService

# Sample medulla data (from SSISCartridge)
SAMPLE_MEDULLA = {
    "data_flow_logic": [
        {
            "type": "SOURCE_DB",
            "name": "OLE DB Source - Customers",
            "raw_properties": {
                "SqlCommand": "SELECT custid, contactname, city, country, address, phone, postalcode FROM dbo.Customers WHERE active = 1"
            }
        },
        {
            "type": "LOOKUP",
            "name": "Lookup - Countries",
            "raw_properties": {
                "SqlCommand": "SELECT country_code, country_name FROM dbo.Countries"
            }
        },
        {
            "type": "DERIVED_COLUMN",
            "name": "Add LoadDate",
            "raw_properties": {}
        },
        {
            "type": "CONDITIONAL",
            "name": "Filter Active Customers",
            "raw_properties": {}
        },
        {
            "type": "DESTINATION_DB",
            "name": "OLE DB Destination - DimCustomers",
            "raw_properties": {
                "TableOrViewName": "dbo.DimCustomers"
            }
        }
    ]
}

SAMPLE_CONNECTIONS = [
    {
        "name": "OLEDB_SourceConnection",
        "id": "{ABC-123-DEF}",
        "connection_string": "Data Source=SERVER01;Initial Catalog=Northwind;Provider=SQLNCLI11.1;Integrated Security=SSPI;"
    },
    {
        "name": "OLEDB_DestConnection",
        "id": "{XYZ-789-GHI}",
        "connection_string": "Data Source=DW01;Initial Catalog=DataWarehouse;Provider=SQLNCLI11.1;Integrated Security=SSPI;"
    }
]

async def test_origin_analysis():
    """Test origin analysis extraction"""
    print("\n" + "="*70)
    print("TEST: ORIGIN ANALYSIS EXTRACTION")
    print("="*70)
    
    agent_c = AgentCService()
    
    # Test 1: Extract origin analysis
    print("\n1️⃣  Testing _extract_origin_analysis()...")
    origin = await agent_c._extract_origin_analysis(SAMPLE_MEDULLA, SAMPLE_CONNECTIONS)
    
    print(f"\n✅ Origin Analysis:")
    print(json.dumps(origin, indent=2))
    
    assert origin["source_type"] == "SQL Server (OLEDB)", "❌ Source type incorrect"
    assert origin["server"] == "SERVER01", "❌ Server incorrect"
    assert origin["database"] == "Northwind", "❌ Database incorrect"
    assert len(origin["connections"]) == 2, "❌ Connections count incorrect"
    print("\n✅ Origin analysis passed!")
    
    # Test 2: Extract transformations
    print("\n2️⃣  Testing _extract_transformations()...")
    transformations = await agent_c._extract_transformations(SAMPLE_MEDULLA)
    
    print(f"\n✅ Transformations ({len(transformations)}):")
    for t in transformations:
        print(f"   - {t['type']}: {t['name']} (complexity factor: {t['complexity_factor']})")
    
    assert len(transformations) == 5, "❌ Transformations count incorrect"
    assert transformations[1]["type"] == "LOOKUP", "❌ LOOKUP not found"
    print("\n✅ Transformations extraction passed!")
    
    # Test 3: Extract source queries
    print("\n3️⃣  Testing _extract_source_queries()...")
    queries = await agent_c._extract_source_queries(SAMPLE_MEDULLA)
    
    print(f"\n✅ Source Queries ({len(queries)}):")
    for q in queries:
        print(f"   [{q['component_type']}] {q['component_name']}")
        print(f"   Query: {q['query'][:80]}...")
    
    assert len(queries) == 2, f"❌ Expected 2 queries, got {len(queries)}"
    assert queries[0]["component_type"] == "SOURCE_DB", "❌ First query should be SOURCE_DB"
    assert queries[1]["component_type"] == "LOOKUP", "❌ Second query should be LOOKUP"
    print("\n✅ Source queries extraction passed!")
    
    # Test 4: Calculate complexity score
    print("\n4️⃣  Testing _calculate_complexity_score()...")
    score = await agent_c._calculate_complexity_score(transformations)
    
    print(f"\n✅ Complexity Score: {score}/100")
    print(f"   Breakdown:")
    print(f"   - Total transformations: {len(transformations)}")
    print(f"   - Total complexity factors: {sum(t['complexity_factor'] for t in transformations)}")
    print(f"   - Average: {sum(t['complexity_factor'] for t in transformations) / len(transformations):.1f}")
    
    assert 0 <= score <= 100, "❌ Score out of range"
    assert score > 0, "❌ Score should be > 0 with transformations"
    print(f"\n✅ Complexity calculation passed! Score: {score}")
    
    # Test 5: Parse connection string
    print("\n5️⃣  Testing _parse_connection_string()...")
    conn_str = "Data Source=SERVER01;Initial Catalog=Northwind;Provider=SQLNCLI11.1;Integrated Security=SSPI;"
    parsed = agent_c._parse_connection_string(conn_str)
    
    print(f"\n✅ Parsed Connection String:")
    print(json.dumps(parsed, indent=2))
    
    assert parsed["server"] == "SERVER01", "❌ Server parsing failed"
    assert parsed["database"] == "Northwind", "❌ Database parsing failed"
    assert parsed["type"] == "OLEDB", "❌ Type detection failed"
    print("\n✅ Connection string parsing passed!")
    
    print("\n" + "="*70)
    print("🎉 ALL TESTS PASSED!")
    print("="*70)
    
    # Summary
    print(f"\n📊 SUMMARY:")
    print(f"   • Origin: {origin['source_type']} on {origin['server']}")
    print(f"   • Transformations: {len(transformations)}")
    print(f"   • Source Queries: {len(queries)}")
    print(f"   • Complexity Score: {score}/100")
    print(f"   • Connections: {len(origin['connections'])}")
    
    return {
        "origin": origin,
        "transformations": transformations,
        "queries": queries,
        "score": score
    }

if __name__ == "__main__":
    result = asyncio.run(test_origin_analysis())
    print("\n✅ Test completed successfully!")

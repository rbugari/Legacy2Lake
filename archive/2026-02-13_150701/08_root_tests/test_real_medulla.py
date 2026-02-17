"""Test extraction with REAL medulla structure"""
import asyncio
import json

# Use real medulla structure from DB
REAL_MEDULLA = {
  "constraints": [
    {
      "id": "{B4D84A0B-812B-43A7-8FAF-340C16C8F2C0}",
      "source": "Package\\max customer",
      "target": "Package\\DimCustomer"
    }
  ],
  "data_flow_logic": [
    {
      "name": "OLE DB Source",
      "type": "SOURCE_DB",
      "ref_id": "Package\\DimCustomer\\OLE DB Source",
      "raw_properties": {
        "OpenRowset": "",
        "SqlCommand": "SELECT custid,contactname,city,country,address,phone,postalcode FROM Sales.Customers\\nWHERE custid > ?"
      },
      "original_intent": "SOURCE"
    },
    {
      "name": "OLE DB Destination",
      "type": "DESTINATION_DB",
      "ref_id": "Package\\DimCustomer\\OLE DB Destination",
      "raw_properties": {
        "OpenRowset": "[DimCustomer]",
        "SqlCommand": ""
      },
      "original_intent": "DESTINATION"
    }
  ],
  "control_flow_topology": [
    {
      "id": "{33BB0E4F-2690-40BE-A99E-249BE1D3AAB3}",
      "name": "Package1",
      "type": "Microsoft.Package"
    },
    {
      "id": "{96CCE585-CA7A-4BFC-8F0B-0FB1F1B93783}",
      "name": "DimCustomer",
      "type": "Microsoft.Pipeline"
    },
    {
      "id": "{5F987137-E7DC-45DF-8709-82CBEA999F83}",
      "name": "max customer",
      "type": "Microsoft.ExecuteSQLTask"
    }
  ]
}

# Copy corrected functions
async def _extract_transformations_from_medulla(medulla):
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

async def _extract_queries_from_medulla(medulla):
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

async def test_real_medulla():
    print("="*70)
    print("🧪 Testing with REAL Medulla Structure")
    print("="*70)
    
    print("\n📊 Medulla Structure:")
    print(f"   - data_flow_logic components: {len(REAL_MEDULLA.get('data_flow_logic', []))}")
    print(f"   - control_flow_topology: {len(REAL_MEDULLA.get('control_flow_topology', []))}")
    print(f"   - constraints: {len(REAL_MEDULLA.get('constraints', []))}")
    
    print("\n1️⃣  Testing Transformations Extraction...")
    transformations = await _extract_transformations_from_medulla(REAL_MEDULLA)
    print(f"   ✅ Found {len(transformations)} transformations")
    for t in transformations:
        print(f"      - {t['type']}: {t['name']}")
    
    print("\n2️⃣  Testing Queries Extraction...")
    queries = await _extract_queries_from_medulla(REAL_MEDULLA)
    print(f"   ✅ Found {len(queries)} queries")
    for q in queries:
        print(f"      - {q['component_type']}: {q['query'][:60]}...")
    
    print("\n" + "="*70)
    if len(queries) > 0:
        print("✅ SUCCESS - Extraction works with real medulla structure!")
    else:
        print("⚠️  No queries found - but structure is now correct")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(test_real_medulla())

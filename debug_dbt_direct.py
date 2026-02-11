"""
Debug dbt cartridge Body=None error by running transpile directly
"""
import asyncio
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Set up environment
TENANT_ID = "daac0ee6-3b28-412d-8acd-43ec51149188"
PROJECT_ID = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"

async def test_dbt_transpile():
    # Import after environment is set
    from apps.api.services.agent_c_service import AgentCService
    
    # Read dbt prompt
    with open("prompt_lab/cartridges/dbt/bronze_layer.md", 'r', encoding='utf-8') as f:
        bronze_prompt = f.read()
    
    print(f"✅ Loaded dbt Bronze prompt: {len(bronze_prompt)} chars")
    
    node_data = {
        "name": "dbt_source_customers",
        "label": "dbt - Source Definition Customers",
        "description": "Define dbt source for raw customers table with freshness checks",
        "type": "source",
        "layer": "bronze",
        "tech_id": "dbt",
        "source_schema": "raw_data",
        "source_table": "customers",
        "freshness": "24 hours",
        "cartridge_prompt": bronze_prompt,
        "project_id": PROJECT_ID
    }
    
    context = {
        "project_id": PROJECT_ID,
        "solution_name": "ttt_migration",
        "source_tech": "PostgreSQL",
        "target_tech": "dbt Core"
    }
    
    print("\n📤 Creating AgentCService...")
    try:
        service = AgentCService(tenant_id=TENANT_ID)
        print("✅ Service created")
        
        print("\n📤 Calling transpile_task...")
        result = await service.transpile_task(node_data=node_data, context=context)
        
        print("\n✅ SUCCESS!")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_dbt_transpile())

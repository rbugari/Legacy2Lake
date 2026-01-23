import asyncio
import os
import sys
import json

# Add project root and apps/api to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "apps", "api"))

from dotenv import load_dotenv
load_dotenv(".env")

from apps.api.services.agent_c_service import AgentCService

async def test_dual_mode():
    agent = AgentCService()
    
    project_id = "c522d48a-0329-4264-85ac-58bd0c8c316c" # base
    
    task_def = {
        "project_id": project_id,
        "name": "DimCategory.dtsx",
        "type": "Data Flow",
        "description": "Load categories from SQL Server to Delta Lake",
        "load_strategy": "FULL_OVERWRITE",
        "package_name": "DimCategory.dtsx",
        "inputs": ["Production.Categories"],
        "outputs": ["DimCategory"],
        "lookups": []
    }
    
    print("Testing Agent C in DUAL MODE...")
    result = await agent.transpile_task(task_def)
    
    print("\nKeys in result:", list(result.keys()))
    if "sql_code" in result:
        print("\n--- SQL CODE DETECTED ---")
        print(result["sql_code"][:200] + "...")
    else:
        print("\n--- NO SQL CODE DETECTED ---")
        
    if "pyspark_code" in result:
        print("\n--- PYSPARK CODE DETECTED ---")
        print(result["pyspark_code"][:200] + "...")

if __name__ == "__main__":
    asyncio.run(test_dual_mode())

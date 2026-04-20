import asyncio
import os
import sys
import pytest
from dotenv import load_dotenv

# Add apps/api to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "apps", "api"))

from services.ssis_parser import SSISParser
from services.agent_a_service import AgentAService

@pytest.mark.integration
async def test_discovery():
    load_dotenv()
    
    # Path to sample DTSX
    sample_file = r"c:\proyectos_dev\ShifT\tests\fixtures\ssis_test_repo\Building Sales Data Mart Using ETL\ETL_Dim_Customer.dtsx"
    
    if not os.path.exists(sample_file):
        print(f"File not found: {sample_file}")
        return

    print(f"--- Processing: {os.path.basename(sample_file)} ---")
    
    with open(sample_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 1. Parse XML
    parser = SSISParser(content)
    summary = parser.get_summary()
    summary["executables"] = parser.extract_executables()
    
    print("\n[Parser Summary]:")
    print(summary)
    
    # 2. Agent A Analysis
    agent_a = AgentAService()
    print("\n[Agent A (Detective) is investigating...]")
    report = await agent_a.analyze_package(summary)
    
    print("\n[Detective Report]:")
    import json
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    asyncio.run(test_discovery())

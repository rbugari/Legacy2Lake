"""
Test SQL DDL Parser
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

# Set test environment
os.environ["RUNNING_IN_TEST"] = "1"

from apps.api.services.sql_ddl_parser_service import SQLDDLParserService

async def main():
    tenant_id = "daac0ee6-e94a-48cd-8464-ad3cf08ed69e"
    project_id = "ec771d1a-4fe4-4499-970d-54e28de4d926"
    
    parser = SQLDDLParserService(tenant_id=tenant_id)
    
    print("\n" + "="*80)
    print("Parsing SQL DDL files in project...")
    print("="*80 + "\n")
    
    result = await parser.parse_sql_assets_in_project(project_id)
    
    print(f"\nResults:")
    print(f"   Assets parsed: {result['assets_parsed']}")
    print(f"   Tables found: {result['total_tables']}")
    print(f"   Columns saved: {result['total_columns']}")
    
    print(f"\nDetails:")
    for asset in result['assets']:
        print(f"\n   {asset['asset_name']}")
        print(f"      - Tables: {asset['tables_parsed']}")
        print(f"      - Columns: {asset['columns_saved']}")
        print(f"      - Table names: {', '.join(asset['tables'][:5])}")
        if len(asset['tables']) > 5:
            print(f"                     ... and {len(asset['tables']) - 5} more")

if __name__ == "__main__":
    asyncio.run(main())

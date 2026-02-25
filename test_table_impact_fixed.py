"""
Test Table Impact Analysis with fixed service
"""
import asyncio
import os
from dotenv import load_dotenv
from apps.api.services.table_impact_service import TableImpactService

# Load .env
load_dotenv()

# Project ID
project_id = "ec771d1a-4fe4-4499-970d-54e28de4d926"
tenant_id = "daac0ee6-3b28-412d-8acd-43ec51149188"  # CORRECT tenant_id from utm_projects

async def test_analysis():
    print("=" * 80)
    print("Testing Table Impact Analysis (FIXED)")
    print("=" * 80)
    
    # Create service
    service = TableImpactService(
        project_id=project_id,
        tenant_id=tenant_id
    )
    
    print("\n1. Running analyze_impacts()...")
    result = await service.analyze_impacts()
    
    print(f"\n✅ Analysis complete!")
    print(f"   Status: {result['status']}")
    print(f"   Total assets analyzed: {result['total_assets']}")
    print(f"   Total impacts detected: {result['total_impacts']}")
    print(f"   Unique tables: {result['unique_tables']}")
    
    if result.get('errors'):
        print(f"\n⚠️ Errors encountered: {len(result['errors'])}")
        for err in result['errors']:
            print(f"   - {err['asset']}: {err['error']}")
    
    print("\n2. Getting table summary...")
    summary = await service.get_table_summary()
    
    print(f"\n✅ Found {len(summary)} tables:")
    for table in summary:
        print(f"   - {table.table_name}")
        print(f"       Readers: {table.readers_count}, Writers: {table.writers_count}")
        print(f"       Operations: {', '.join(table.operations)}")
    
    print("\n" + "=" * 80)
    print("Test complete!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_analysis())

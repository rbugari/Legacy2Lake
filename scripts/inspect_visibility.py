
import os
import sys
import asyncio
from dotenv import load_dotenv

# Add API path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'apps', 'api'))

# Load environment
load_dotenv()

from services.persistence_service import SupabasePersistence

async def inspecters():
    print("--- Tenant & Project Inspection ---")
    db = SupabasePersistence()
    
    # 1. Get all Tenants
    print("\n1. Tenants:")
    try:
        tenants = db.client.table("utm_tenants").select("tenant_id, username").execute().data
        tenant_map = {t['tenant_id']: t['username'] for t in tenants}
        for t in tenants:
            print(f"   [{t['username']}] ID: {t['tenant_id']}")
    except Exception as e:
        print(f"   Error fetching tenants: {e}")
        tenant_map = {}

    # 2. Get all projects named TEST9
    print("\n2. 'TEST9' Projects:")
    try:
        projects = db.client.table("utm_projects").select("*").eq("name", "TEST9").execute().data
        if not projects:
            print("   ❌ None found.")
        else:
            for p in projects:
                owner = tenant_map.get(p['tenant_id'], "UNKNOWN")
                print(f"   - Found 'TEST9' owned by [{owner}] (TenantID: {p['tenant_id']}) - Active: {p.get('is_active')}")
    except Exception as e:
        print(f"   Error fetching projects: {e}")

if __name__ == "__main__":
    asyncio.run(inspecters())

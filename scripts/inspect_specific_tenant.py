
import os
import sys
import asyncio
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'apps', 'api'))
load_dotenv()
from services.persistence_service import SupabasePersistence

async def check():
    db = SupabasePersistence()
    
    # 1. Resolve ID to Name
    target_id = "461b0d87-57a4-4ce5-b990-977bec9603eb"
    res = db.client.table("utm_tenants").select("username").eq("tenant_id", target_id).execute()
    username = res.data[0]['username'] if res.data else "UNKNOWN"
    print(f"Tenant {target_id} is: {username}")

    # 2. Check for TEST9 global
    res = db.client.table("utm_projects").select("project_id, name, tenant_id").eq("name", "TEST9").execute()
    print(f"\nFound {len(res.data)} projects named TEST9:")
    for p in res.data:
        print(f"- Tenant: {p['tenant_id']} | ID: {p['project_id']}")

if __name__ == "__main__":
    asyncio.run(check())


import os
import sys
import asyncio
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'apps', 'api'))
load_dotenv()
from services.persistence_service import SupabasePersistence

async def find_test9_owner():
    db = SupabasePersistence()
    res = db.client.table("utm_projects").select("project_id, name, tenant_id, created_at").eq("name", "TEST9").execute()
    
    print(f"Found {len(res.data)} projects named TEST9:")
    for p in res.data:
        print(f"Project ID: {p['project_id']}")
        print(f"Tenant ID:  {p['tenant_id']}")
        print(f"Created At: {p['created_at']}")
        print("-" * 30)

if __name__ == "__main__":
    asyncio.run(find_test9_owner())

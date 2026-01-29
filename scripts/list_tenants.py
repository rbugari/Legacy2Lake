
import os
import sys
import asyncio
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'apps', 'api'))
load_dotenv()
from services.persistence_service import SupabasePersistence

async def list_all_tenants():
    db = SupabasePersistence()
    res = db.client.table("utm_tenants").select("tenant_id, username").execute()
    print("\n--- ALL TENANTS ---")
    for t in res.data:
        print(f"User: {t['username']} | ID: {t['tenant_id']}")
    print("-------------------")

if __name__ == "__main__":
    asyncio.run(list_all_tenants())

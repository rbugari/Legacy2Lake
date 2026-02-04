import sys
import os
import asyncio

# Setup path to import apps.api
sys.path.append(os.path.join(os.getcwd(), "apps", "api"))

from services.persistence_service import SupabasePersistence

async def main():
    db = SupabasePersistence()
    # Try to fetch tenants
    try:
        res = db.client.table("utm_tenants").select("tenant_id").limit(1).execute()
        if res.data:
            print(f"TENANT_ID={res.data[0]['tenant_id']}")
        else:
            print("No tenants found.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

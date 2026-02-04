
import os
import asyncio
from supabase import create_client

async def main():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        return
        
    client = create_client(url, key)
    res = client.table("utm_projects").select("project_id, name, tenant_id").limit(5).execute()
    for row in res.data:
        print(f"ID: {row['project_id']} | Name: {row['name']} | Tenant: {row['tenant_id']}")

if __name__ == "__main__":
    asyncio.run(main())

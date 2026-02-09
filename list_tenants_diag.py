
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add apps/api to path
sys.path.append(os.path.join(os.getcwd(), "apps", "api"))

from services.persistence_service import SupabasePersistence

async def main():
    load_dotenv()
    db = SupabasePersistence()
    try:
        # Check if utm_tenants table exists and has data
        res = db.client.table("utm_tenants").select("*").execute()
        if res.data:
            print(f"Found {len(res.data)} tenants:")
            for t in res.data:
                print(f"- {t.get('name', 'N/A')} (ID: {t.get('tenant_id', 'N/A')})")
        else:
            print("No tenants found in Supabase.")
            
        # Also check utm_projects for tenant_id references
        res_p = db.client.table("utm_projects").select("name, project_id, tenant_id").execute()
        if res_p.data:
            print("\nProject -> Tenant Mapping:")
            for p in res_p.data:
                print(f"- {p['name']} (Proj: {p['project_id']}, Tenant: {p.get('tenant_id', 'N/A')})")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

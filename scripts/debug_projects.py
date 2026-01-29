import os
import asyncio
import sys
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "api")))

from apps.api.services.persistence_service import SupabasePersistence

async def debug_projects():
    load_dotenv()
    db = SupabasePersistence(tenant_id=None)
    
    print("--- Debugging TEST9 Visibility ---")
    
    # 1. Check if TEST9 exists at all
    res = db.client.table("utm_projects").select("*").eq("name", "TEST9").execute()
    projects = res.data
    
    if not projects:
        print("CRITICAL: No projects named 'TEST9' found in database.")
    else:
        print(f"Found {len(projects)} 'TEST9' records:")
        for p in projects:
            print(f" - ID: {p['project_id']}")
            print(f"   Tenant: {p.get('tenant_id')}")
            print(f"   Client: {p.get('client_id')}")
            print(f"   Active: {p.get('is_active')}")
            # Check tenant name if possible
            if p.get('tenant_id'):
                t_res = db.client.table("utm_tenants").select("username").eq("tenant_id", p.get('tenant_id')).execute()
                if t_res.data:
                    print(f"   Tenant Name: {t_res.data[0]['username']}")
            print("-" * 20)

    # 2. Check all projects for DEMO2/DEMO3 to see what *should* be there
    print("\n--- Checking all projects for DEMO2 & DEMO3 ---")
    
    tenants_res = db.client.table("utm_tenants").select("tenant_id, username").in_("username", ["DEMO2", "DEMO3"]).execute()
    
    for t in tenants_res.data:
        t_id = t['tenant_id']
        t_name = t['username']
        print(f"\nProjects for {t_name} ({t_id}):")
        
        p_res = db.client.table("utm_projects").select("name, tenant_id").eq("tenant_id", t_id).execute()
        for p in p_res.data:
            print(f" - {p['name']}")

if __name__ == "__main__":
    asyncio.run(debug_projects())

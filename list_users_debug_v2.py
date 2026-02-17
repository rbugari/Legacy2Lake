import sys
import os
import asyncio

# Add project root to path
sys.path.append("c:\\proyectos_dev\\UTM")

# Fix import path based on file location
from apps.api.services.persistence_service import SupabasePersistence

async def list_users():
    try:
        print("Connecting to DB...")
        db = SupabasePersistence(tenant_id=None) 
        
        print("Querying utm_users...")
        res = db.client.table("utm_users").select("username, email, role, tenant_id").execute()
        
        if res.data:
            print(f"Found {len(res.data)} users:")
            for u in res.data:
                print(f"- User: {u['username']} | Email: {u['email']} | Role: {u['role']} | Tenant: {u['tenant_id']}")
        else:
            print("No users found in utm_users table.")
            
        print("\nQuerying utm_projects to find 'fff'...")
        proj_res = db.client.table("utm_projects").select("project_id, name, tenant_id").ilike("name", "%fff%").execute()
        
        if proj_res.data:
            for p in proj_res.data:
                print(f"- Project: {p['name']} | ID: {p['project_id']} | Tenant: {p['tenant_id']}")
        else:
            print("Project 'fff' not found in utm_projects.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(list_users())

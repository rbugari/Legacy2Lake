import asyncio
import os
from dotenv import load_dotenv
load_dotenv()
from apps.api.services.persistence_service import SupabasePersistence

async def check_project():
    print("--- Checking Project Existence ---")
    db = SupabasePersistence()
    
    target_id = "2f28aa44-b44e-4f9f-bf35-db93d38fb1e1"
    
    print(f"Looking for project ID: {target_id}")
    
    try:
        # Check by ID
        res = db.client.table("utm_projects").select("*").eq("project_id", target_id).execute()
        if res.data:
            print(f"✅ Project FOUND in DB: {res.data[0]}")
        else:
            print("❌ Project NOT FOUND in DB.")
            
        # List all projects just in case
        all_res = db.client.table("utm_projects").select("project_id, name").execute()
        print("\nAll Projects in DB:")
        for p in all_res.data:
            print(f" - {p['project_id']} ({p['name']})")
            
    except Exception as e:
        print(f"Error querying DB: {e}")

if __name__ == "__main__":
    asyncio.run(check_project())

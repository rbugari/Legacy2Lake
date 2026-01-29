
import os
import sys
import asyncio
from dotenv import load_dotenv

# Add API path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'apps', 'api'))

# Load environment
load_dotenv()

from services.persistence_service import SupabasePersistence, PersistenceService

async def check_test9():
    print("--- Debugging TEST9 ---")
    
    # 1. Check DB for ANY project named TEST9
    print("\n1. Querying DB for 'TEST9'...")
    try:
        db = SupabasePersistence()
        # Raw query to bypass tenant filters for debugging
        res = db.client.table("utm_projects").select("*").eq("name", "TEST9").execute()
        projects = res.data
        
        if not projects:
            print("❌ No project named 'TEST9' found in utm_projects.")
        else:
            print(f"✅ Found {len(projects)} project(s) named 'TEST9':")
            for p in projects:
                print(f"   - ID: {p['project_id']}")
                print(f"   - Tenant ID: {p['tenant_id']}")
                print(f"   - Client ID: {p.get('client_id')}")
                print(f"   - Created At: {p['created_at']}")
                
                # Check FS for this specific tenant
                fs_path = PersistenceService.ensure_solution_dir(p['name'], p['tenant_id'])
                exists = os.path.exists(fs_path)
                print(f"   - File System Path: {fs_path}")
                print(f"   - Exists on Disk? {'✅ YES' if exists else '❌ NO'}")
                if exists:
                    # Check children
                    print(f"     Contents: {os.listdir(fs_path)}")

    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    asyncio.run(check_test9())

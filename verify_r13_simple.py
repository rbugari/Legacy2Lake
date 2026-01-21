import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

import sys
sys.path.append(os.path.join(os.getcwd(), "apps", "api"))

from services.persistence_service import SupabasePersistence

async def check():
    db = SupabasePersistence()
    print("Checking projects...")
    projects = await db.list_projects()
    if not projects:
        print("No projects found.")
        return
        
    pid = projects[0]['id']
    print(f"Testing design_registry for project {pid}...")
    try:
        # Try a simple select
        res = db.client.table('design_registry').select('*').limit(1).execute()
        print(f"Design Registry Select Result: {res}")
    except Exception as e:
        print(f"Design Registry Select FAILED: {e}")

    print("Testing assets metadata columns...")
    try:
        assets = await db.get_project_assets(pid)
        if assets:
            a = assets[0]
            print(f"Current asset: {a.get('filename')} (Business: {a.get('business_entity')}, Target: {a.get('target_name')})")
    except Exception as e:
        print(f"Assets Select FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(check())

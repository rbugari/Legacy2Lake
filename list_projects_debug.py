import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

import sys
sys.path.append(os.path.join(os.getcwd(), "apps", "api"))

from services.persistence_service import SupabasePersistence

async def list_and_check():
    db = SupabasePersistence()
    projects = await db.list_projects()
    print("--- Listing Projects ---")
    for p in projects:
        print(f"ID: {p['id']} | Name: {p['name']} | Status: {p.get('status')}")
        assets = await db.get_project_assets(p['id'])
        print(f"   > Assets: {len(assets)}")

if __name__ == "__main__":
    asyncio.run(list_and_check())

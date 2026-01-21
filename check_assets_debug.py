import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

import sys
sys.path.append(os.path.join(os.getcwd(), "apps", "api"))

from services.persistence_service import SupabasePersistence

async def check_assets():
    db = SupabasePersistence()
    pid = '2f28aa44-b44e-4f9f-bf35-db93d38fb1e1'
    assets = await db.get_project_assets(pid)
    print(f"--- Assets for {pid} ---")
    for a in assets:
        print(f"ID: {a['id']} | File: {a['filename']} | Path: {a['source_path']} | Type: {a['type']}")

if __name__ == "__main__":
    asyncio.run(check_assets())

import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

import sys
sys.path.append(os.path.join(os.getcwd(), "apps", "api"))

from services.persistence_service import SupabasePersistence

async def debug_batch_save():
    db = SupabasePersistence()
    pid = '2f28aa44-b44e-4f9f-bf35-db93d38fb1e1'
    
    # Mock asset data
    assets = [
        {
            "filename": "test.sql",
            "type": "SQL_SCRIPT",
            "source_path": "Triage/test.sql",
            "metadata": {"test": True},
            "selected": True
        }
    ]
    
    print(f"--- Attempting batch_save_assets for project {pid} ---")
    try:
        # We need to bypass the DRAFTING check if status is wrong, but we already know it is TRIAGE.
        # Let's see what happens.
        res = await db.batch_save_assets(pid, assets)
        print(f"Result: {res}")
    except Exception as e:
        print(f"Caught Exception: {e}")

if __name__ == "__main__":
    asyncio.run(debug_batch_save())

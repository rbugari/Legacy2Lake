import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

import sys
sys.path.append(os.path.join(os.getcwd(), "apps", "api"))

from services.persistence_service import SupabasePersistence

async def unlock_base2():
    db = SupabasePersistence()
    # Project base2 ID from previous logs
    pid = "2f28aa44-b44e-4f9f-bf35-db93d38fb1e1"
    print(f"[*] Unlocking and Resetting project {pid} (base2)...")
    
    success = await db.reset_project_data(pid)
    if success:
        print("[OK] Project base2 is now in TRIAGE mode and cleared.")
    else:
        print("[FAIL] Could not reset base2.")

if __name__ == "__main__":
    asyncio.run(unlock_base2())

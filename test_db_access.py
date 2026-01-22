import asyncio
import os
from dotenv import load_dotenv
from apps.api.services.persistence_service import SupabasePersistence

load_dotenv()

async def test_access():
    print("Testing access to utm_asset_context...")
    db = SupabasePersistence()
    project_id = "03372277-e908-4835-907e-56d4ac0c0e34"
    
    try:
        context = await db.get_project_context(project_id)
        print(f"SUCCESS! Fetched {len(context)} entries.")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test_access())

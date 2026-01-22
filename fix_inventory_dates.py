import asyncio
import os
from dotenv import load_dotenv
load_dotenv()
from apps.api.services.persistence_service import SupabasePersistence

async def clear_inventory():
    print("--- Clearing utm_file_inventory for base2 ---")
    db = SupabasePersistence()
    
    # Resolve UUID
    project_id = "base2"
    project_uuid = "03372277-e908-4835-907e-56d4ac0c0e34" # Known from logs
    
    try:
        # Delete entries
        db.client.table("utm_file_inventory").delete().eq("project_id", project_uuid).execute()
        print("✅ Cache cleared. Next API call will trigger a fresh scan with timestamps.")
    except Exception as e:
        print(f"❌ Error clearing cache: {e}")

if __name__ == "__main__":
    asyncio.run(clear_inventory())

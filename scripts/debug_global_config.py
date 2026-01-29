
import asyncio
import os
import sys

sys.path.append(os.getcwd())
from apps.api.services.persistence_service import SupabasePersistence

async def debug_global():
    print("--- Debugging Global Config ---")
    db = SupabasePersistence(tenant_id=None)
    config = await db.get_global_config("provider_settings")
    print(f"Config: {config}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(debug_global())

import os
import asyncio
import sys
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "api")))

from apps.api.services.persistence_service import SupabasePersistence

async def inspect():
    load_dotenv()
    db = SupabasePersistence(tenant_id=None)
    try:
        res = db.client.table("utm_clients").select("*").limit(1).execute()
        if res.data:
            print("Columns:", res.data[0].keys())
        else:
            print("No clients found.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(inspect())

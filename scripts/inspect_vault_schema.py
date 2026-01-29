
import os
import sys
import asyncio
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'apps', 'api'))
load_dotenv()
from services.persistence_service import SupabasePersistence

async def inspect():
    db = SupabasePersistence()
    res = db.client.table("utm_vault").select("*").limit(1).execute()
    if res.data:
        print("Columns:", res.data[0].keys())
    else:
        print("Table empty or inaccessible.")

if __name__ == "__main__":
    asyncio.run(inspect())

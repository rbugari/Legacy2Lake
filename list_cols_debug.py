import os
import asyncio
from dotenv import load_dotenv
load_dotenv()
import sys
sys.path.append(os.path.join(os.getcwd(), "apps", "api"))
from services.persistence_service import SupabasePersistence

async def list_cols():
    db = SupabasePersistence()
    # Query an asset to see keys
    res = db.client.table("assets").select("*").limit(1).execute()
    if res.data:
        print("Columns in 'assets':")
        print(list(res.data[0].keys()))
    else:
        print("No assets found to inspect columns.")

if __name__ == "__main__":
    asyncio.run(list_cols())

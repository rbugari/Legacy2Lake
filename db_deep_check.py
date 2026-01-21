import os
import asyncio
from dotenv import load_dotenv
load_dotenv()
import sys
sys.path.append(os.path.join(os.getcwd(), "apps", "api"))
from services.persistence_service import SupabasePersistence

async def debug_db():
    db = SupabasePersistence()
    print("--- Checking 'design_registry' ---")
    try:
        res = db.client.table("design_registry").select("*").limit(1).execute()
        if res.data:
            print(f"Columns: {list(res.data[0].keys())}")
        else:
            print("Table exists but is empty.")
    except Exception as e:
        print(f"Error reading design_registry: {e}")

    print("\n--- Checking 'assets' row count for base2 ---")
    res = db.client.table("assets").select("id", count="exact").eq("project_id", "2f28aa44-b44e-4f9f-bf35-db93d38fb1e1").execute()
    print(f"Count: {res.count}")

if __name__ == "__main__":
    asyncio.run(debug_db())

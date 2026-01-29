
import os
import sys
import asyncio
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'apps', 'api'))
load_dotenv()
from services.persistence_service import SupabasePersistence

async def check():
    db = SupabasePersistence()
    
    # DEMO3 ID from previous step: f98edb5e-4165-4c49-9fce-18894e8a818c
    demo3_id = "f98edb5e-4165-4c49-9fce-18894e8a818c"
    
    res = db.client.table("utm_projects").select("*").eq("name", "TEST9").eq("tenant_id", demo3_id).execute()
    
    if res.data:
        print(f"✅ TEST9 found for DEMO3!")
        print(res.data[0])
    else:
        print("❌ TEST9 STILL NOT FOUND for DEMO3")

if __name__ == "__main__":
    asyncio.run(check())

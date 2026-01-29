
import os
import sys
import asyncio
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'apps', 'api'))
load_dotenv()
from services.persistence_service import SupabasePersistence

async def check_settings():
    db = SupabasePersistence()
    # DEMO3
    tenant_id = "f98edb5e-4165-4c49-9fce-18894e8a818c"
    
    res = db.client.table("utm_projects").select("project_id, name, settings").eq("name", "TEST9").eq("tenant_id", tenant_id).execute()
    
    if res.data:
        print(f"Project: {res.data[0]['name']}")
        print(f"Settings: {res.data[0]['settings']}")
    else:
        print("Project not found.")

if __name__ == "__main__":
    asyncio.run(check_settings())

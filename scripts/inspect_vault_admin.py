
import os
import sys
import asyncio
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'apps', 'api'))
load_dotenv()
from services.persistence_service import SupabasePersistence

async def inspect_as_admin():
    # Initialize without tenant_id to use Service Role fully (if setup allows)
    # OR explicitly set tenant_id=None
    db = SupabasePersistence() 
    print("--- Inspecting Vault (Admin Mode) ---")
    
    # Filter by DEMO3's ID manually
    demo3_id = "f98edb5e-4165-4c49-9fce-18894e8a818c"
    
    res = db.client.table("utm_vault").select("*").eq("tenant_id", demo3_id).execute()
    
    if not res.data:
        print("❌ No providers found for DEMO3.")
    else:
        for p in res.data:
            print(f"Provider: {p['provider_name']}")
            print(f"Credentials: {p['encrypted_credentials']}")

if __name__ == "__main__":
    asyncio.run(inspect_as_admin())

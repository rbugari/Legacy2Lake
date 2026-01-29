
import os
import sys
import asyncio
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'apps', 'api'))
load_dotenv()
from services.persistence_service import SupabasePersistence

async def inspect_vault():
    # DEMO3
    tenant_id = "f98edb5e-4165-4c49-9fce-18894e8a818c"
    
    db = SupabasePersistence(tenant_id=tenant_id)
    print(f"--- Inspecting Vault for Tenant: {tenant_id} ---")
    
    # 1. Get Providers
    res = db.client.table("utm_vault").select("*").eq("tenant_id", tenant_id).execute()
    providers = res.data
    
    if not providers:
        print("❌ No providers found in Vault!")
    else:
        for p in providers:
            print(f"Provider: {p['provider_name']} (Active: {p['is_active']})")
            print(f"Details: {p['encrypted_credentials']}")
            # Note: details might be encrypted or plain dict depending on implementation phase. 
            # Assuming JSON/Dict for now based on previous context.

if __name__ == "__main__":
    asyncio.run(inspect_vault())

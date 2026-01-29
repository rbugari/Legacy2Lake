
import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from apps.api.services.persistence_service import SupabasePersistence

async def clean_vault():
    print("--- Cleaning Vault for DEMO2 ---")
    tenant_id = "bb579c64-c8c1-4602-bd8e-4f7c1e228419"
    
    db = SupabasePersistence(tenant_id=tenant_id) # Context doesn't matter for delete by ID, but good practice
    
    # 1. Delete all vault entries for this tenant
    res = db.client.table("utm_provider_vault").delete().eq("tenant_id", tenant_id).execute()
    
    print(f"Deleted rows: {len(res.data) if res.data else 0}")
    print("Vault cleaned.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(clean_vault())

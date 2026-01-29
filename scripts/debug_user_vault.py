
import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from apps.api.services.persistence_service import SupabasePersistence

async def debug_vault():
    username = "user_saas_5786"
    print(f"--- Debugging Vault for {username} ---")
    
    db = SupabasePersistence(tenant_id=None)
    
    # Get Tenant ID
    user_res = db.client.table("utm_tenants").select("tenant_id").eq("username", username).execute()
    if not user_res.data:
        print("User not found.")
        return
    
    tenant_id = user_res.data[0]["tenant_id"]
    print(f"Tenant ID: {tenant_id}")
    
    # Get Vault
    vault_res = db.client.table("utm_provider_vault").select("*").eq("tenant_id", tenant_id).execute()
    
    print(f"Vault Entries Found: {len(vault_res.data)}")
    for item in vault_res.data:
        print(f"- Provider: {item.get('provider_name')} (Active: {item.get('is_active')})")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(debug_vault())

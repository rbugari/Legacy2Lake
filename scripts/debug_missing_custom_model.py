
import asyncio
import os
import sys

sys.path.append(os.getcwd())
from apps.api.services.persistence_service import SupabasePersistence

async def debug_missing_model():
    username = "user_saas_5786"
    print(f"--- Debugging Missing Model for {username} ---")
    
    db = SupabasePersistence(tenant_id=None)
    
    # Get Tenant
    user_res = db.client.table("utm_tenants").select("tenant_id").eq("username", username).execute()
    if not user_res.data:
        print("User not found")
        return
    tenant_id = user_res.data[0]["tenant_id"]
    print(f"Tenant ID: {tenant_id}")
    
    # 1. Check Catalog (Raw DB check, no filters)
    print("\n[1] Checking Raw Catalog in DB:")
    models_res = db.client.table("utm_model_catalog").select("*").eq("tenant_id", tenant_id).execute()
    if models_res.data:
        for m in models_res.data:
            print(f" - Found Model: {m.get('model_name')} (ID: {m.get('model_id')})")
            print(f"   Provider: {m.get('provider')}")
    else:
        print(" - No models found in database for this tenant.")

    # 2. Check Vault
    print("\n[2] Checking Vault:")
    vault_res = db.client.table("utm_provider_vault").select("provider_name, is_active").eq("tenant_id", tenant_id).execute()
    active_providers = []
    if vault_res.data:
        for v in vault_res.data:
            print(f" - Key: {v.get('provider_name')} (Active: {v.get('is_active')})")
            if v.get('is_active'):
                active_providers.append(v.get('provider_name').lower())
    else:
        print(" - Vault is EMPTY.")
        
    # 3. GLOBAL SEARCH (to find if it was saved with wrong ID)
    print("\n[3] Global Search for 'mini':")
    # Search label or model_id using 'or' logic if possible, or just two queries
    # PostgREST syntax for OR search on different columns is tricky in python lib
    # simple approach: search label first, then model_id
    
    print("Searching 'label'...")
    res_label = db.client.table("utm_model_catalog").select("*").ilike("label", "%mini%").execute()
    
    print("Searching 'model_id'...")
    res_id = db.client.table("utm_model_catalog").select("*").ilike("model_id", "%mini%").execute()
    
    all_res = (res_label.data or []) + (res_id.data or [])
    
    if all_res:
         for m in all_res:
            print(f" - Found: {m.get('label')} (ID: {m.get('model_id')}) | Tenant: {m.get('tenant_id')} | Provider: {m.get('provider')}")
            if m.get('tenant_id') != tenant_id:
                print("   -> MISMATCH: Model saved with wrong Tenant ID!")
            else:
                print("   -> MATCH: Tenant ID matches. Why is it hidden?")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(debug_missing_model())

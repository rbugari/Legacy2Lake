
import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from apps.api.services.persistence_service import SupabasePersistence

async def restore_keys():
    username = "user_saas_5786"
    target_providers = ["openai", "groq"]
    
    print(f"--- Restoring {target_providers} keys for {username} ---")
    
    db = SupabasePersistence(tenant_id=None) # Admin context
    
    # 1. Get Target User
    user_res = db.client.table("utm_tenants").select("tenant_id").eq("username", username).execute()
    if not user_res.data:
        print("Target user not found.")
        return
    tenant_id = user_res.data[0]["tenant_id"]
    print(f"Target Tenant ID: {tenant_id}")
    
    # 2. Find Admin Keys (Tenant IS NULL)
    # Note: Supabase/PostgREST 'is' filter for NULL is slightly different, usually "is.null"
    # But often checking for where tenant_id is null involves a specific query filter.
    # In python supabase lib: .is_("tenant_id", "null")
    
    print("[Action] Searching for Admin keys...")
    admin_keys_res = db.client.table("utm_provider_vault").select("*").is_("tenant_id", "null").execute()
    
    found_keys = {}
    if admin_keys_res.data:
        for k in admin_keys_res.data:
            p_name = k.get("provider_name", "").lower()
            if p_name in target_providers:
                found_keys[p_name] = k

    print(f"Found Admin Keys: {list(found_keys.keys())}")
    
    
    # 3. Insert into User Vault
    # Strategy: Check Env Vars directly since Global Config was empty/missing
    env_map = {
        "openai": "OPENAI_API_KEY",
        "groq": "GROQ_API_KEY"
    }

    for p_name in target_providers:
        print(f"[Action] restoring {p_name} key...")
        
        # Try Env Var first (Most likely source for Admin/System keys)
        env_var = env_map.get(p_name)
        api_key = os.getenv(env_var)
        
        if not api_key:
             print(f"  - WARNING: Could not find API Key for {p_name} in Environment ({env_var})")
             continue
             
        # Prepare payload
        new_entry = {
            "tenant_id": tenant_id,
            "provider_name": p_name,
            "api_key": api_key,
            "base_url": None, # Default
            "is_active": True,
            "meta": {}
        }
        
        # Upsert
        exists = db.client.table("utm_provider_vault").select("id").eq("tenant_id", tenant_id).eq("provider_name", p_name).execute()
        if not exists.data:
            db.client.table("utm_provider_vault").insert(new_entry).execute()
            print(f"  - Success: Added {p_name}")
        else:
            print(f"  - Skipped: {p_name} already exists for user.")

    print("Restoration Complete.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(restore_keys())

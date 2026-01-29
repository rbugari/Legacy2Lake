
import asyncio
import os
import sys
import httpx

sys.path.append(os.getcwd())
from apps.api.services.persistence_service import SupabasePersistence

async def verify_filtering():
    base_url = "http://localhost:8085"
    username = "user_saas_5786"
    password = "DEMO123!"
    
    print(f"--- Verifying Provider Filtering for {username} ---")
    
    # 1. Login to get token/IDs
    async with httpx.AsyncClient() as client:
        print("Logging in...")
        login_res = await client.post(f"{base_url}/login", json={
            "username": username,
            "password": password
        })
        
        if login_res.status_code != 200:
            print(f"Login Failed: {login_res.text}")
            return
            
        data = login_res.json()
        headers = {
            "X-Tenant-ID": data["tenant_id"],
            "X-Client-ID": data["client_id"]
        }
        
        # 2. Fetch Providers with User Headers
        print("Fetching /providers with Tenant context...")
        prov_res = await client.get(f"{base_url}/providers", headers=headers)
        
        if prov_res.status_code == 200:
            providers = prov_res.json()
            print(f"Providers returned: {len(providers)}")
            names = [p["id"] for p in providers]
            print(f"List: {names}")
            
            # Validation Logic
            # User should have 'openai' (restored) and maybe 'groq' (restored).
            # Should NOT have 'azure', 'anthropic', etc. unless restored.
            # Based on previous restoration steps:
            # - OpenAI: Attempted restore (Env var missing, but maybe vault entry created empty?)
            # - Groq: Attempted restore.
            # Let's check what's ACTUALLY in the vault first to know what to expect.
            
            db = SupabasePersistence(tenant_id=None)
            vault = db.client.table("utm_provider_vault").select("provider_name").eq("tenant_id", data["tenant_id"]).execute()
            vault_providers = {v["provider_name"].lower() for v in vault.data}
            print(f"Actual Vault Content: {vault_providers}")
            
            missing_from_api = vault_providers - set(names)
            extra_in_api = set(names) - vault_providers
            
            if not missing_from_api and not extra_in_api:
                print("SUCCESS: API matches Vault exactly.")
            else:
                print("FAILED: API does not match Vault.")
                if missing_from_api: print(f" - Missing from API: {missing_from_api}")
                if extra_in_api: print(f" - Extra in API (Leak?): {extra_in_api}")
                
        else:
            print(f"API Error: {prov_res.status_code}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(verify_filtering())

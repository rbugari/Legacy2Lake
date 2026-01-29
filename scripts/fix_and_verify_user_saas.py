
import asyncio
import os
import sys
import httpx

# Add project root to path
sys.path.append(os.getcwd())

from apps.api.services.persistence_service import SupabasePersistence

async def fix_and_verify():
    username = "user_saas_5786"
    password = "DEMO123!"
    base_url = "http://localhost:8085"
    
    print(f"--- Fixing Model Leakage for {username} ---")
    
    # 1. Clean Vault
    db = SupabasePersistence(tenant_id=None)
    user_res = db.client.table("utm_tenants").select("tenant_id").eq("username", username).execute()
    
    if not user_res.data:
        print("User not found.")
        return
    tenant_id = user_res.data[0]["tenant_id"]
    
    print(f"[Action] Deleting vault entries for Tenant: {tenant_id}...")
    db.client.table("utm_provider_vault").delete().eq("tenant_id", tenant_id).execute()
    print("Vault Cleared.")
    
    # 2. Verify Fix (Login & Check Catalog)
    print("\n[Verification] Logging in and checking catalog...")
    async with httpx.AsyncClient() as client:
        # Login
        login_res = await client.post(f"{base_url}/login", json={
            "username": username,
            "password": password
        })
        
        if login_res.status_code != 200:
            print(f"Login Failed: {login_res.text}")
            return
            
        token_data = login_res.json()
        # Ensure we use the IDs returned to emulate the frontend
        headers = {
            "X-Tenant-ID": token_data["tenant_id"],
            "X-Client-ID": token_data["client_id"]
        }
        
        # Get Catalog
        catalog_res = await client.get(f"{base_url}/catalog", headers=headers)
        
        if catalog_res.status_code == 200:
            data = catalog_res.json()
            models = data.get("catalog", [])
            print(f"Models Found: {len(models)}")
            
            # EXPECTATION: Even with keys restored, catalog should be 0 
            # because we disabled 'is_public' auto-suggestion.
            if len(models) == 0:
                print("SUCCESS: Catalog is empty. Strict Isolation (No Suggestions) working.")
            else:
                print("FAILED: Models still visible (Auto-suggestion active).")
                print([m["model_id"] for m in models])
        else:
             print(f"API Error: {catalog_res.status_code}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(fix_and_verify())


import asyncio
import os
import sys
import httpx
from dotenv import load_dotenv

# Ensure we can import from apps
sys.path.append(os.getcwd())

async def verify_isolation():
    base_url = "http://localhost:8085"
    print("\n--- Verifying Catalog Isolation ---")
    
    async with httpx.AsyncClient() as client:
        # 1. Login as DEMO2 (The Client User)
        print("[1] Logging in as DEMO2...")
        login_res = await client.post(f"{base_url}/auth/login", json={
            "username": "DEMO2",
            "password": "DEMO123!"
        })
        if login_res.status_code != 200:
             print(f"FAILED: Could not login as DEMO2: {login_res.text}")
             return
        
        user_data = login_res.json()
        tenant_id = user_data["tenant_id"]
        print(f"Logged in as {tenant_id}")

        # 1.5 Check Vault
        print("\n[1.5] Checking Vault for DEMO2...")
        vault_res = await client.get(f"{base_url}/vault", headers={"X-Tenant-ID": tenant_id})
        if vault_res.status_code == 200:
             print("Vault:", vault_res.json())
        else:
             print("Failed to fetch vault")

        # 2. Check Catalog (Should be EMPTY because Vault is empty)
        print("\n[2] Checking Model Catalog for DEMO2 (Expect EMPTY)...")
        catalog_res = await client.get(f"{base_url}/catalog", headers={"X-Tenant-ID": tenant_id})
        
        if catalog_res.status_code == 200:
            data = catalog_res.json()
            models = data.get("catalog", [])
            print(f"Models found: {len(models)}")
            
            if len(models) == 0:
                print("SUCCESS: Catalog is empty (Clean State).")
            else:
                print("FAILED: Catalog is NOT empty.")
                print("Found models:", [m["model_id"] for m in models])
                if "azure-gpt-4o" in [m["model_id"] for m in models]:
                     print("CRITICAL: Azure models leaking!")
        else:
             print(f"FAILED: API Error {catalog_res.status_code}")

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(verify_isolation())

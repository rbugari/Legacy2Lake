
import asyncio
import os
import httpx
from dotenv import load_dotenv

async def test_saas():
    base_url = "http://localhost:8085"
    
    print("\n--- Testing SaaS & Impersonation ---")
    
    # 1. Login as Admin (Assuming DEMO exists from previous migration)
    async with httpx.AsyncClient() as client:
        print("[1] Logging in as Admin (DEMO)...")
        login_res = await client.post(f"{base_url}/auth/login", json={
            "username": "DEMO",
            "password": "DEMO123!"
        })
        if login_res.status_code != 200:
             print(f"FAILED: Could not login as admin: {login_res.text}")
             return
        
        admin_data = login_res.json()
        admin_tenant_id = admin_data["tenant_id"]
        print(f"SUCCESS: Admin Tenant ID: {admin_tenant_id}")

        # 2. Create a new Client
        print("\n[2] Creating a new Client 'TEST_SAAS_CORP'...")
        client_res = await client.post(
            f"{base_url}/auth/clients",
            json={"name": "TEST_SAAS_CORP"},
            headers={"X-Tenant-ID": admin_tenant_id, "X-Role": "ADMIN"}
        )
        if client_res.status_code != 200:
            print(f"FAILED: {client_res.text}")
            # If it already exists, that's fine for testing
            if "exists" in client_res.text:
                 # Try to find it
                 list_res = await client.get(f"{base_url}/auth/clients", headers={"X-Tenant-ID": admin_tenant_id, "X-Role": "ADMIN"})
                 new_client_id = [c["client_id"] for c in list_res.json() if c["name"] == "TEST_SAAS_CORP"][0]
            else:
                 return
        else:
            new_client_id = client_res.json()["client_id"]
        print(f"SUCCESS: Client ID: {new_client_id}")

        # 3. Create a Tenant for that Client
        print("\n[3] Creating a Tenant 'USER_SAAS'...")
        import random
        random_suffix = random.randint(1000, 9999)
        username = f"user_saas_{random_suffix}"
        tenant_res = await client.post(
            f"{base_url}/auth/tenants",
            json={
                "username": username,
                "password": "Password123!",
                "client_id": new_client_id,
                "role": "USER"
            },
            headers={"X-Tenant-ID": admin_tenant_id, "X-Role": "ADMIN"}
        )
        if tenant_res.status_code != 200:
             print(f"FAILED: {tenant_res.text}")
             return
        new_tenant_id = tenant_res.json()["tenant_id"]
        print(f"SUCCESS: Tenant ID: {new_tenant_id}")

        # 4. Test Impersonation
        # Admin wants to list projects for the NEW tenant
        print(f"\n[4] Testing Admin Impersonation of {username}...")
        projects_res = await client.get(
            f"{base_url}/auth/tenants", # Use an admin endpoint to test role preservation
            headers={
                "X-Admin-Tenant-ID": admin_tenant_id,
                "X-Tenant-ID": new_tenant_id,
                "X-Client-ID": new_client_id
            }
        )
        if projects_res.status_code == 200:
            print(f"SUCCESS: Impersonation worked. Admin privileges preserved.")
        else:
            print(f"FAILED: {projects_res.status_code} - {projects_res.text}")

        # 5. Test Unauthorized Impersonation
        print("\n[5] Testing Unauthorized Impersonation (User trying to impersonate Admin)...")
        bad_impersonation = await client.get(
            f"{base_url}/auth/tenants",
            headers={
                "X-Admin-Tenant-ID": new_tenant_id, # User trying to be admin
                "X-Tenant-ID": admin_tenant_id,
                "X-Client-ID": admin_data["client_id"]
            }
        )
        if bad_impersonation.status_code == 403:
            print("SUCCESS: Blocked unauthorized impersonation.")
        else:
            print(f"FAILED: Should have been 403, got {bad_impersonation.status_code}")

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(test_saas())

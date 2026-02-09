
import asyncio
import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

async def check_users_tenants(name, url, key):
    client = create_client(url, key)
    print(f"\n--- Checking Persistence in {name} ---")
    
    tables = ["utm_users", "utm_tenants", "auth.users"]
    
    # Check utm_clients
    try:
        res = client.table("utm_clients").select("*", count="exact").execute()
        print(f"- utm_clients: {res.count} rows.")
    except Exception as e:
        print(f"- utm_clients: Error ({e})")

    # Check utm_tenants
    try:
        res = client.table("utm_tenants").select("*", count="exact").execute()
        print(f"- utm_tenants: {res.count} rows.")
    except Exception as e:
         print(f"- utm_tenants: Error ({e})")

async def main():
    load_dotenv() # Load from current .env (which is now PROD)
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not key:
        print("Error: Missing credentials in .env")
        return

    await check_users_tenants("PROD (Current Env)", url, key)

if __name__ == "__main__":
    asyncio.run(main())


import asyncio
import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

async def check_providers_models():
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not key:
        print("Error: Missing credentials in .env")
        return

    client = create_client(url, key)
    print(f"\n--- Checking Providers & Models in PROD ---")
    
    # 1. Check Provider Vault
    try:
        res = client.table("utm_provider_vault").select("*").execute()
        print(f"\n[Provider Vault] Found {len(res.data)} Active Credentials:")
        for p in res.data:
            print(f"- {p.get('provider_name')} (Active: {p.get('is_active')})")
    except Exception as e:
        print(f"Error checking Vault: {e}")

    # 2. Check Agent Catalog (Assigned Models/Prompts)
    try:
        res = client.table("utm_agent_catalog").select("*").eq("is_active", True).execute()
        print(f"\n[Agent Catalog] Found {len(res.data)} Active Agents:")
        for a in res.data:
             print(f"- {a.get('agent_id')} ({a.get('role')})")
    except Exception as e:
         print(f"Error checking Agents: {e}")

    # 3. Check System Catalog (Available Models)
    try:
        res = client.table("utm_system_catalog").select("*", count="exact").eq("is_active", True).execute()
        print(f"\n[Model Catalog] {res.count} defined models available in system.")
    except Exception as e:
         print(f"Error checking Catalog: {e}")

async def main():
    await check_providers_models()

if __name__ == "__main__":
    asyncio.run(main())

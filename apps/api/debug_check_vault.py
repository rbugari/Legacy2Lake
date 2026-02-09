import asyncio
import os
import sys
from dotenv import load_dotenv

# Force load .env file to ensure keys are available
load_dotenv()

# Add project root to sys.path
sys.path.append("c:\\proyectos_dev\\UTM")

from apps.api.services.persistence_service import SupabasePersistence

async def main():
    print("--- Checking Provider Vault ---")
    try:
        db = SupabasePersistence()
        # Fetch all rows from utm_provider_vault to see what's stored
        res = db.client.table("utm_provider_vault").select("*").execute()
        
        print(f"Found {len(res.data)} credentials:")
        for row in res.data:
            print(f"- Provider: '{row['provider_name']}' (ID: {row.get('id')}) | Tenant: {row.get('tenant_id')} | Active: {row.get('is_active')}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

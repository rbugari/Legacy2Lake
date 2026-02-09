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
    print("--- Checking Model Catalog ---")
    try:
        db = SupabasePersistence()
        # Fetch all rows from utm_model_catalog
        res = db.client.table("utm_model_catalog").select("*").execute()
        
        print(f"Found {len(res.data)} models:")
        for row in res.data:
            print(f"- Model: '{row['model_id']}' | Provider: '{row['provider']}' | Tenant: {row.get('tenant_id')} | Active: {row.get('is_active')}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

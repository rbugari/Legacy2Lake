
import asyncio
from supabase import create_client

# Credentials from History (Step 1862)

# ENV 1: qdsdf...
URL_1 = "https://qdsdfityyxmalyipqbfm.supabase.co"
KEY_1 = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFkc2RmaXR5eXhtYWx5aXBxYmZtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODg2NTczOSwiZXhwIjoyMDg0NDQxNzM5fQ.f4Ge4MPpeDoFLgLSD9e79V2N-ND-aU9YqwNp2VrOgC0"

# ENV 2: wdmlnv...
URL_2 = "https://wdmlnvppkhjjeuiutnjl.supabase.co"
KEY_2 = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndkbWxudnBwa2hqamV1aXV0bmpsIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDA4MjM2NiwiZXhwIjoyMDg1NjU4MzY2fQ.ptqq5JugnDa2FcuTeSl28PfbfKfW5Qz4tDuMggH9eeg"

async def check_env(name, url, key):
    print(f"\n--- Checking {name} ({url[:15]}...) ---")
    try:
        client = create_client(url, key)
        
        # Check Provider Vault
        res_vault = client.table("utm_provider_vault").select("*", count="exact").execute()
        print(f"Provider Vault: {res_vault.count} rows")
        
        # Check Agent Matrix
        res_matrix = client.table("utm_agent_matrix").select("*", count="exact").execute()
        print(f"Agent Matrix: {res_matrix.count} rows")
        
        # Check Model Catalog (Custom models)
        res_model = client.table("utm_model_catalog").select("*", count="exact").execute()
        print(f"Model Catalog: {res_model.count} rows")
        
    except Exception as e:
        print(f"Error checking {name}: {e}")

async def main():
    await check_env("ENV 1 (qdsdf)", URL_1, KEY_1)
    await check_env("ENV 2 (wdmlnv)", URL_2, KEY_2)

if __name__ == "__main__":
    asyncio.run(main())

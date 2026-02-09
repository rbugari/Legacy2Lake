
import asyncio
import os
import sys
from supabase import create_client, Client

async def check_env(name, url, key):
    client = create_client(url, key)
    print(f"\n--- Checking {name} ({url}) ---")
    
    tables_to_check = ["utm_tenants", "utm_projects", "utm_clients"]
    for table in tables_to_check:
        try:
            res = client.table(table).select("*").execute()
            print(f"- {table}: {len(res.data)} rows.")
            if res.data:
                for row in res.data[:3]:
                    print(f"  - {row.get('name') or row.get('label') or row.get('id') or row.get('tenant_id')}")
        except Exception as e:
            print(f"- {table}: Error: {e}")

async def main():
    dev_url = "https://qdsdfityyxmalyipqbfm.supabase.co"
    dev_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFkc2RmaXR5eXhtYWx5aXBxYmZtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODg2NTczOSwiZXhwIjoyMDg0NDQxNzM5fQ.f4Ge4MPpeDoFLgLSD9e79V2N-ND-aU9YqwNp2VrOgC0"
    
    prod_url = "https://wdmlnvppkhjjeuiutnjl.supabase.co"
    prod_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndkbWxudnBwa2hqamV1aXV0bmpsIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDA4MjM2NiwiZXhwIjoyMDg1NjU4MzY2fQ.ptqq5JugnDa2FcuTeSl28PfbfKfW5Qz4tDuMggH9eeg"

    await check_env("DEV", dev_url, dev_key)
    await check_env("PROD", prod_url, prod_key)

if __name__ == "__main__":
    asyncio.run(main())

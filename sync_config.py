
import asyncio
from supabase import create_client

# DEV (Source)
DEV_URL = "https://qdsdfityyxmalyipqbfm.supabase.co"
DEV_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFkc2RmaXR5eXhtYWx5aXBxYmZtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODg2NTczOSwiZXhwIjoyMDg0NDQxNzM5fQ.f4Ge4MPpeDoFLgLSD9e79V2N-ND-aU9YqwNp2VrOgC0"

# PROD (Target)
PROD_URL = "https://wdmlnvppkhjjeuiutnjl.supabase.co"
PROD_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndkbWxudnBwa2hqamV1aXV0bmpsIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDA4MjM2NiwiZXhwIjoyMDg1NjU4MzY2fQ.ptqq5JugnDa2FcuTeSl28PfbfKfW5Qz4tDuMggH9eeg"

async def sync_table(dev, prod, table, id_col):
    print(f"\nSynced {table}...")
    try:
        # 1. Fetch from DEV
        res = dev.table(table).select("*").execute()
        source_data = res.data
        print(f"  - Found {len(source_data)} rows in DEV.")
        
        if not source_data:
            return

        # 2. Upsert to PROD (Remove 'id' if needed to let PROD generate it, BUT for sync we usually want match)
        # We will try to upsert based on specific columns if possible, but simplest is bulk upsert.
        # Supabase upsert works if primary key matches.
        
        # Clean data (remove None/nulls if they cause issues? supabase usually handles)
        # Actually, if we want to exact match, we pass the ID.
        
        count = 0
        for row in source_data:
            try:
                # Try upsert
                # Remove 'created_at' to avoid issues? No, keep it.
                prod.table(table).upsert(row).execute()
                count += 1
            except Exception as e:
                print(f"  - Error upserting row {row.get(id_col)}: {e}")
        
        print(f"  - Successfully synced {count} rows to PROD.")

    except Exception as e:
        print(f"  - Fatal error syncing {table}: {e}")

async def main():
    dev = create_client(DEV_URL, DEV_KEY)
    prod = create_client(PROD_URL, PROD_KEY)
    
    print("Starting Configuration Sync: DEV -> PROD")
    
    # 1. Sync Provider Vault (Critical)
    await sync_table(dev, prod, "utm_provider_vault", "id")
    
    # 2. Sync Model Catalog (Custom Models)
    await sync_table(dev, prod, "utm_model_catalog", "model_id")
    
    # 3. Sync Agent Matrix (Assignments)
    await sync_table(dev, prod, "utm_agent_matrix", "id")
    
    # 4. Sync Tech Catalog (If custom cartridges?)
    # await sync_table(dev, prod, "utm_system_catalog", "id") # optional
    
    print("\nSync Complete.")

if __name__ == "__main__":
    asyncio.run(main())


import asyncio
import os
import sys
from dotenv import load_dotenv

# Add apps/api to path
sys.path.append(os.path.join(os.getcwd(), "apps", "api"))

from services.persistence_service import SupabasePersistence

async def main():
    load_dotenv()
    db = SupabasePersistence()
    try:
        # Querying information_schema to see all public tables
        res = db.client.rpc("get_tables_info").execute() # This might not exist
    except:
        try:
            # Fallback: Query pg_tables directly if permissions allow or try to list some common ones
            query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            # Supabase client doesn't have a direct 'sql' method easily accessible, but we can try to guess tables
            # based on my previous knowledge of the app.
            tables = ["utm_projects", "utm_assets", "utm_tenants", "utm_agent_catalog", "utm_knowledge_hub", "utm_asset_notes", "utm_extraction_rules"]
            print("Checking existence of common tables:")
            for t in tables:
                try:
                    r = db.client.table(t).select("count", count="exact").limit(1).execute()
                    print(f"- {t}: EXISTS (Rows: {r.count})")
                except Exception as e:
                    print(f"- {t}: NOT FOUND or Error: {e}")
        except Exception as e:
            print(f"Error listing tables: {e}")

if __name__ == "__main__":
    asyncio.run(main())

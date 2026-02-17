
import asyncio
import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

async def main():
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    client = create_client(url, key)
    
    try:
        # 1. Check is_active status
        res = client.table("utm_supported_techs").select("tech_id, label, role, is_active").execute()
        print("Technology Status:")
        for t in res.data:
            print(f"- {t['label']} ({t['role']}): is_active={t['is_active']}")
        
        # 2. Wipe projects and related data
        tables_to_wipe = [
            "utm_logical_steps",
            "utm_transformations",
            "utm_asset_context",
            "utm_file_inventory",
            "utm_execution_logs",
            "utm_objects",
            "utm_projects"
        ]
        
        print("\nWiping Project Data:")
        for table in tables_to_wipe:
            try:
                # Delete all rows
                res = client.table(table).delete().neq("project_id", "00000000-0000-0000-0000-000000000000").execute()
                print(f"- {table}: Wiped.")
            except Exception as e:
                # Some tables might not have project_id, try deleting everything
                try:
                    res = client.table(table).delete().neq("id", "-1").execute()
                    print(f"- {table}: Wiped (fallback).")
                except:
                    print(f"- {table}: Error wiping: {e}")

        print("\nCleanup Complete.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

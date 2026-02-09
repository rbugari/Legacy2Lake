
import asyncio
import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

async def main():
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    client = create_client(url, key)
    
    try:
        # Check for catalogs
        catalogs = ["utm_supported_techs", "utm_agent_catalog", "utm_system_catalog"]
        print("Checking Catalogs:")
        for table in catalogs:
            try:
                res = client.table(table).select("*").execute()
                print(f"- {table}: Found {len(res.data)} rows.")
                if len(res.data) > 0:
                    for item in res.data[:2]: # Show first 2 items
                        print(f"  - {item.get('label') or item.get('name') or item.get('tech_id')}")
            except Exception as e:
                print(f"- {table}: Error or Not Found: {e}")

        # Check for projects
        try:
             res = client.table("utm_projects").select("project_id, name").execute()
             print(f"\nProjects Found: {len(res.data)}")
             for p in res.data:
                 print(f"- {p['name']} ({p['project_id']})")
        except Exception as e:
             print(f"\nError listing projects: {e}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

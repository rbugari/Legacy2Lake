import os
import asyncio
from dotenv import load_dotenv

# Load env
load_dotenv()

from apps.api.services.persistence_service import SupabasePersistence

async def main():
    print("--- Debugging DB Access ---")
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    print(f"URL: {url}")
    print(f"Key: {key[:10]}...{key[-5:] if key else ''}")
    
    db = SupabasePersistence()
    
    # 1. Try Read utm_projects
    print("\nReading projects (utm_projects)...")
    try:
        data = await db.list_projects()
        print(f"Read Success! Found {len(data)} projects.")
        for p in data:
            print(f" - {p.get('name')} (id: {p.get('project_id')})")
    except Exception as e:
        print(f"PROJECTS READ ERROR: {e}")

    # 2. Try Read utm_global_config
    print("\nReading global config...")
    try:
        data = await db.get_global_config("sources")
        print(f"Read Success: {data}")
    except Exception as e:
        print(f"CONFIG READ ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())

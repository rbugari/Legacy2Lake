
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
        res = db.client.table("utm_projects").select("*").execute()
        if res.data:
            print(f"Found {len(res.data)} projects:")
            for p in res.data:
                print(f"- {p['name']} (ID: {p['project_id']})")
        else:
            print("No projects found in Supabase.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

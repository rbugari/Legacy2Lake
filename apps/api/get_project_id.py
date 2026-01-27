
import asyncio
import os
import sys

# Add apps to path
sys.path.append(os.getcwd())

from services.persistence_service import SupabasePersistence

async def main():
    db = SupabasePersistence()
    try:
        res = db.client.table("utm_projects").select("project_id").eq("name", "Legacy2Lake_MVP_Target_Test").execute()
        if res.data:
            print(f"Project ID: {res.data[0]['project_id']}")
        else:
            print("Project not found")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

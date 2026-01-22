import asyncio
import os
from dotenv import load_dotenv
load_dotenv()
from apps.api.services.persistence_service import SupabasePersistence

async def check_dates():
    print("--- Checking Dates for base2 (0337...) ---")
    db = SupabasePersistence()
    project_id = "03372277-e908-4835-907e-56d4ac0c0e34"
    
    files = await db.get_project_files_from_db(project_id)
    print(f"File count: {len(files)}")
    
    if files:
        print("Sample file:", files[0].get('name'))
        print("Last Modified:", files[0].get('last_modified'))
        print("Type:", type(files[0].get('last_modified')))
    else:
        print("No files found!")

if __name__ == "__main__":
    asyncio.run(check_dates())

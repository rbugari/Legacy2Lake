import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure we can import from apps
sys.path.append(os.getcwd())

# Load .env from root
load_dotenv(".env")

from apps.api.services.persistence_service import SupabasePersistence

async def fix_inventory(project_name):
    print(f"Fixing inventory for {project_name}...")
    
    # Initialize Persistence
    # Note: SupabasePersistence expects SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY to be in os.environ
    if not os.getenv("SUPABASE_URL"):
        print("Error: SUPABASE_URL not found in environment.")
        return

    try:
        db = SupabasePersistence()
        
        # 1. Get UUID
        project_uuid = await db.get_project_id_by_name(project_name)
        if not project_uuid:
            print(f"Project '{project_name}' not found in DB.")
            return

        print(f"Found Project UUID: {project_uuid}")

        # 2. Force Sync
        print(f"Syncing file inventory...")
        success = await db.sync_file_inventory(project_uuid)
        print(f"Sync result: {success}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "base"
    asyncio.run(fix_inventory(target))

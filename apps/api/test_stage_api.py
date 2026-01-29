import asyncio
import os
from dotenv import load_dotenv

# Load .env from root
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")))

from services.persistence_service import SupabasePersistence

async def test_stage_update():
    print("Testing Stage Update for 'Test1'...")
    db = SupabasePersistence()
    
    # 1. Resolve 'Test1'
    project_id = await db.get_project_id_by_name("Test1")
    if not project_id:
        print("Error: Could not find project 'Test1' in DB.")
        return

    print(f"Found project 'Test1' with ID: {project_id}")
    
    # 2. Try to update stage to '1' (no-op) or '2'
    print("Attempting to update stage to '1'...")
    success = await db.update_project_stage(project_id, "1")
    print(f"Success: {success}")

    print("\nAttempting to update stage to '2' (Triage)...")
    success = await db.update_project_stage(project_id, "2")
    print(f"Success: {success}")
    
    # 3. Verify
    print("\nVerifying metadata...")
    meta = await db.get_project_metadata(project_id)
    if meta:
        print(f"Current project stage: {meta.get('stage')}")
    else:
        print("Error fetching metadata.")

if __name__ == "__main__":
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    asyncio.run(test_stage_update())


import asyncio
import sys
import os
from dotenv import load_dotenv

sys.path.append(os.getcwd())
load_dotenv()

from apps.api.services.persistence_service import SupabasePersistence

async def fix_registry():
    project_name = "base2"
    print(f"Fixing registry for project: {project_name}")
    
    db = SupabasePersistence()
    project_id = await db.get_project_id_by_name(project_name)
    
    if not project_id:
        print(f"Project {project_name} not found.")
        return

    print(f"Found Project ID: {project_id}")
    
    # Force insert target_stack
    success = await db.update_design_registry(
        project_id, 
        "PATHS", 
        "target_stack", 
        "pyspark"
    )
    
    if success:
        print("Successfully inserted 'target_stack' = 'pyspark'")
    else:
        print("Failed to insert registry entry.")

if __name__ == "__main__":
    asyncio.run(fix_registry())

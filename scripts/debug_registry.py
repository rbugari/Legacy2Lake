
import asyncio
import sys
import os
from dotenv import load_dotenv

sys.path.append(os.getcwd())
load_dotenv()

from apps.api.services.persistence_service import SupabasePersistence
from apps.api.services.knowledge_service import KnowledgeService

async def check_registry():
    project_name = "base2"
    print(f"Checking registry for project: {project_name}")
    
    db = SupabasePersistence()
    project_id = await db.get_project_id_by_name(project_name)
    
    if not project_id:
        print("[ERROR] Project not found.")
        return

    print(f"Project ID: {project_id}")
    
    # Check DB directly
    registry = await db.get_design_registry(project_id)
    target_stack = "NOT FOUND"
    for r in registry:
        cat = r.get('category') if isinstance(r, dict) else r.category
        key = r.get('key') if isinstance(r, dict) else r.key
        val = r.get('value') if isinstance(r, dict) else r.value
        
        if key == "target_stack":
            target_stack = val
            print(f"[DB] Found target_stack: {val}")
            
    # Check what KnowledgeService flattens it to (which is what ArchitectService uses)
    flat = KnowledgeService.flatten_knowledge(registry)
    print(f"[FLATTENED] paths.target_stack = {flat.get('paths', {}).get('target_stack')}")

if __name__ == "__main__":
    asyncio.run(check_registry())

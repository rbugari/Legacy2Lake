import asyncio
import os
from dotenv import load_dotenv
load_dotenv()
from apps.api.services.persistence_service import SupabasePersistence

async def debug_dates():
    print("--- Debugging File Dates for base2 ---")
    db = SupabasePersistence()
    
    project_id = "base2"
    files = await db.get_project_files_from_db(project_id)
    
    print(f"Found {len(files)} files/folders in tree response.")
    
    if len(files) > 0:
        # Check the first few children
        for node in files[:5]:
            print(f"Name: {node.get('name')}, Type: {node.get('type')}, Last Modified: {node.get('last_modified')} (Type: {type(node.get('last_modified'))})")
            if node.get('children'):
                for child in node.get('children')[:3]:
                    print(f"  Child: {child.get('name')}, Last Modified: {child.get('last_modified')} (Type: {type(child.get('last_modified'))})")

if __name__ == "__main__":
    asyncio.run(debug_dates())

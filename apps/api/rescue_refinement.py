
import os
import asyncio
from services.persistence_service import PersistenceService

async def rescue_files():
    tenant_id = "f98edb5e-4165-4c49-9fce-18894e8a818c"
    # Source: Stray UUID folder
    src_prefix = f"{tenant_id}/67864f20fe8d4524ba68063a48b5add9/refinement"
    # Destination: testx folder
    dest_prefix = f"{tenant_id}/testx/refinement"
    
    storage = PersistenceService.get_storage()
    print(f"Rescuing files from {src_prefix} to {dest_prefix}...")
    
    try:
        files = storage.list_files(src_prefix, recursive=True)
        print(f"Found {len(files)} items to move.")
        
        for file in files:
            if file["type"] == "file":
                src_key = file["path"]
                # Extract relative path from src_prefix
                rel_path = src_key.replace(src_prefix, "").lstrip("/")
                dest_key = f"{dest_prefix}/{rel_path}"
                
                print(f"Moving: {rel_path}...")
                content = storage.read_file(src_key, is_binary=True)
                storage.save_file(dest_key, content)
                # storage.delete_file(src_key) # Optional: delete after move
        
        print("Rescue complete.")
    except Exception as e:
        print(f"Error during rescue: {e}")

if __name__ == "__main__":
    asyncio.run(rescue_files())

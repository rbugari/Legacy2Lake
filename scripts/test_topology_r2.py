import os
import boto3
import json
from dotenv import load_dotenv

# Mocking PersistenceService and R2StorageProvider for testing
from apps.api.services.persistence_service import PersistenceService
from apps.api.services.storage.r2_storage import R2StorageProvider

def test_topology_discovery():
    load_dotenv()
    
    project_id = "test10"
    tenant_id = "f98edb5e-4165-4c49-9fce-18894e8a818c"
    
    storage = PersistenceService.get_storage()
    base_path = PersistenceService.ensure_solution_dir(project_id, tenant_id=tenant_id)
    print(f"Base Path: {base_path}")
    
    items = storage.list_files(base_path, recursive=True)
    # print(f"Items: {json.dumps(items, indent=2)}")
    
    def get_all_files(nodes):
        files = []
        for n in nodes:
            if n["type"] == "folder" and n.get("children"):
                files.extend(get_all_files(n["children"]))
            elif n["type"] == "file":
                files.append(n)
        return files
    
    all_files = get_all_files(items)
    print(f"Total files found: {len(all_files)}")
    for f in all_files:
        print(f" - {f['name']} (Path: {f['path']})")
        
    dtsx_files = [f for f in all_files if f["name"].lower().endswith(".dtsx")]
    print(f"DTSX files found: {len(dtsx_files)}")

if __name__ == "__main__":
    test_topology_discovery()

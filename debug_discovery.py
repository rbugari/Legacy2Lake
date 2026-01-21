import os
import sys
import asyncio

# Add apps/api to path
sys.path.append(os.path.abspath("apps/api"))

from services.discovery_service import DiscoveryService
from services.persistence_service import PersistenceService

def test_base2_discovery():
    project_id = "base2"
    print(f"Testing discovery for: {project_id}")
    
    path = PersistenceService.ensure_solution_dir(project_id)
    print(f"Resolved path: {path}")
    print(f"Path exists: {os.path.exists(path)}")
    
    if os.path.exists(path):
        print(f"Contents of {path}: {os.listdir(path)}")
        triage_path = os.path.join(path, "Triage")
        if os.path.exists(triage_path):
            print(f"Contents of {triage_path}: {os.listdir(triage_path)}")
    
    manifest = DiscoveryService.generate_manifest(project_id)
    print(f"Manifest file count: {len(manifest['file_inventory'])}")
    for item in manifest['file_inventory'][:5]:
        print(f" - {item['path']}")

if __name__ == "__main__":
    test_base2_discovery()

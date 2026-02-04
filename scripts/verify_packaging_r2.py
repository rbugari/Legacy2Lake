
import os
import sys
import asyncio
import json
from pathlib import Path

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from apps.api.services.persistence_service import PersistenceService
    from apps.api.services.packaging_service import PackagingService
    from apps.api.utils.logger import logger
except ImportError:
    print("Error: Could not import services.")
    sys.exit(1)

async def verify_packaging():
    # Use the real project reported by R2 list earlier
    project_id = "b9613e9a-c56a-4ddf-b45a-3ce319624ea9" 
    tenant_id = "461b0d87-57a4-4ce5-b990-977bec9603eb"
    
    print(f"--- Verifying PackagingService R2 Ingestion for Tenant: {tenant_id} ---")
    
    packager = PackagingService(project_id, tenant_id=tenant_id)
    
    try:
        # This will list R2, download files to temp local dir, and return path
        staging_root = await packager.prepare_bundle()
        print(f"\nSUCCESS: Bundle prepared at {staging_root}")
        
        # 1. Check directory structure
        print("\n[STAGING DIRECTORY CONTENT]")
        for root, dirs, files in os.walk(staging_root):
            rel_root = os.path.relpath(root, staging_root)
            if files:
                print(f"  {rel_root}: {len(files)} files")
                for f in files[:3]:
                    print(f"    - {f}")
                    
        # 2. Specifically check if src/bronze, src/silver, etc are populated
        for layer in ["bronze", "silver", "gold"]:
            layer_dir = os.path.join(staging_root, os.path.basename(staging_root), "src", layer)
            if os.path.exists(layer_dir):
                files = os.listdir(layer_dir)
                print(f"\nLayer '{layer}': {len(files)} files found.")
            else:
                print(f"\nWARNING: Layer dir '{layer}' missing or empty.")
                
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_packaging())

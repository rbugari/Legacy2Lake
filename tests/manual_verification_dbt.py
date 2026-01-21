
import asyncio
import shutil
import sys
import os
sys.path.append(os.getcwd())
from pathlib import Path
from apps.api.services.refinement.cartridges.factory import CartridgeFactory

async def test_dbt_generation():
    print(">>> Starting Manual Verification: Release 3.0 (dbt Cartridge)")
    
    # 1. Setup Mock Project & Registry
    project_id = "verify_dbt_release"
    registry = {
        "paths": {"target_stack": "dbt"},
        "naming": {"silver_prefix": "stg_", "gold_prefix": "dim_"}
    }
    
    # 2. Instantiate Cartridge via Factory
    print(f"[TEST] Requesting Cartridge for target_stack='dbt'...")
    cartridge = CartridgeFactory.get_cartridge(project_id, registry)
    print(f"[TEST] Received Cartridge: {cartridge.__class__.__name__}")
    
    if cartridge.__class__.__name__ != "DbtCartridge":
        print("[FAIL] Factory returned wrong cartridge!")
        return

    # 3. generate_scaffolding
    print("[TEST] Generating Scaffolding...")
    scaffold = cartridge.generate_scaffolding()
    if "dbt_project.yml" in scaffold and "Bronze/sources.yml" in scaffold:
        print("[PASS] dbt_project.yml and sources.yml generated.")
    else:
        print(f"[FAIL] Missing scaffolding files. Got: {list(scaffold.keys())}")

    # 4. generate_bronze
    print("[TEST] Generating Bronze Layer...")
    meta = {"source_path": "legacy_customer.py"}
    bronze_code = cartridge.generate_bronze(meta)
    
    if "{{ source(" in bronze_code and "select * from renamed" in bronze_code:
        print("[PASS] Bronze SQL contains Jinja 'source' and CTEs.")
    else:
        print("[FAIL] Bronze SQL looks wrong:\n" + bronze_code)

    # 5. generate_silver
    print("[TEST] Generating Silver Layer...")
    meta["pk_columns"] = ["cust_id"]
    silver_code = cartridge.generate_silver(meta)
    
    if "{{ ref(" in silver_code and "unique_key=['cust_id']" in silver_code:
        print("[PASS] Silver SQL contains Jinja 'ref' and incremental config.")
    else:
        print("[FAIL] Silver SQL looks wrong:\n" + silver_code)
        
    print(">>> Verification Complete.")

if __name__ == "__main__":
    asyncio.run(test_dbt_generation())

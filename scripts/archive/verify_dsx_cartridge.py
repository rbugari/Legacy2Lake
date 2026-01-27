import sys
import os

# Add apps/api to path
sys.path.append(os.path.join(os.getcwd(), 'apps', 'api'))

from services.extraction.cartridges.datastage_cartridge import DataStageCartridge

def test_datastage_extraction():
    # Setup cartridge pointing to our mock file
    config = {
        "type": "datastage",
        "path": "mock_job.dsx"
    }
    
    cartridge = DataStageCartridge(config)
    
    print("--- Scanning Catalog ---")
    assets = cartridge.scan_catalog()
    for asset in assets:
        print(f"Found Job: {asset['name']} ({asset['type']})")
    
    if assets:
        job_name = assets[0]['name']
        print(f"\n--- Extracting Logic for {job_name} ---")
        logic = cartridge.extract_ddl(job_name)
        print(logic)
        
        # Validation checks
        if "SELECT OrderID" in logic:
            print("\nSUCCESS: SQL Source query extracted.")
        else:
            print("\nFAILURE: SQL Source query missing.")
            
        if "BI_MART.FACT_SALES" in logic:
            print("SUCCESS: Target table extracted.")
        else:
            print("FAILURE: Target table missing.")

if __name__ == "__main__":
    test_datastage_extraction()

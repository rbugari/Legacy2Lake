import sys
import os

# Add apps/api to path
sys.path.append(os.path.join(os.getcwd(), 'apps', 'api'))

from services.extraction.cartridges.talend_cartridge import TalendCartridge

def test_talend_extraction():
    config = {
        "type": "talend",
        "path": "mock_talend.item"
    }
    
    cartridge = TalendCartridge(config)
    
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
        if "SELECT ID, NAME" in logic:
            print("\nSUCCESS: Talend SQL Input extracted.")
        else:
            print("\nFAILURE: SQL Input missing.")
            
        if "FACT_SALES" in logic:
            print("SUCCESS: Target table detected.")
        else:
            print("FAILURE: Target table missing.")

if __name__ == "__main__":
    test_talend_extraction()

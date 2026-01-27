import sys
import os

# Add apps/api to path
sys.path.append(os.path.join(os.getcwd(), 'apps', 'api'))

from services.extraction.cartridges.sap_bods_cartridge import SapBodsCartridge

def test_bods_extraction():
    config = {
        "type": "sap_bods",
        "path": "mock_bods.atl"
    }
    
    cartridge = SapBodsCartridge(config)
    
    print("--- Scanning Catalog ---")
    assets = cartridge.scan_catalog()
    for asset in assets:
        print(f"Found Asset: {asset['name']} ({asset['type']})")
    
    if assets:
        # Test extraction for the Dataflow
        name = "DF_Migrate_Sales"
        print(f"\n--- Extracting Logic for {name} ---")
        logic = cartridge.extract_ddl(name)
        print(logic)
        
        # Validation checks
        if "SELECT O.ID" in logic:
            print("\nSUCCESS: BODS SQL Transform extracted.")
        else:
            print("\nFAILURE: SQL Transform missing.")
            
        if "ORACLE_FACT_SALES" in logic:
            print("SUCCESS: Target table detected.")
        else:
            print("FAILURE: Target table missing.")

if __name__ == "__main__":
    test_bods_extraction()

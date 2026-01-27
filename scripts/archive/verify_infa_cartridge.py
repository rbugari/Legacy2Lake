import sys
import os

# Add apps/api to path
sys.path.append(os.path.join(os.getcwd(), 'apps', 'api'))

from services.extraction.cartridges.informatica_cartridge import InformaticaCartridge

def test_informatica_extraction():
    config = {
        "type": "informatica",
        "path": "mock_infa.xml"
    }
    
    cartridge = InformaticaCartridge(config)
    
    print("--- Scanning Catalog ---")
    assets = cartridge.scan_catalog()
    for asset in assets:
        print(f"Found Mapping: {asset['name']} ({asset['type']})")
    
    if assets:
        mapping_name = assets[0]['name']
        print(f"\n--- Extracting Logic for {mapping_name} ---")
        logic = cartridge.extract_ddl(mapping_name)
        print(logic)
        
        # Validation checks
        if "SELECT O.OrderID" in logic:
            print("\nSUCCESS: Informatica SQL Source query extracted.")
        else:
            print("\nFAILURE: SQL Query missing.")
            
        if "FACT_SALES" in logic:
            print("SUCCESS: Target table detected.")
        else:
            print("FAILURE: Target table missing.")

if __name__ == "__main__":
    test_informatica_extraction()

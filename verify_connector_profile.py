import requests
import json
import time

BASE_URL = "http://127.0.0.1:8087"

def test_sources():
    print("--- Testing Source Profiles ---")
    
    # 1. Clean up
    print("Cleaning up existing sources...")
    sources = requests.get(f"{BASE_URL}/config/sources").json()
    for s in sources:
        requests.delete(f"{BASE_URL}/config/sources/{s['id']}")
        
    # 2. Create Profile
    payload = {
        "id": "src_test_1",
        "name": "Legacy CRM SQL",
        "type": "sqlserver",
        "version": "2008 R2",
        "description": "Main customer database, very old.",
        "context_prompt": "Watch out for implicit conversions."
    }
    print(f"Creating source: {payload['name']}")
    res = requests.post(f"{BASE_URL}/config/sources", json=payload)
    if res.status_code != 200:
        print(f"FAILED to create source: {res.text}")
        return False
        
    # 3. Verify
    print("Verifying source creation...")
    sources = requests.get(f"{BASE_URL}/config/sources").json()
    if len(sources) != 1:
        print(f"FAILED: Expected 1 source, got {len(sources)}")
        return False
        
    src = sources[0]
    if src["version"] != "2008 R2" or src["context_prompt"] != "Watch out for implicit conversions.":
         print(f"FAILED: Source data mismatch: {src}")
         return False
         
    print("✅ Source Profiles OK")
    return True

def test_generators():
    print("\n--- Testing Generator Profiles ---")
    
    # 1. Get Config
    print("Fetching generator config...")
    config = requests.get(f"{BASE_URL}/config/generators").json()
    
    # Verify structure
    if "generators" not in config:
        print(f"FAILED: Response missing 'generators' list: {config.keys()}")
        return False
        
    gens = config["generators"]
    spark = next((g for g in gens if g["type"] == "spark"), None)
    
    if not spark:
        print("FAILED: Spark generator not found in default list.")
        return False
        
    # 2. Update Instruction
    new_instruction = "Use Pandas API on Spark where possible."
    print("Updating Spark instructions...")
    res = requests.post(f"{BASE_URL}/config/generators/update", json={
        "type": "spark",
        "instruction_prompt": new_instruction
    })
    
    if res.status_code != 200:
        print(f"FAILED to update generator: {res.text}")
        return False
        
    # 3. Verify Update
    print("Verifying persistence...")
    config = requests.get(f"{BASE_URL}/config/generators").json()
    spark = next((g for g in config["generators"] if g["type"] == "spark"), None)
    
    if spark.get("instruction_prompt") != new_instruction:
        print(f"FAILED: Instruction not updated. Got: {spark.get('instruction_prompt')}")
        return False
        
    print("✅ Generator Profiles OK")
    return True

if __name__ == "__main__":
    try:
        s_ok = test_sources()
        g_ok = test_generators()
        
        if s_ok and g_ok:
            print("\n🎉 ALL TESTS PASSED")
        else:
            print("\n❌ SOME TESTS FAILED")
    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")


import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE = "http://localhost:8085"
PROJECT_ID = "dd13fc92-4091-456a-8ce4-712406ceb831" # TEST9

# Headers from local storage simulation
HEADERS = {
    "X-Tenant-ID": "f98edb5e-4165-4c49-9fce-18894e8a818c",
    "X-Client-ID": "f98edb5e-4165-4c49-9fce-18894e8a818c",
    "Content-Type": "application/json"
}

def verify_triage():
    print(f"Testing Triage for project {PROJECT_ID}...")
    url = f"{API_BASE}/projects/{PROJECT_ID}/triage"
    payload = {
        "system_prompt": "You are a helpful architect.",
        "user_context": "None"
    }
    
    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=60)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Successfully received triage data.")
            print(f"RAW DATA: {json.dumps(data, indent=2)}")
            
            nodes = data.get("nodes", [])
            assets = data.get("assets", [])
            
            print(f"Found {len(nodes)} nodes and {len(assets)} assets.")
            
            # Check for path-based IDs
            path_ids = [n["id"] for n in nodes if "/" in n["id"]]
            if path_ids:
                print(f"WARNING: Found {len(path_ids)} nodes with PATH as ID instead of UUID!")
                print(f"Example: {path_ids[0]}")
            else:
                print("All nodes have UUID-like IDs (success).")
                
            # Check asset IDs
            null_asset_ids = [a for a in assets if not a.get("id")]
            if null_asset_ids:
                print(f"ERROR: Found {len(null_asset_ids)} assets with NULL ID!")
            else:
                print("All assets have IDs.")
                
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    verify_triage()

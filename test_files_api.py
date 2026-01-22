import requests
import json

API_URL = "http://localhost:8085"
PROJECT_ID = "base2"

def test_files_api():
    print(f"--- Querying Files API for {PROJECT_ID} ---")
    try:
        resp = requests.get(f"{API_URL}/projects/{PROJECT_ID}/files")
        
        if resp.status_code == 200:
            data = resp.json()
            print("Response Status: 200 OK")
            
            # Use json.dumps for pretty printing, but cap it to avoid huge logs
            text = json.dumps(data, indent=2)
            if len(text) > 2000:
                print(f"Response Body (First 2000 chars):\n{text[:2000]}...")
            else:
                print(f"Response Body:\n{text}")
                
            # Check if 'children' exists and has items
            children = data.get("children", [])
            print(f"\nRoot Children Count: {len(children)}")
            
            # recurse to find 'Refinement'
            def find_node(nodes, name):
                for n in nodes:
                    if n['name'] == name: return n
                    if 'children' in n and n['children']:
                        found = find_node(n['children'], name)
                        if found: return found
                return None
                
            refinement = find_node(children, "Refinement")
            if refinement:
                print(f"SUCCESS: Found 'Refinement' folder. Item count: {len(refinement.get('children', []))}")
            else:
                print("FAILURE: 'Refinement' folder NOT found in response.")
                
        else:
            print(f"Response Failed: {resp.status_code} - {resp.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_files_api()

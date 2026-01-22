import requests
import json

base_url = "http://localhost:8085"
project_id = "2f28aa44-b44e-4f9f-bf35-db93d38fb1e1"

print(f"Testing /discovery/status for {project_id}...")
resp = requests.get(f"{base_url}/discovery/status/{project_id}")
print(f"Status Response: {resp.status_code} - {resp.json()}")

print(f"\nTriggering /projects/{project_id}/triage...")
payload = {"system_prompt": "", "user_context": ""}
resp = requests.post(f"{base_url}/projects/{project_id}/triage", json=payload)

if resp.status_code == 200:
    data = resp.json()
    print("SUCCESS!")
    assets = data.get("assets", [])
    print(f"Discovered {len(assets)} assets.")
    for a in assets[:5]:
        print(f" - {a['name']} ({a['type']})")
    
    # Check if they are in the DB too
    print("\nVerifying DB assets...")
    resp_db = requests.get(f"{base_url}/projects/{project_id}/assets")
    db_assets = resp_db.json().get("assets", [])
    print(f"DB reflects {len(db_assets)} assets.")
else:
    print(f"FAILED: {resp.status_code}")
    print(resp.text)

import requests
import time
import json

API_URL = "http://localhost:8085"

def run_test(project_name):
    print(f"\n--- Testing Project: {project_name} ---")
    
    # 1. Trigger Drafting (Agent C)
    # Endpoint derived from main.py: /transpile/orchestrate
    print(f"1. Triggering Drafting for {project_name}...")
    try:
        # Need to find the project ID (UUID) first because the API might expect it? 
        # main.py line 1060: async def trigger_orchestration(project_id: str = Form(...)):
        # It takes 'project_id' as a form field.
        # Wait, previous error showed calling orchestrator with `project_name`.
        # Let's check if the endpoint accepts name or UUID.
        # Most endpoints allow both due to the logic I saw in `PersistenceService`.
        
        # Payload matches `trigger_orchestration` in main.py
        # Note: Depending on main.py, this might needed to be multipart/form-data or json.
        # Main.py uses payload: Dict[str, Any], so it expects JSON.
        payload = {"project_id": project_name, "limit": 0} 
        resp = requests.post(f"{API_URL}/transpile/orchestrate", json=payload)
        # resp = type('obj', (object,), {'status_code': 200, 'json': lambda: {"skipped": True}})
        # print("   [SKIPPED] Drafting (Artifacts exist)")
        
        if resp.status_code == 200:
            print(f"   [SUCCESS] Drafting Triggered. Response: {resp.json()}")
        else:
            print(f"   [FAILED] Drafting Error {resp.status_code}: {resp.text}")
            
    except Exception as e:
        print(f"   [ERROR] Drafting Exception: {e}")

    # 2. Trigger Refinement (Agent A/R)
    # Endpoint: /refine/start (from user's error log and main.py)
    print(f"2. Triggering Refinement for {project_name}...")
    try:
        # Check params for /refine/start
        # Likely takes project_id as query or body. 
        # The user's log showed "POST /refine/start", so likely body.
        # Let's assume JSON body {"project_id": ...} or query param.
        # Based on typical FastAPI:
        resp = requests.post(f"{API_URL}/refine/start", params={"project_id": project_name})
        
        if resp.status_code == 200:
             print(f"   [SUCCESS] Refinement Triggered. Response: {resp.json()}")
        elif resp.status_code == 422:
             # Try body if query failed
             print("   (422 on query param, trying JSON body...)")
             resp = requests.post(f"{API_URL}/refine/start", json={"project_id": project_name})
             if resp.status_code == 200:
                 print(f"   [SUCCESS] Refinement Triggered. Response: {resp.json()}")
             else:
                 print(f"   [FAILED] Refinement Error {resp.status_code}: {resp.text}")
        else:
            print(f"   [FAILED] Refinement Error {resp.status_code}: {resp.text}")

    except Exception as e:
        print(f"   [ERROR] Refinement Exception: {e}")

if __name__ == "__main__":
    # run_test("base")
    run_test("base2") # Uncomment if base succeeds

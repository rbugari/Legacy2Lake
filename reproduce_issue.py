import requests
import json
import uuid

BASE_URL = "http://localhost:8085"
TENANT_ID = "bb579c64-c8c1-4602-bd8e-4f7c1e228419"
HEADERS = {
    "X-Tenant-ID": TENANT_ID,
    "Content-Type": "application/json"
}

MODEL_ID = f"test-model-{uuid.uuid4().hex[:8]}"

def create_model():
    print(f"Creating model {MODEL_ID}...")
    payload = {
        "id": MODEL_ID,
        "name": "Test Model",
        "provider": "openai",
        "context": 0
    }
    resp = requests.post(f"{BASE_URL}/catalog", headers=HEADERS, json=payload)
    print(f"Create Status: {resp.status_code}")
    print(f"Create Response: {resp.text}")

def update_model(context_value):
    print(f"Updating model {MODEL_ID} with context {context_value}...")
    payload = {
        "context": context_value
    }
    # Note: Frontend sends mapped values, let's match frontend exactly
    # Frontend payload keys: id, name, provider, context, deployment_id, api_version
    # But update endpoint only checks keys.
    resp = requests.post(f"{BASE_URL}/catalog/{MODEL_ID}/update", headers=HEADERS, json=payload)
    print(f"Update Status: {resp.status_code}")
    print(f"Update Response: {resp.text}")

def check_model():
    print(f"Checking model {MODEL_ID}...")
    resp = requests.get(f"{BASE_URL}/catalog", headers=HEADERS)
    if resp.status_code == 200:
        catalog = resp.json().get("catalog", [])
        for m in catalog:
            if m["model_id"] == MODEL_ID:
                print(f"FOUND: context_window = {m.get('context_window')}")
                return m.get('context_window')
    else:
        print(f"Failed to fetch catalog: {resp.status_code}")
    return None

def delete_model():
    print(f"Deleting model {MODEL_ID}...")
    requests.delete(f"{BASE_URL}/catalog/{MODEL_ID}", headers=HEADERS)

def main():
    try:
        create_model()
        val = check_model()
        if val != 0:
            print(f"Initial check failed. Expected 0, got {val}")
        
        # Update to 128000
        update_model(128000)
        val = check_model()
        if val == 128000:
            print("SUCCESS: Context updated correctly to 128000.")
        else:
            print(f"FAILURE: Context NOT updated. Got {val}")

        # Test String Input
        update_model("32000")
        val = check_model()
        if val == 32000:
             print("SUCCESS: String context '32000' updated correctly.")
        else:
             print(f"FAILURE: String context NOT updated. Got {val}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        delete_model()

if __name__ == "__main__":
    main()

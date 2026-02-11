"""Test Fabric Silver/Gold - Combined"""
import os, json, requests
from dotenv import load_dotenv
load_dotenv()

API_BASE = "http://localhost:8085"
TENANT_ID = "daac0ee6-3b28-412d-8acd-43ec51149188"
PROJECT_ID = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"
USER_ID = TENANT_ID

def test_silver():
    with open("prompt_lab/cartridges/ms_fabric/silver_layer.md", 'r', encoding='utf-8') as f:
        prompt = f.read()
    
    response = requests.post(f"{API_BASE}/transpile/task",
        json={"node_data": {"layer": "silver", "tech_id": "fabric", "cartridge_prompt": prompt}, 
              "context": {"project_id": PROJECT_ID}},
        headers={"X-Tenant-ID": TENANT_ID, "X-User-ID": USER_ID}, timeout=120
    )
    
    if response.status_code == 200:
        code = response.json().get("final_code", response.json().get("code", ""))
        with open("prompt_lab/TEST_OUTPUT_MS_FABRIC_SILVER_01.py", 'w', encoding='utf-8') as f:
            f.write(code)
        return 0
    return 1

def test_gold():
    with open("prompt_lab/cartridges/ms_fabric/gold_layer.md", 'r', encoding='utf-8') as f:
        prompt = f.read()
    
    response = requests.post(f"{API_BASE}/transpile/task",
        json={"node_data": {"layer": "gold", "tech_id": "fabric", "cartridge_prompt": prompt},
              "context": {"project_id": PROJECT_ID}},
        headers={"X-Tenant-ID": TENANT_ID, "X-User-ID": USER_ID}, timeout=120
    )
    
    if response.status_code == 200:
        code = response.json().get("final_code", response.json().get("code", ""))
        with open("prompt_lab/TEST_OUTPUT_MS_FABRIC_GOLD_01.py", 'w', encoding='utf-8') as f:
            f.write(code)
        return 0
    return 1

if __name__ == "__main__":
    print("TEST: FABRIC-SILVER-01")
    result = test_silver()
    print("✅ PASS" if result == 0 else "❌ FAIL")
    exit(result)

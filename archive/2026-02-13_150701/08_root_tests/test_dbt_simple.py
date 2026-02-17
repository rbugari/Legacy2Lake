"""
Simple dbt test - minimal version to debug
"""
import requests
import json

API_BASE = "http://localhost:8085"
TENANT_ID = "daac0ee6-3b28-412d-8acd-43ec51149188"
PROJECT_ID = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"
USER_ID = "daac0ee6-3b28-412d-8acd-43ec51149188"

# Read dbt prompt
with open("prompt_lab/cartridges/dbt/bronze_layer.md", 'r', encoding='utf-8') as f:
    bronze_prompt = f.read()

print(f"✅ Loaded dbt Bronze prompt: {len(bronze_prompt)} chars")

node_data = {
    "name": "dbt_source_customers",
    "label": "dbt - Source Definition Customers",
    "layer": "bronze",
    "tech_id": "dbt",
    "cartridge_prompt": bronze_prompt,
    "project_id": PROJECT_ID
}

context = {
    "project_id": PROJECT_ID,
    "solution_name": "test_dbt"
}

payload = {"node_data": node_data, "context": context}
headers = {
    "Content-Type": "application/json",
    "X-Tenant-ID": TENANT_ID,
    "X-User-ID": USER_ID
}

print("\n📤 Sending request...")
try:
    response = requests.post(
        f"{API_BASE}/transpile/task",
        json=payload,
        headers=headers,
        timeout=60
    )
    
    print(f"\n📥 Response Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
    
    if response.status_code == 200:
        result = response.json()
        final_code = result.get("final_code", "")
        print(f"\n✅ SUCCESS! Generated {len(final_code)} characters")
        print(f"First 200 chars:\n{final_code[:200]}")
    else:
        print(f"\n❌ ERROR: {response.text}")
        
except Exception as e:
    print(f"\n💥 EXCEPTION: {type(e).__name__}: {str(e)}")

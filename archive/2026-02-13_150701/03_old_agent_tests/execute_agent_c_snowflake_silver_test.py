"""Test Snowflake Silver"""
import os, json, requests
from dotenv import load_dotenv
load_dotenv()

API_BASE = "http://localhost:8085"
TENANT_ID = "daac0ee6-3b28-412d-8acd-43ec51149188"
PROJECT_ID = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"
USER_ID = TENANT_ID

def execute_test():
    print("TEST: SNOWFLAKE-SILVER-01")
    with open("prompt_lab/cartridges/snowflake/silver_layer.md", 'r', encoding='utf-8') as f:
        prompt = f.read()
    
    node_data = {
        "name": "silver_customers_sf",
        "layer": "silver",
        "tech_id": "snowflake",
        "primary_keys": ["customer_key"],
        "dedup_column": "_ingestion_timestamp",
        "cartridge_prompt": prompt
    }
    
    response = requests.post(f"{API_BASE}/transpile/task",
        json={"node_data": node_data, "context": {"project_id": PROJECT_ID}},
        headers={"X-Tenant-ID": TENANT_ID, "X-User-ID": USER_ID},
        timeout=120
    )
    
    if response.status_code == 200:
        code = response.json().get("final_code", response.json().get("code", ""))
        with open("prompt_lab/TEST_OUTPUT_SNOWFLAKE_SILVER_01.sql", 'w', encoding='utf-8') as f:
            f.write(code)
        print(f"✅ PASS - {len(code.splitlines())} lines")
        return 0
    else:
        print(f"❌ FAIL - {response.status_code}")
        return 1

if __name__ == "__main__":
    exit(execute_test())

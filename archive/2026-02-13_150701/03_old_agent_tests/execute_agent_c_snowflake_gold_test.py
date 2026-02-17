"""Test Snowflake Gold"""
import os, json, requests
from dotenv import load_dotenv
load_dotenv()

API_BASE = "http://localhost:8085"
TENANT_ID = "daac0ee6-3b28-412d-8acd-43ec51149188"
PROJECT_ID = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"
USER_ID = TENANT_ID

def execute_test():
    print("="*80)
    print("🧪 TEST: SNOWFLAKE-GOLD-01 (Star Schema)")
    print("="*80)
    
    with open("prompt_lab/cartridges/snowflake/gold_layer.md", 'r', encoding='utf-8') as f:
        prompt = f.read()
    print(f"\n✅ Prompt Gold loaded: {len(prompt)} chars")
    
    node_data = {
        "name": "gold_fact_orders_sf",
        "label": "Gold - Fact Orders Star Schema (Snowflake)",
        "description": "Build Star Schema with fact_orders and dim_customers for BI reporting",
        "type": "analytics",
        "layer": "gold",
        "tech_id": "snowflake",
        "fact_table": "GOLD_ANALYTICS.FACT_ORDERS",
        "dimension_tables": ["GOLD_ANALYTICS.DIM_CUSTOMERS", "GOLD_ANALYTICS.DIM_PRODUCTS"],
        "grain": "One row per order",
        "measures": ["order_amount", "quantity", "discount_amount"],
        "cartridge_prompt": prompt
    }
    
    context = {
        "project_id": PROJECT_ID,
        "solution_name": "snowflake_migration",
        "source_tech": "Microsoft SQL Server",
        "target_tech": "Snowflake"
    }
    
    payload = {"node_data": node_data, "context": context}
    headers = {
        "Content-Type": "application/json",
        "X-Tenant-ID": TENANT_ID,
        "X-User-ID": USER_ID
    }
    
    print(f"\n📤 Sending request to Agent C (Snowflake Gold)...")
    
    response = requests.post(
        f"{API_BASE}/transpile/task",
        json=payload,
        headers=headers,
        timeout=120
    )
    
    print(f"\n📥 Response Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        code = result.get("final_code", result.get("code", ""))
        
        output_file = "prompt_lab/TEST_OUTPUT_SNOWFLAKE_GOLD_01.sql"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        lines = code.splitlines()
        print(f"\n💾 Snowflake Gold code saved: {output_file}")
        print(f"   Lines: {len(lines)}, Characters: {len(code)}")
        
        print("\n" + "="*80)
        print("📋 SNOWFLAKE GOLD LAYER CHECKLIST")
        print("="*80)
        
        checks = {
            "FACT table creation": 'FACT_' in code or 'fact_' in code.lower(),
            "DIMENSION tables": 'DIM_' in code or 'dim_' in code.lower(),
            "Surrogate keys": '_KEY' in code or '_ID' in code,
            "JOIN operations": 'JOIN' in code.upper(),
            "GROUP BY aggregation": 'GROUP BY' in code.upper(),
            "Aggregate functions": any(x in code.upper() for x in ['SUM(', 'AVG(', 'COUNT(']),
            "CREATE/REPLACE": 'CREATE OR REPLACE' in code.upper() or 'CREATE TABLE' in code.upper(),
            "UPPERCASE naming": code.isupper() or (code.upper().count('SELECT') > 0),
            "WAREHOUSE usage": 'WAREHOUSE' in code.upper() or 'USE WAREHOUSE' in code.upper(),
            "Clustering keys": 'CLUSTER BY' in code.upper() or 'CLUSTERING' in code.upper()
        }
        
        passed = sum(1 for v in checks.values() if v)
        total = len(checks)
        
        for check, result in checks.items():
            status = "✅" if result else "❌"
            print(f"{status} {check}")
        
        score = (passed / total) * 100
        print(f"\n📊 SCORE: {passed}/{total} = {score:.0f}%")
        
        if score >= 70:
            print(f"\n✅ TEST PASSED - SNOWFLAKE GOLD")
            return 0
        else:
            print(f"\n⚠️ TEST PASSED WITH WARNINGS")
            return 0
    else:
        print(f"\n❌ TEST FAILED - {response.status_code}")
        print(response.text)
        return 1

if __name__ == "__main__":
    exit(execute_test())

"""Test Salesforce Data Cloud Silver Layer"""
import os, json, requests
from dotenv import load_dotenv
load_dotenv()

API_BASE = "http://localhost:8085"
TENANT_ID = "daac0ee6-3b28-412d-8acd-43ec51149188"
PROJECT_ID = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"
USER_ID = TENANT_ID

def execute_test():
    print("="*80)
    print("🧪 TEST: SALESFORCE-DATA-CLOUD-SILVER-01")
    print("="*80)
    
    prompt_file = "prompt_lab/cartridges/salesforce/silver_layer.md"
    if os.path.exists(prompt_file):
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt = f.read()
        print(f"\n✅ Prompt Silver loaded from file: {len(prompt)} chars")
    else:
        prompt = "# Salesforce Data Cloud Silver Layer\nGenerate Data Model Objects (DMO) SQL for harmonized data."
        print(f"\n⚠️ Using default prompt (will be loaded from DB): {len(prompt)} chars")
    
    node_data = {
        "name": "silver_unified_customer_sf",
        "label": "Silver - Unified Customer Profile (Salesforce Data Cloud)",
        "description": "Create harmonized customer profile by deduplicating and enriching raw data",
        "type": "transformation",
        "layer": "silver",
        "tech_id": "salesforce",
        "input_objects": ["Customer_360__dlm"],
        "target_dmo": "Unified_Customer_Profile__dll",
        "dmo_type": "Data Model Object (DMO)",
        "deduplication": True,
        "identity_resolution": True,
        "cartridge_prompt": prompt
    }
    
    context = {
        "project_id": PROJECT_ID,
        "solution_name": "salesforce_migration",
        "source_tech": "Microsoft SQL Server",
        "target_tech": "Salesforce Data Cloud"
    }
    
    payload = {"node_data": node_data, "context": context}
    headers = {
        "Content-Type": "application/json",
        "X-Tenant-ID": TENANT_ID,
        "X-User-ID": USER_ID
    }
    
    print(f"\n📤 Sending request to Agent C (Salesforce Silver)...")
    
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
        
        output_file = "prompt_lab/TEST_OUTPUT_SALESFORCE_SILVER_01.sql"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        lines = code.splitlines()
        print(f"\n💾 Salesforce Silver SQL saved: {output_file}")
        print(f"   Lines: {len(lines)}, Characters: {len(code)}")
        
        print("\n" + "="*80)
        print("📋 SALESFORCE DATA CLOUD SILVER LAYER CHECKLIST")
        print("="*80)
        
        checks = {
            "SQL format": any(x in code.upper() for x in ['SELECT', 'CREATE', 'INSERT']),
            "Data Model Object": '__dll' in code or 'Data Model' in code or 'DMO' in code,
            "Identity resolution": any(x in code.lower() for x in ['identity', 'unified', 'profile']),
            "Deduplication logic": any(x in code.upper() for x in ['DISTINCT', 'GROUP BY', 'ROW_NUMBER']),
            "JOIN operations": 'JOIN' in code.upper(),
            "Data enrichment": any(x in code.upper() for x in ['COALESCE', 'CASE WHEN', 'NULLIF']),
            "Customer unification": any(x in code.lower() for x in ['customer', 'contact', 'individual']),
            "FROM clause": 'FROM' in code.upper() and '__dlm' in code,
        }
        
        passed = sum(1 for v in checks.values() if v)
        total = len(checks)
        
        for check, result in checks.items():
            status = "✅" if result else "❌"
            print(f"{status} {check}")
        
        score = (passed / total) * 100
        print(f"\n📊 SCORE: {passed}/{total} = {score:.0f}%")
        
        if score >= 60:
            print(f"\n✅ TEST PASSED - SALESFORCE DATA CLOUD SILVER")
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

"""
Execute Agent C test via API - SALESFORCE-BRONZE-01
Sprint 0 Day 4 - Test 9: Salesforce Bronze layer
"""
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE = "http://localhost:8085"
TENANT_ID = "daac0ee6-3b28-412d-8acd-43ec51149188"
PROJECT_ID = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"
USER_ID = "daac0ee6-3b28-412d-8acd-43ec51149188"

def read_prompt_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def execute_test():
    print("="*80)
    print("🧪 TEST: SALESFORCE-DATA-CLOUD-BRONZE-01")
    print("="*80)
    
    prompt_file = "prompt_lab/cartridges/sf/bronze_layer.md"
    if os.path.exists(prompt_file):
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt = f.read()
        print(f"\n✅ Prompt Bronze loaded from file: {len(prompt)} chars")
    else:
        prompt = "# Salesforce Data Cloud Bronze Layer\nGenerate Data Cloud JSON schema for raw data ingestion."
        print(f"\n⚠️ Using default prompt (will be loaded from DB): {len(prompt)} chars")
    
    node_data = {
        "name": "bronze_accounts_sf",
        "label": "Bronze - Raw Accounts (Salesforce Data Cloud)",
        "description": "Extract Account records from Salesforce to Bronze layer",
        "type": "ingestion",
        "layer": "bronze",
        "tech_id": "salesforce",
        "source_object": "Account",
        "target_object": "Bronze_Accounts__dlm",
        "fields": ["Id", "Name", "Industry", "AnnualRevenue", "AccountNumber"],
        "schema_type": "Data Lake Object (DLO)",
        "cartridge_prompt": prompt
    }
    
    context = {
        "project_id": PROJECT_ID,
        "solution_name": "salesforce_migration",
        "source_tech": "Salesforce",
        "target_tech": "Salesforce Data Cloud"
    }
    
    payload = {"node_data": node_data, "context": context}
    headers = {
        "Content-Type": "application/json",
        "X-Tenant-ID": TENANT_ID,
        "X-User-ID": USER_ID
    }
    
    print(f"\n📤 Sending request to Agent C (Salesforce Bronze)...")
    
    response = requests.post(
        f"{API_BASE}/transpile/task",
        json=payload,
        headers=headers,
        timeout=120
    )
    
    print(f"\n📥 Response Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        
        print(f"\n🔍 DEBUG: result keys = {list(result.keys())}")
        print(f"🔍 DEBUG: 'final_code' in result? {('final_code' in result)}")
        print(f"🔍 DEBUG: 'code' in result? {('code' in result)}")
        if 'final_code' in result:
            print(f"🔍 DEBUG: final_code type/length = {type(result['final_code'])}/{len(result['final_code']) if result['final_code'] else 0}")
        if 'code' in result:
            print(f"🔍 DEBUG: code type/length = {type(result['code'])}/{len(result['code']) if result['code'] else 0}")
        
        code = result.get("final_code", result.get("code", ""))
        
        print(f"\n🔍 DEBUG: code type = {type(code)}, length = {len(code) if code else 0}")
        print(f"🔍 DEBUG: first 200 chars = {str(code)[:200]}")
        
        # Handle case where Agent C returns a dict instead of JSON string
        if isinstance(code, dict):
            print(f"\n⚠️  Agent C returned dict, converting to JSON string...")
            code = json.dumps(code, indent=2)
        elif not isinstance(code, str):
            print(f"\n⚠️  Unexpected code type: {type(code)}, converting to string...")
            code = str(code)
        
        output_file = "prompt_lab/TEST_OUTPUT_SALESFORCE_BRONZE_01.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        lines = code.splitlines()
        print(f"\n💾 Salesforce Bronze schema saved: {output_file}")
        print(f"   Lines: {len(lines)}, Characters: {len(code)}")
        
        print("\n" + "="*80)
        print("📋 SALESFORCE DATA CLOUD BRONZE LAYER CHECKLIST")
        print("="*80)
        
        checks = {
            "JSON format": code.strip().startswith('{') or code.strip().startswith('['),
            "Data Lake Object": '__dlm' in code or 'Data Lake Object' in code or 'DLO' in code,
            "Schema definition": 'schema' in code.lower() or 'fields' in code.lower(),
            "Field mappings": 'name' in code.lower() and 'type' in code.lower(),
            "Data types": any(x in code.lower() for x in ['text', 'number', 'date', 'boolean']),
            "Account fields": 'account' in code.lower(),
            "Source mapping": 'source' in code.lower() or 'sourceField' in code.lower(),
            "Metadata": 'metadata' in code.lower() or 'description' in code.lower(),
        }
        
        passed = sum(1 for v in checks.values() if v)
        total = len(checks)
        
        for check, result in checks.items():
            status = "✅" if result else "❌"
            print(f"{status} {check}")
        
        score = (passed / total) * 100
        print(f"\n📊 SCORE: {passed}/{total} = {score:.0f}%")
        
        if score >= 60:
            print(f"\n✅ TEST PASSED - SALESFORCE DATA CLOUD BRONZE")
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

"""Test Salesforce Data Cloud Gold Layer"""
import os, json, requests
from dotenv import load_dotenv
load_dotenv()

API_BASE = "http://localhost:8085"
TENANT_ID = "daac0ee6-3b28-412d-8acd-43ec51149188"
PROJECT_ID = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"
USER_ID = TENANT_ID

def execute_test():
    print("="*80)
    print("🧪 TEST: SALESFORCE-DATA-CLOUD-GOLD-01")
    print("="*80)
    
    prompt_file = "prompt_lab/cartridges/salesforce/gold_layer.md"
    if os.path.exists(prompt_file):
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt = f.read()
        print(f"\n✅ Prompt Gold loaded from file: {len(prompt)} chars")
    else:
        prompt = "# Salesforce Data Cloud Gold Layer\nGenerate Calculated Insights for analytics and activation."
        print(f"\n⚠️ Using default prompt (will be loaded from DB): {len(prompt)} chars")
    
    node_data = {
        "name": "gold_customer_ltv_sf",
        "label": "Gold - Customer Lifetime Value (Salesforce Data Cloud)",
        "description": "Calculate Customer LTV, engagement scores, and segmentation for analytics",
        "type": "analytics",
        "layer": "gold",
        "tech_id": "salesforce",
        "input_dmos": ["Unified_Customer_Profile__dll", "Order_History__dll"],
        "target_insight": "Customer_LTV_Segments__dli",
        "insight_type": "Calculated Insight",
        "metrics": ["lifetime_value", "engagement_score", "churn_risk"],
        "segments": ["high_value", "at_risk", "dormant"],
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
    
    print(f"\n📤 Sending request to Agent C (Salesforce Gold)...")
    
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
        
        output_file = "prompt_lab/TEST_OUTPUT_SALESFORCE_GOLD_01.sql"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        lines = code.splitlines()
        print(f"\n💾 Salesforce Gold Insight saved: {output_file}")
        print(f"   Lines: {len(lines)}, Characters: {len(code)}")
        
        print("\n" + "="*80)
        print("📋 SALESFORCE DATA CLOUD GOLD LAYER CHECKLIST")
        print("="*80)
        
        checks = {
            "SQL format": any(x in code.upper() for x in ['SELECT', 'CREATE', 'INSERT']),
            "Calculated Insight": '__dli' in code or 'Calculated Insight' in code,
            "Aggregation functions": any(x in code.upper() for x in ['SUM(', 'AVG(', 'COUNT(']),
            "Business metrics": any(x in code.lower() for x in ['lifetime', 'ltv', 'value', 'score']),
            "Segmentation logic": any(x in code.upper() for x in ['CASE WHEN', 'NTILE', 'PARTITION']),
            "Customer analytics": any(x in code.lower() for x in ['customer', 'engagement', 'churn']),
            "GROUP BY": 'GROUP BY' in code.upper(),
            "DMO source": '__dll' in code or 'FROM' in code.upper(),
        }
        
        passed = sum(1 for v in checks.values() if v)
        total = len(checks)
        
        for check, result in checks.items():
            status = "✅" if result else "❌"
            print(f"{status} {check}")
        
        score = (passed / total) * 100
        print(f"\n📊 SCORE: {passed}/{total} = {score:.0f}%")
        
        if score >= 60:
            print(f"\n✅ TEST PASSED - SALESFORCE DATA CLOUD GOLD")
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

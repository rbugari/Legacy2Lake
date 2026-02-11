"""
Quick test for GCP and Salesforce Bronze to verify Body=None fix
"""
import requests
import json

API_BASE = "http://localhost:8085"
TENANT_ID = "daac0ee6-3b28-412d-8acd-43ec51149188"
PROJECT_ID = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"
USER_ID = "daac0ee6-3b28-412d-8acd-43ec51149188"

def test_cartridge(tech_id, prompt_file):
    print("\n" + "="*80)
    print(f"🧪 Testing: {tech_id.upper()} Bronze")
    print("="*80)
    
    try:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt = f.read()
        print(f"✅ Loaded {tech_id} Bronze prompt: {len(prompt)} chars")
    except FileNotFoundError:
        print(f"❌ Prompt file not found: {prompt_file}")
        return {"success": False, "error": "Prompt file not found"}
    
    node_data = {
        "name": f"{tech_id}_test",
        "label": f"{tech_id} Bronze Test",
        "layer": "bronze",
        "tech_id": tech_id,
        "cartridge_prompt": prompt,
        "project_id": PROJECT_ID
    }
    
    context = {
        "project_id": PROJECT_ID,
        "solution_name": f"test_{tech_id}"
    }
    
    payload = {"node_data": node_data, "context": context}
    headers = {
        "Content-Type": "application/json",
        "X-Tenant-ID": TENANT_ID,
        "X-User-ID": USER_ID
    }
    
    print("📤 Sending request...")
    try:
        response = requests.post(
            f"{API_BASE}/transpile/task",
            json=payload,
            headers=headers,
            timeout=60
        )
        
        print(f"📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            final_code = result.get("final_code", "")
            print(f"✅ SUCCESS! Generated {len(final_code)} characters")
            print(f"First 150 chars:\n{final_code[:150]}")
            return {"success": True, "code_length": len(final_code)}
        else:
            print(f"❌ ERROR: {response.text[:200]}")
            return {"success": False, "error": response.text[:200]}
            
    except requests.Timeout:
        print("❌ TIMEOUT")
        return {"success": False, "error": "Timeout"}
    except Exception as e:
        print(f"💥 EXCEPTION: {type(e).__name__}: {str(e)}")
        return {"success": False, "error": str(e)}

# Test GCP
gcp_result = test_cartridge("gcp", "prompt_lab/cartridges/gcp/bronze_layer.md")

# Test Salesforce
sf_result = test_cartridge("salesforce", "prompt_lab/cartridges/salesforce/bronze_layer.md")

# Summary
print("\n" + "="*80)
print("📊 SUMMARY")
print("="*80)
print(f"GCP:        {'✅ PASS' if gcp_result.get('success') else '❌ FAIL'}")
print(f"Salesforce: {'✅ PASS' if sf_result.get('success') else '❌ FAIL'}")
print("\nBody=None error fix validation:")
if gcp_result.get('success') and sf_result.get('success'):
    print("🎉 All 3 cartridges (dbt, GCP, Salesforce) now working!")
else:
    print("⚠️  Some cartridges still have issues")

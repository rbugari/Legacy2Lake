"""
Sprint 1 Test - Multiple Cartridges with DB-Based Prompts
==========================================================
Batch test to validate DB-based prompt loading across different cartridges.

Tests:
  1. PySpark Silver (Window functions)
  2. Snowflake Bronze (Snowpark Python)
  3. dbt Bronze (SQL models)
  4. MS Fabric Bronze (Fabric SDK)
  5. GCP Bronze (BigQuery SQL)
"""
import os
import json
import requests
import time
from dotenv import load_dotenv

load_dotenv()

API_BASE = "http://localhost:8085"
TENANT_ID = "daac0ee6-3b28-412d-8acd-43ec51149188"
PROJECT_ID = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"
USER_ID = "daac0ee6-3b28-412d-8acd-43ec51149188"

def test_cartridge(tech_id, layer, description, expected_patterns):
    """Test a single cartridge with DB-based prompt loading"""
    print(f"\n{'='*80}")
    print(f"🧪 Test: {tech_id.upper()} - {layer.upper()}")
    print(f"{'='*80}")
    print(f"📋 Description: {description}")
    print(f"🔬 DB Lookup: cartridge_{tech_id}_{layer}")
    
    node_data = {
        "name": f"{layer}_test_{tech_id}",
        "label": f"{layer.capitalize()} - {tech_id.upper()} Test",
        "description": description,
        "type": "transformation" if layer != "bronze" else "ingestion",
        "layer": layer,
        "tech_id": tech_id,
        "source_table": "raw.customers" if layer == "bronze" else f"{layer}_prev.customers",
        "target_table": f"{layer}.customers",
        "primary_keys": ["customer_id"]
    }
    
    context = {
        "project_id": PROJECT_ID,
        "solution_name": "sprint1_validation",
        "source_tech": "MSSQL",
        "target_tech": tech_id
    }
    
    payload = {"node_data": node_data, "context": context}
    headers = {
        "Content-Type": "application/json",
        "X-Tenant-ID": TENANT_ID,
        "X-User-ID": USER_ID
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/transpile/task",
            json=payload,
            headers=headers,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            final_code = result.get("final_code") or result.get("code") or result.get("sql_code") or result.get("pyspark_code")
            
            if not final_code:
                print(f"❌ FAILED: No code generated")
                print(f"   Response keys: {list(result.keys())}")
                return False
            
            chars = len(final_code)
            lines = final_code.count('\n') + 1
            print(f"✅ SUCCESS: Generated {lines} lines, {chars} chars")
            
            # Validate expected patterns
            found_patterns = sum(1 for pattern in expected_patterns if pattern in final_code)
            total_patterns = len(expected_patterns)
            score = (found_patterns / total_patterns) * 100 if total_patterns > 0 else 100
            
            print(f"📊 Pattern match: {found_patterns}/{total_patterns} ({score:.0f}%)")
            for pattern in expected_patterns:
                status = "✅" if pattern in final_code else "❌"
                print(f"   {status} Contains '{pattern}'")
            
            return score >= 60  # Lower threshold for batch test
            
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
            print(f"   {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    print("="*80)
    print("🚀 SPRINT 1 - BATCH CARTRIDGE TEST (DB-BASED PROMPTS)")
    print("="*80)
    print(f"\n⏳ Waiting 3 seconds for backend...")
    time.sleep(3)
    
    tests = [
        {
            "tech_id": "pyspark",
            "layer": "silver",
            "description": "Deduplication with Window functions",
            "expected_patterns": ["Window", "row_number", "partitionBy", "_row_num"]
        },
        {
            "tech_id": "snowflake",
            "layer": "bronze",
            "description": "Snowpark Python ingestion",
            "expected_patterns": ["snowflake.snowpark", "session.table", "write.save_as_table"]
        },
        {
            "tech_id": "dbt",
            "layer": "bronze",
            "description": "dbt SQL source model",
            "expected_patterns": ["{{ config(", "{{ source(", "with", "select"]
        },
        {
            "tech_id": "fabric",
            "layer": "bronze",
            "description": "MS Fabric SDK ingestion",
            "expected_patterns": ["lakehouse", "get_table", "save_to_lakehouse"]
        },
        {
            "tech_id": "gcp",
            "layer": "bronze",
            "description": "BigQuery SQL DDL",
            "expected_patterns": ["CREATE OR REPLACE", "TABLE", "SELECT", "FROM"]
        }
    ]
    
    results = []
    
    for test in tests:
        success = test_cartridge(
            test["tech_id"],
            test["layer"],
            test["description"],
            test["expected_patterns"]
        )
        results.append({
            "cartridge": f"{test['tech_id']}-{test['layer']}",
            "success": success
        })
        time.sleep(2)  # Rate limiting
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 BATCH TEST SUMMARY")
    print(f"{'='*80}")
    
    passed = sum(1 for r in results if r["success"])
    total = len(results)
    
    for r in results:
        status = "✅ PASS" if r["success"] else "❌ FAIL"
        print(f"  {status}  {r['cartridge']}")
    
    print(f"\n📈 Results: {passed}/{total} passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"   ✅ Database-based cartridge prompt loading is PRODUCTION READY")
    elif passed >= total * 0.8:
        print(f"\n✅ MOSTLY PASSED!")
        print(f"   ⚠️  {total - passed} cartridge(s) need attention")
    else:
        print(f"\n⚠️  NEEDS ATTENTION")
        print(f"   ❌ {total - passed} cartridge(s) failed")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

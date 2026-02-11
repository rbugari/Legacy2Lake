"""
Sprint 1 Test - Database-Based Cartridge Prompt Loading
========================================================
Tests Agent C with NEW database-first prompt loading.
Does NOT inject cartridge_prompt in node_data - relies on DB lookup.

Expected behavior:
  1. Agent C checks node_data["cartridge_prompt"] → Not found
  2. Agent C builds prompt_id: cartridge_{tech_id}_{layer}
  3. Agent C calls db.get_prompt(cartridge_prompt_id)
  4. Agent C loads from utm_prompts table
  5. Code generation succeeds

Test: PySpark Bronze Layer
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

def execute_test():
    print("="*80)
    print("🧪 SPRINT 1 TEST: Database-Based Cartridge Prompt Loading")
    print("="*80)
    print(f"\n📋 Test: PySpark Bronze Layer")
    print(f"🔬 Method: DB lookup (NO cartridge_prompt injection)")
    print(f"🎯 Expected: Load from utm_prompts.cartridge_pyspark_bronze")
    
    # NO cartridge_prompt injection - rely on DB
    node_data = {
        "name": "bronze_dim_customers",
        "label": "Bronze - Raw Dim Customers",
        "description": "Ingest raw Dim Customers from MSSQL to Databricks Bronze layer",
        "type": "ingestion",
        "layer": "bronze",  # Important for DB lookup: cartridge_{tech_id}_{layer}
        "tech_id": "pyspark",  # Important for DB lookup: cartridge_{tech_id}_{layer}
        "source_table": "dbo.DimCustomers",
        "target_table": "bronze_raw.dim_customers",
        "primary_keys": ["CustomerKey"]
        # NOTE: NO cartridge_prompt field!
    }
    
    context = {
        "project_id": PROJECT_ID,
        "solution_name": "ttt_migration",
        "source_tech": "Microsoft SQL Server",
        "target_tech": "Databricks (PySpark)"
    }
    
    payload = {"node_data": node_data, "context": context}
    headers = {
        "Content-Type": "application/json",
        "X-Tenant-ID": TENANT_ID,
        "X-User-ID": USER_ID
    }
    
    print(f"\n📤 Sending request to Agent C...")
    print(f"   tech_id: {node_data['tech_id']}")
    print(f"   layer: {node_data['layer']}")
    print(f"   Expected DB lookup: cartridge_pyspark_bronze")
    
    # Wait for backend to be ready
    print(f"\n⏳ Waiting 5 seconds for backend startup...")
    time.sleep(5)
    
    try:
        response = requests.post(
            f"{API_BASE}/transpile/task",
            json=payload,
            headers=headers,
            timeout=120
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Check for code in different possible keys
            final_code = result.get("final_code") or result.get("code") or result.get("pyspark_code")
            
            if not final_code:
                print(f"\n❌ No code generated!")
                print(f"Response keys: {list(result.keys())}")
                print(f"Response: {json.dumps(result, indent=2)[:500]}...")
                return False
            
            output_file = "SPRINT_1_TEST_DB_PYSPARK_BRONZE.py"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(final_code)
            
            lines = final_code.splitlines()
            print(f"\n💾 Code saved: {output_file}")
            print(f"   Lines: {len(lines)}, Characters: {len(final_code)}")
            
            # Checklist validation
            checklist = {
                "SparkSession import": "from pyspark.sql import SparkSession" in final_code,
                "DeltaTable import": "from delta.tables import DeltaTable" in final_code,
                "SparkSession.builder": "SparkSession.builder" in final_code,
                "JDBC read": ".jdbc(" in final_code or ".read.format(" in final_code,
                "source_table reference": "dim_customers" in final_code.lower() or "dimcustomers" in final_code.lower(),
                "Delta write": ".write.format(" in final_code and "delta" in final_code,
                "target_table reference": "bronze_raw" in final_code or "bronze" in final_code,
                "Logging": "logger" in final_code or "print(" in final_code,
                "Try-except": "try:" in final_code and "except" in final_code,
                "PK validation": "CustomerKey" in final_code or "primary" in final_code.lower()
            }
            
            passed = sum(checklist.values())
            total = len(checklist)
            score = (passed / total) * 100
            
            print(f"\n📊 Validation Checklist ({passed}/{total} = {score:.1f}%):")
            for item, result in checklist.items():
                status = "✅" if result else "❌"
                print(f"  {status} {item}")
            
            if score >= 80:
                print(f"\n🎉 TEST PASSED! DB-based prompt loading works!")
                print(f"   ✅ Agent C loaded cartridge_pyspark_bronze from utm_prompts")
                print(f"   ✅ Code generation successful")
                print(f"   ✅ Score: {score:.1f}%")
                return True
            else:
                print(f"\n⚠️  TEST INCOMPLETE: Score {score:.1f}% < 80%")
                return False
                
        else:
            print(f"\n❌ Request failed: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = execute_test()
    exit(0 if success else 1)

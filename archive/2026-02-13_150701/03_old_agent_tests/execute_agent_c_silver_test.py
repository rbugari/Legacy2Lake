"""
Execute Agent C test via API - PYSPARK-SILVER-01 (Deduplication)
Sprint 0 Day 4 - Test 2: Silver layer with window functions
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
    print("🧪 EJECUTANDO TEST: PYSPARK-SILVER-01 (Deduplication)")
    print("="*80)
    
    silver_prompt = read_prompt_file("prompt_lab/cartridges/pyspark/silver_layer.md")
    print(f"\n✅ Prompt Silver cargado: {len(silver_prompt)} caracteres")
    
    node_data = {
        "name": "silver_dim_customers",
        "label": "Silver - DimCustomers Deduplication",
        "description": "Deduplicate Bronze DimCustomers using window functions, keep latest by _ingestion_timestamp",
        "type": "transformation",
        "layer": "silver",
        "tech_id": "pyspark",
        "source_table": "bronze_raw.dim_customers",
        "target_table": "silver_clean.dim_customers",
        "primary_keys": ["CustomerKey"],
        "dedup_column": "_ingestion_timestamp",
        "cartridge_prompt": silver_prompt
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
    
    print(f"\n📤 Enviando request a Agent C (Silver)...")
    
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
            final_code = result.get("final_code", "")
            
            output_file = "prompt_lab/TEST_OUTPUT_PYSPARK_SILVER_01.py"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(final_code)
            
            lines = final_code.splitlines()
            print(f"\n💾 Código Silver guardado: {output_file}")
            print(f"   Líneas: {len(lines)}, Caracteres: {len(final_code)}")
            
            print("\n📄 Primeras 50 líneas:")
            print("-"*80)
            for i, line in enumerate(lines[:50], 1):
                print(f"{i:3d} | {line}")
            if len(lines) > 50:
                print(f"... ({len(lines) - 50} líneas más)")
            
            print("\n" + "="*80)
            print("📋 CHECKLIST SILVER LAYER")
            print("="*80)
            
            checks = {
                "Window.partitionBy()": 'Window.partitionBy(' in final_code or 'window.partitionBy(' in final_code,
                "orderBy(_ingestion_timestamp)": '_ingestion_timestamp' in final_code and 'orderBy(' in final_code,
                "row_number() window function": 'row_number()' in final_code,
                "Filter _row_num == 1": '_row_num' in final_code and ('== 1' in final_code or '= 1' in final_code),
                "DeltaTable.forName().merge()": 'DeltaTable' in final_code and 'merge(' in final_code,
                "MERGE for incremental": 'merge(' in final_code or 'mode("overwrite")' not in final_code,
                "Bronze audit columns preserved": '_ingestion_timestamp' in final_code and '_source_system' in final_code,
                "Delta Lake format": '.format("delta")' in final_code or 'format("delta")' in final_code,
                "saveAsTable()": '.saveAsTable(' in final_code,
                "Try/except": 'try:' in final_code and 'except' in final_code,
                "Logging": 'logging' in final_code or 'logger' in final_code,
                "from pyspark.sql.window": 'Window' in final_code,
                ".withColumn()": '.withColumn(' in final_code,
                "Primary key deduplication": 'CustomerKey' in final_code or 'primary' in final_code.lower(),
                "Quality checks": 'assert' in final_code or 'count()' in final_code
            }
            
            passed = sum(checks.values())
            total = len(checks)
            
            for check, result in checks.items():
                status = "✅" if result else "❌"
                print(f"{status} {check}")
            
            print("\n" + "="*80)
            print(f"🎯 SCORE: {passed}/{total} ({passed/total*100:.1f}%)")
            print("="*80)
            
            if passed >= total * 0.8:
                print("\n🎉 TEST PASSED! Silver deduplication cumple >= 80%")
            else:
                print("\n⚠️  TEST NEEDS REVIEW")
            
            critic = result.get("critic", {})
            if critic:
                print("\n" + "="*80)
                print("🔍 AGENT F CRITIQUE")
                print("="*80)
                print(f"Status: {critic.get('status')}")
                print(f"Score: {critic.get('score')}/10")
                if critic.get('critique'):
                    print("\nFeedback:")
                    for i, c in enumerate(critic.get('critique', [])[:5], 1):
                        print(f"  {i}. {c}")
            
            return {
                "success": True,
                "score": passed / total,
                "passed_checks": passed,
                "total_checks": total,
                "code_file": output_file,
                "code_lines": len(lines)
            }
        
        else:
            print(f"\n❌ ERROR: {response.status_code}")
            print(response.text)
            return {"success": False, "error": response.text}
    
    except Exception as e:
        print(f"\n💥 EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    result = execute_test()
    print("\n" + "="*80)
    print("📊 RESULTADO SILVER-01")
    print("="*80)
    print(json.dumps(result, indent=2))

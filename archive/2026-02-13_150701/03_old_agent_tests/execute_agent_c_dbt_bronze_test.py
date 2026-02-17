"""
Execute Agent C test via API - DBT-BRONZE-01 (Source definitions)
Sprint 0 Day 4 - Test 5: dbt Bronze layer
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
    print("🧪 EJECUTANDO TEST: DBT-BRONZE-01 (Source Definitions)")
    print("="*80)
    
    bronze_prompt = read_prompt_file("prompt_lab/cartridges/dbt/bronze_layer.md")
    print(f"\n✅ Prompt dbt Bronze cargado: {len(bronze_prompt)} caracteres")
    
    node_data = {
        "name": "dbt_source_customers",
        "label": "dbt - Source Definition Customers",
        "description": "Define dbt source for raw customers table with freshness checks",
        "type": "source",
        "layer": "bronze",
        "tech_id": "dbt",
        "source_schema": "raw_data",
        "source_table": "customers",
        "freshness": "24 hours",
        "cartridge_prompt": bronze_prompt
    }
    
    context = {
        "project_id": PROJECT_ID,
        "solution_name": "ttt_migration",
        "source_tech": "PostgreSQL",
        "target_tech": "dbt Core"
    }
    
    payload = {"node_data": node_data, "context": context}
    headers = {
        "Content-Type": "application/json",
        "X-Tenant-ID": TENANT_ID,
        "X-User-ID": USER_ID
    }
    
    print(f"\n📤 Enviando request a Agent C (dbt Bronze)...")
    
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
            
            output_file = "prompt_lab/TEST_OUTPUT_DBT_BRONZE_01.sql"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(final_code)
            
            lines = final_code.splitlines()
            print(f"\n💾 Código dbt guardado: {output_file}")
            print(f"   Líneas: {len(lines)}, Caracteres: {len(final_code)}")
            
            print("\n📄 Primeras 50 líneas:")
            print("-"*80)
            for i, line in enumerate(lines[:50], 1):
                print(f"{i:3d} | {line}")
            if len(lines) > 50:
                print(f"... ({len(lines) - 50} líneas más)")
            
            print("\n" + "="*80)
            print("📋 CHECKLIST DBT BRONZE (SQL Model)")
            print("="*80)
            
            checks = {
                "{{ config() }} block": '{{ config(' in final_code or '{{config(' in final_code,
                "materialized='view'": "materialized='view'" in final_code or 'materialized="view"' in final_code,
                "schema='bronze'": "schema='bronze'" in final_code or "schema='staging'" in final_code or 'schema="bronze"' in final_code,
                "{{ source() }} usage": '{{ source(' in final_code or '{{source(' in final_code,
                "CTE pattern (with...as)": 'with ' in final_code.lower() and ' as (' in final_code.lower(),
                "Audit column (_ingested_at)": '_ingested_at' in final_code or '_loaded_at' in final_code,
                "current_timestamp()": 'current_timestamp()' in final_code.lower() or 'now()' in final_code.lower(),
                "from source": 'from source' in final_code.lower(),
                "select * from": 'select ' in final_code.lower() and ' from ' in final_code.lower(),
                "_source_system column": '_source_system' in final_code or '_source' in final_code,
                "Jinja comments {# #}": '{#' in final_code and '#}' in final_code,
                "L2L trace comment": 'L2L' in final_code or 'Legacy2Lake' in final_code,
                "SQL code (correct format)": 'SELECT' in final_code.upper() or 'select' in final_code.lower(),
                "renamed CTE": 'renamed as' in final_code.lower() or 'staging as' in final_code.lower(),
                "Proper indentation": '  ' in final_code or '    ' in final_code
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
                print("\n🎉 TEST PASSED! dbt Bronze >= 80%")
            else:
                print("\n⚠️  TEST NEEDS REVIEW")
            
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
    print("📊 RESULTADO DBT-BRONZE-01")
    print("="*80)
    print(json.dumps(result, indent=2))

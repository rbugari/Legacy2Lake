"""
Execute Agent C test via API - SNOWFLAKE-BRONZE-01 (Snowpark ingestion)
Sprint 0 Day 4 - Test 4: Snowflake Bronze layer
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
    print("🧪 EJECUTANDO TEST: SNOWFLAKE-BRONZE-01 (Snowpark Ingestion)")
    print("="*80)
    
    bronze_prompt = read_prompt_file("prompt_lab/cartridges/snowflake/bronze_layer.md")
    print(f"\n✅ Prompt Snowflake Bronze cargado: {len(bronze_prompt)} caracteres")
    
    node_data = {
        "name": "bronze_customers_snowflake",
        "label": "Bronze - Raw Customers (Snowflake)",
        "description": "Ingest raw CSV from S3 to Snowflake RAW_DATA schema with COPY INTO",
        "type": "ingestion",
        "layer": "bronze",
        "tech_id": "snowflake",
        "source_table": "@CUSTOMER_STAGE/customers.csv",
        "target_table": "RAW_DATA.BRONZE_CUSTOMERS",
        "columns": ["CUSTOMER_KEY", "CUSTOMER_ID", "NAME", "EMAIL", "REGION"],
        "cartridge_prompt": bronze_prompt
    }
    
    context = {
        "project_id": PROJECT_ID,
        "solution_name": "ttt_migration",
        "source_tech": "Amazon S3",
        "target_tech": "Snowflake (Snowpark)"
    }
    
    payload = {"node_data": node_data, "context": context}
    headers = {
        "Content-Type": "application/json",
        "X-Tenant-ID": TENANT_ID,
        "X-User-ID": USER_ID
    }
    
    print(f"\n📤 Enviando request a Agent C (Snowflake Bronze)...")
    
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
            
            output_file = "prompt_lab/TEST_OUTPUT_SNOWFLAKE_BRONZE_01.sql"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(final_code)
            
            lines = final_code.splitlines()
            print(f"\n💾 Código Snowflake guardado: {output_file}")
            print(f"   Líneas: {len(lines)}, Caracteres: {len(final_code)}")
            
            print("\n📄 Primeras 60 líneas:")
            print("-"*80)
            for i, line in enumerate(lines[:60], 1):
                print(f"{i:3d} | {line}")
            if len(lines) > 60:
                print(f"... ({len(lines) - 60} líneas más)")
            
            print("\n" + "="*80)
            print("📋 CHECKLIST SNOWFLAKE BRONZE")
            print("="*80)
            
            checks = {
                "COPY INTO statement": 'COPY INTO' in final_code,
                "FROM @STAGE pattern": '@' in final_code and 'FROM' in final_code,
                "FILE_FORMAT": 'FILE_FORMAT' in final_code,
                "CSV type": 'CSV' in final_code or 'TYPE = CSV' in final_code,
                "UPPERCASE objects": final_code.count(final_code.upper()) > len(final_code) * 0.3,
                "Metadata columns": '_INGESTION_TIMESTAMP' in final_code or 'METADATA$' in final_code,
                "CREATE OR REPLACE": 'CREATE OR REPLACE' in final_code or 'CREATE TABLE IF NOT EXISTS' in final_code,
                "Schema qualification": 'RAW_DATA.' in final_code or any(s in final_code for s in ['SCHEMA', 'DATABASE']),
                "ON_ERROR": 'ON_ERROR' in final_code,
                "Column mapping": 'FROM @' in final_code and '(' in final_code,
                "File format options": 'SKIP_HEADER' in final_code or 'FIELD_DELIMITER' in final_code,
                "Audit timestamp": 'CURRENT_TIMESTAMP()' in final_code or '_INGESTION_TIMESTAMP' in final_code,
                "Comment/trace": '-- L2L' in final_code or 'COMMENT' in final_code,
                "Transaction safety": 'BEGIN' in final_code or 'COPY INTO' in final_code,
                "Validation query": 'SELECT COUNT(*)' in final_code or 'VALIDATION_MODE' in final_code
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
                print("\n🎉 TEST PASSED! Snowflake Bronze >= 80%")
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
    print("📊 RESULTADO SNOWFLAKE-BRONZE-01")
    print("="*80)
    print(json.dumps(result, indent=2))

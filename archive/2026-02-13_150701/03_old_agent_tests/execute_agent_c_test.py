"""
Execute Agent C test via API - PYSPARK-BRONZE-01
Sprint 0 Day 4 - First automated test
"""
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE = "http://localhost:8085"

# Test configuration
TENANT_ID = "daac0ee6-3b28-412d-8acd-43ec51149188"  # demo3
PROJECT_ID = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"  # ttt
USER_ID = "daac0ee6-3b28-412d-8acd-43ec51149188"    # demo3 user

def read_prompt_file(path):
    """Read the cartridge prompt file"""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def execute_agent_c_test():
    print("="*80)
    print("🧪 EJECUTANDO TEST: PYSPARK-BRONZE-01")
    print("="*80)
    
    # Read the Bronze layer prompt
    bronze_prompt = read_prompt_file("prompt_lab/cartridges/pyspark/bronze_layer.md")
    print(f"\n✅ Prompt cargado: {len(bronze_prompt)} caracteres")
    
    # Construct the node_data (simulates a Bronze layer task)
    node_data = {
        "name": "bronze_dim_customers",
        "label": "Bronze - DimCustomers",
        "description": "Ingest DimCustomers from SQL Server SSIS to Databricks Delta Lake Bronze layer",
        "type": "source",
        "layer": "bronze",
        "tech_id": "pyspark",
        "source_system": "SSIS_MIGRATION",
        "source_table": "dbo.DimCustomers",
        "target_table": "bronze_raw.dim_customers",
        "columns": [
            {"name": "CustomerKey", "type": "INT"},
            {"name": "CustomerID", "type": "VARCHAR(50)"},
            {"name": "Name", "type": "VARCHAR(100)"},
            {"name": "Email", "type": "VARCHAR(100)"},
            {"name": "Region", "type": "VARCHAR(50)"}
        ],
        "cartridge_prompt": bronze_prompt  # Inject the cartridge prompt
    }
    
    # Context
    context = {
        "project_id": PROJECT_ID,
        "solution_name": "ttt_migration",
        "source_tech": "Microsoft SQL Server",
        "target_tech": "Databricks (PySpark)"
    }
    
    # API Request payload
    payload = {
        "node_data": node_data,
        "context": context
    }
    
    # Headers (simulate authenticated user)
    headers = {
        "Content-Type": "application/json",
        "X-Tenant-ID": TENANT_ID,
        "X-User-ID": USER_ID
    }
    
    print("\n📤 Enviando request a Agent C...")
    print(f"   Endpoint: {API_BASE}/transpile/task")
    print(f"   Tenant: {TENANT_ID}")
    print(f"   Project: {PROJECT_ID}")
    
    try:
        response = requests.post(
            f"{API_BASE}/transpile/task",
            json=payload,
            headers=headers,
            timeout=120  # 2 minutes max
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n✅ Agent C EJECUTADO EXITOSAMENTE")
            print("="*80)
            
            # Extract generated code
            final_code = result.get("final_code", "")
            interpreter_result = result.get("interpreter", {})
            critic_result = result.get("critic", {})
            
            # Save generated code
            output_file = "prompt_lab/TEST_OUTPUT_PYSPARK_BRONZE_01.py"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(final_code)
            
            print(f"\n💾 Código generado guardado en: {output_file}")
            print(f"   Líneas: {len(final_code.splitlines())}")
            print(f"   Caracteres: {len(final_code)}")
            
            # Show first 50 lines of generated code
            lines = final_code.splitlines()
            print("\n📄 Primeras 50 líneas del código generado:")
            print("-"*80)
            for i, line in enumerate(lines[:50], 1):
                print(f"{i:3d} | {line}")
            if len(lines) > 50:
                print(f"... ({len(lines) - 50} líneas más)")
            
            # Validation checklist
            print("\n" + "="*80)
            print("📋 CHECKLIST DE VALIDACIÓN AUTOMÁTICA")
            print("="*80)
            
            checks = {
                "Delta Lake format": '.format("delta")' in final_code or 'format("delta")' in final_code,
                "saveAsTable()": '.saveAsTable(' in final_code,
                "partitionBy()": '.partitionBy(' in final_code and '_ingestion_date' in final_code,
                "Append mode": 'mode("append")' in final_code or "mode='append'" in final_code,
                "_ingestion_timestamp": '_ingestion_timestamp' in final_code,
                "_ingestion_date": '_ingestion_date' in final_code,
                "_source_file": '_source_file' in final_code,
                "_source_system": '_source_system' in final_code,
                "JDBC read": '.jdbc(' in final_code or 'jdbc' in final_code.lower(),
                "Try/except": 'try:' in final_code and 'except' in final_code,
                "Logging": 'logging' in final_code or 'logger' in final_code,
                "Delta imports": 'from delta' in final_code or 'import delta' in final_code,
                ".withColumn()": '.withColumn(' in final_code,
                "current_timestamp()": 'current_timestamp()' in final_code,
                "lit()": 'lit(' in final_code
            }
            
            passed = sum(checks.values())
            total = len(checks)
            
            for check, result in checks.items():
                status = "✅" if result else "❌"
                print(f"{status} {check}")
            
            print("\n" + "="*80)
            print(f"🎯 SCORE: {passed}/{total} ({passed/total*100:.1f}%)")
            print("="*80)
            
            if passed >= total * 0.8:  # 80% pass rate
                print("\n🎉 TEST PASSED! El código cumple con >= 80% de requisitos")
            else:
                print("\n⚠️  TEST NEEDS REVIEW - Score bajo del 80%")
            
            # Critic feedback
            if critic_result:
                print("\n" + "="*80)
                print("🔍 FEEDBACK DE AGENT F (CRITIC)")
                print("="*80)
                print(json.dumps(critic_result, indent=2))
            
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
    
    except requests.exceptions.Timeout:
        print("\n⏰ TIMEOUT: Agent C tardó más de 2 minutos")
        return {"success": False, "error": "timeout"}
    
    except Exception as e:
        print(f"\n💥 EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    result = execute_agent_c_test()
    
    print("\n" + "="*80)
    print("📊 RESULTADO FINAL")
    print("="*80)
    print(json.dumps(result, indent=2))

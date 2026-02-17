"""
Execute Agent C test via API - PYSPARK-GOLD-01 (Star Schema)
Sprint 0 Day 4 - Test 3: Gold layer dimensional model
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
    print("🧪 EJECUTANDO TEST: PYSPARK-GOLD-01 (Star Schema)")
    print("="*80)
    
    gold_prompt = read_prompt_file("prompt_lab/cartridges/pyspark/gold_layer.md")
    print(f"\n✅ Prompt Gold carg ado: {len(gold_prompt)} caracteres")
    
    node_data = {
        "name": "gold_fact_orders",
        "label": "Gold - Fact Orders Star Schema",
        "description": "Build Star Schema with fact_orders and dim_customers for BI reporting",
        "type": "analytics",
        "layer": "gold",
        "tech_id": "pyspark",
        "fact_table": "gold_analytics.fact_orders",
        "dimension_tables": ["gold_analytics.dim_customers"],
        "grain": "One row per order",
        "measures": ["order_amount", "quantity"],
        "cartridge_prompt": gold_prompt
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
    
    print(f"\n📤 Enviando request a Agent C (Gold)...")
    
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
            
            output_file = "prompt_lab/TEST_OUTPUT_PYSPARK_GOLD_01.py"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(final_code)
            
            lines = final_code.splitlines()
            print(f"\n💾 Código Gold guardado: {output_file}")
            print(f"   Líneas: {len(lines)}, Caracteres: {len(final_code)}")
            
            print("\n📄 Primeras 50 líneas:")
            print("-"*80)
            for i, line in enumerate(lines[:50], 1):
                print(f"{i:3d} | {line}")
            if len(lines) > 50:
                print(f"... ({len(lines) - 50} líneas más)")
            
            print("\n" + "="*80)
            print("📋 CHECKLIST GOLD LAYER")
            print("="*80)
            
            checks = {
                "FACT table creation": 'fact_' in final_code.lower() or 'FACT' in final_code,
                "DIMENSION table": 'dim_' in final_code.lower() or 'DIMENSION' in final_code,
                "Surrogate keys": 'key' in final_code.lower() and ('BIGINT' in final_code or 'bigint' in final_code or 'long' in final_code),
                "Foreign key relationship": 'join' in final_code.lower() or 'JOIN' in final_code,
                ".groupBy() aggregation": '.groupBy(' in final_code or '.group_by(' in final_code,
                "SUM/AVG/COUNT aggregate": any(x in final_code for x in ['sum(', 'SUM(', 'avg(', 'AVG(', 'count(', 'COUNT(']),
                "SCD Type 2 columns": 'effective' in final_code.lower() or 'valid_from' in final_code.lower() or 'is_current' in final_code.lower(),
                "Delta Lake format": '.format("delta")' in final_code or 'format("delta")' in final_code,
                "saveAsTable()": '.saveAsTable(' in final_code,
                "Try/except": 'try:' in final_code and 'except' in final_code,
                "Logging": 'logging' in final_code or 'logger' in final_code,
                ".withColumn()": '.withColumn(' in final_code,
                "Date dimension": 'date' in final_code.lower() and ('dim_' in final_code.lower() or 'DIMENSION' in final_code),
                "Business metrics": 'amount' in final_code.lower() or 'revenue' in final_code.lower() or 'sales' in final_code.lower(),
                "Grain documentation": 'grain' in final_code.lower() or '# One row per' in final_code or 'One row per' in final_code
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
                print("\n🎉 TEST PASSED! Gold Star Schema cumple >= 80%")
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
    print("📊 RESULTADO GOLD-01")
    print("="*80)
    print(json.dumps(result, indent=2))

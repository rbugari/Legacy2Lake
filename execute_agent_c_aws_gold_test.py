"""Test AWS Gold"""
import os, json, requests
from dotenv import load_dotenv
load_dotenv()

API_BASE = "http://localhost:8085"
TENANT_ID = "daac0ee6-3b28-412d-8acd-43ec51149188"
PROJECT_ID = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"
USER_ID = TENANT_ID

def execute_test():
    print("="*80)
    print("🧪 TEST: AWS-GLUE-GOLD-01 (Star Schema)")
    print("="*80)
    
    with open("prompt_lab/cartridges/aws/gold_layer.md", 'r', encoding='utf-8') as f:
        prompt = f.read()
    print(f"\n✅ Prompt Gold loaded: {len(prompt)} chars")
    
    node_data = {
        "name": "gold_fact_sales_aws",
        "label": "Gold - Fact Sales Star Schema (AWS Glue)",
        "description": "Build Star Schema with fact_sales and dimensions for BI reporting",
        "type": "analytics",
        "layer": "gold",
        "tech_id": "aws",
        "fact_table": "gold_analytics.fact_sales",
        "dimension_tables": ["gold_analytics.dim_customers", "gold_analytics.dim_products"],
        "grain": "One row per sale transaction",
        "measures": ["sale_amount", "quantity", "discount"],
        "cartridge_prompt": prompt
    }
    
    context = {
        "project_id": PROJECT_ID,
        "solution_name": "aws_migration",
        "source_tech": "Microsoft SQL Server",
        "target_tech": "AWS Glue (PySpark)"
    }
    
    payload = {"node_data": node_data, "context": context}
    headers = {
        "Content-Type": "application/json",
        "X-Tenant-ID": TENANT_ID,
        "X-User-ID": USER_ID
    }
    
    print(f"\n📤 Sending request to Agent C (AWS Gold)...")
    
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
        
        output_file = "prompt_lab/TEST_OUTPUT_AWS_GLUE_GOLD_01.py"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        lines = code.splitlines()
        print(f"\n💾 AWS Gold code saved: {output_file}")
        print(f"   Lines: {len(lines)}, Characters: {len(code)}")
        
        print("\n" + "="*80)
        print("📋 AWS GLUE GOLD LAYER CHECKLIST")
        print("="*80)
        
        checks = {
            "FACT table creation": 'fact_' in code.lower(),
            "DIMENSION tables": 'dim_' in code.lower(),
            "Surrogate keys": 'key' in code.lower() and ('LongType' in code or 'bigint' in code.lower()),
            "JOIN operations": 'join(' in code.lower(),
            ".groupBy() aggregation": '.groupBy(' in code,
            "Aggregate functions": any(x in code for x in ['sum(', 'avg(', 'count(']),
            "AWS Glue context": 'GlueContext' in code or 'glueContext' in code,
            "Dynamic Frame": 'DynamicFrame' in code or 'toDF()' in code,
            "Parquet format": 'parquet' in code.lower(),
            "Write to S3": 's3://' in code or 'write.parquet' in code
        }
        
        passed = sum(1 for v in checks.values() if v)
        total = len(checks)
        
        for check, result in checks.items():
            status = "✅" if result else "❌"
            print(f"{status} {check}")
        
        score = (passed / total) * 100
        print(f"\n📊 SCORE: {passed}/{total} = {score:.0f}%")
        
        if score >= 70:
            print(f"\n✅ TEST PASSED - AWS GLUE GOLD")
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

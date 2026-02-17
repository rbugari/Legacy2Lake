"""
Execute Agent C test via API - GCP BIGQUERY-BRONZE-01
Sprint 0 Day 4 - Test 7: GCP BigQuery Bronze layer
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
    print("TEST: GCP BIGQUERY-BRONZE-01 (Standard SQL Ingestion)")
    print("="*80)
    
    bronze_prompt = read_prompt_file("prompt_lab/cartridges/gcp/bronze_layer.md")
    print(f"\nPrompt BigQuery Bronze: {len(bronze_prompt)} caracteres")
    
    node_data = {
        "name": "bronze_customers_bq",
        "label": "Bronze - Raw Customers (BigQuery)",
        "description": "Ingest CSV from GCS to BigQuery Bronze dataset",
        "type": "ingestion",
        "layer": "bronze",
        "tech_id": "gcp",
        "source_table": "gs://bucket/customers.csv",
        "target_table": "bronze_raw.customers",
        "columns": ["customer_key", "customer_id", "name", "email", "region"],
        "cartridge_prompt": bronze_prompt
    }
    
    context = {
        "project_id": PROJECT_ID,
        "solution_name": "ttt_migration",
        "source_tech": "Google Cloud Storage",
        "target_tech": "Google BigQuery"
    }
    
    payload = {"node_data": node_data, "context": context}
    headers = {
        "Content-Type": "application/json",
        "X-Tenant-ID": TENANT_ID,
        "X-User-ID": USER_ID
    }
    
    print(f"\nEnviando request a Agent C (BigQuery Bronze)...")
    
    try:
        response = requests.post(
            f"{API_BASE}/transpile/task",
            json=payload,
            headers=headers,
            timeout=120
        )
        
        print(f"\nResponse Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            final_code = result.get("final_code", result.get("code", ""))
            
            output_file = "prompt_lab/TEST_OUTPUT_GCP_BIGQUERY_BRONZE_01.sql"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(final_code)
            
            lines = final_code.splitlines()
            print(f"\nCodigo guardado: {output_file}")
            print(f"Lineas: {len(lines)}, Caracteres: {len(final_code)}")
            
            print("\nPrimeras 50 lineas:")
            print("-"*80)
            for i, line in enumerate(lines[:50], 1):
                print(f"{i:3d} | {line}")
            if len(lines) > 50:
                print(f"... ({len(lines) - 50} lineas mas)")
            
            # Quick check
            checks = {
                "BigQuery syntax": "CREATE OR REPLACE TABLE" in final_code or "CREATE TABLE" in final_code,
                "LOAD DATA or SELECT": "LOAD DATA" in final_code or "SELECT" in final_code,
                "Standard SQL": "SELECT" in final_code or "FROM" in final_code,
                "GCS path": "gs://" in final_code,
                "Bronze dataset": "bronze" in final_code.lower()
            }
            passed = sum(checks.values())
            total = len(checks)
            
            print(f"\nQuick checks: {passed}/{total}")
            for k, v in checks.items():
                print(f"  {'✓' if v else '✗'} {k}")
            
            return {
                "success": True,
                "score": passed / total,
                "code_file": output_file,
                "code_lines": len(lines)
            }
        
        else:
            print(f"\nERROR: {response.status_code}")
            print(response.text)
            return {"success": False, "error": response.text}
    
    except Exception as e:
        print(f"\nEXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    result = execute_test()
    print("\n" + "="*80)
    print("RESULTADO GCP-BIGQUERY-BRONZE-01")
    print("="*80)
    print(json.dumps(result, indent=2))

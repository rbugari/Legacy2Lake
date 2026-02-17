"""
Execute Agent C test via API - MS FABRIC-BRONZE-01 (Lakehouse ingestion)
Sprint 0 Day 4 - Test 6: MS Fabric Bronze layer
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
    print("TEST: MS FABRIC-BRONZE-01 (Lakehouse Ingestion)")
    print("="*80)
    
    bronze_prompt = read_prompt_file("prompt_lab/cartridges/ms_fabric/bronze_layer.md")
    print(f"\nPrompt MS Fabric Bronze cargado: {len(bronze_prompt)} caracteres")
    
    node_data = {
        "name": "bronze_customers_fabric",
        "label": "Bronze - Raw Customers (MS Fabric)",
        "description": "Ingest CSV from ADLS to Fabric Lakehouse Bronze layer",
        "type": "ingestion",
        "layer": "bronze",
        "tech_id": "fabric",
        "source_table": "adls://customers.csv",
        "target_table": "bronze_customers",
        "columns": ["customer_key", "customer_id", "name", "email", "region"],
        "cartridge_prompt": bronze_prompt
    }
    
    context = {
        "project_id": PROJECT_ID,
        "solution_name": "ttt_migration",
        "source_tech": "Azure Data Lake Storage",
        "target_tech": "Microsoft Fabric Lakehouse"
    }
    
    payload = {"node_data": node_data, "context": context}
    headers = {
        "Content-Type": "application/json",
        "X-Tenant-ID": TENANT_ID,
        "X-User-ID": USER_ID
    }
    
    print(f"\nEnviando request a Agent C (MS Fabric Bronze)...")
    
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
            
            output_file = "prompt_lab/TEST_OUTPUT_MS_FABRIC_BRONZE_01.py"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(final_code)
            
            lines = final_code.splitlines()
            print(f"\nCodigo guardado: {output_file}")
            print(f"Lineas: {len(lines)}, Caracteres: {len(final_code)}")
            
            print("\nPrimeras 40 lineas:")
            print("-"*80)
            for i, line in enumerate(lines[:40], 1):
                print(f"{i:3d} | {line}")
            if len(lines) > 40:
                print(f"... ({len(lines) - 40} lineas mas)")
            
            return {
                "success": True,
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
    print("RESULTADO MS FABRIC-BRONZE-01")
    print("="*80)
    print(json.dumps(result, indent=2))

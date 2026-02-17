"""
Ver qué hay dentro de logical_medulla.data_flow_logic
"""
from supabase import create_client, Client
import json

SUPABASE_URL = "https://qdsdfityyxmalyipqbfm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFkc2RmaXR5eXhtYWx5aXBxYmZtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODg2NTczOSwiZXhwIjoyMDg0NDQxNzM5fQ.f4Ge4MPpeDoFLgLSD9e79V2N-ND-aU9YqwNp2VrOgC0"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

project_id = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"

result = supabase.table("utm_objects") \
    .select("object_id, object_name, metadata") \
    .eq("project_id", project_id) \
    .eq("type", "CORE") \
    .limit(1) \
    .execute()

if result.data and len(result.data) > 0:
    obj = result.data[0]
    metadata = obj.get('metadata', {})
    if isinstance(metadata, str):
        metadata = json.loads(metadata)
    
    medulla = metadata.get('logical_medulla', {})
    
    print("\n" + "="*80)
    print("ESTRUCTURA DE LOGICAL_MEDULLA")
    print("="*80)
    
    print(f"\nObject: {obj.get('object_name')}")
    print(f"ID: {obj.get('object_id')}")
    
    print(f"\n📦 Keys en medulla: {list(medulla.keys())}")
    
    if 'data_flow_logic' in medulla:
        dfl = medulla['data_flow_logic']
        print(f"\n📊 data_flow_logic:")
        print(f"   Type: {type(dfl)}")
        
        if isinstance(dfl, dict):
            print(f"   Keys: {list(dfl.keys())}")
            
            # Show first 500 chars of each key
            for key, value in dfl.items():
                print(f"\n   {key}:")
                if isinstance(value, list):
                    print(f"      Type: list ({len(value)} items)")
                    if len(value) > 0:
                        print(f"      First item: {json.dumps(value[0], indent=6)}")
                elif isinstance(value, dict):
                    print(f"      Type: dict")
                    print(f"      Keys: {list(value.keys())}")
                    print(f"      Sample: {json.dumps(value, indent=6)[:500]}...")
                else:
                    print(f"      Type: {type(value)}")
                    print(f"      Value: {str(value)[:500]}...")
        else:
            print(f"   Content: {str(dfl)[:1000]}...")
    
    # Check if there are connection strings anywhere
    medulla_str = json.dumps(medulla)
    if 'Data Source' in medulla_str or 'connection' in medulla_str.lower():
        print(f"\n✅ HAY INFORMACIÓN DE CONEXIÓN en la medulla")
        print(f"   Busca 'Data Source' o 'connection' en el JSON completo")
    
    print("\n" + "="*80)
    print("JSON COMPLETO DE data_flow_logic:")
    print("="*80)
    if 'data_flow_logic' in medulla:
        print(json.dumps(medulla['data_flow_logic'], indent=2))
    
else:
    print("❌ No se encontró objeto CORE")

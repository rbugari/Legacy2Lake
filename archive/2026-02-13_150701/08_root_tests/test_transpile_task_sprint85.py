"""
Simular llamada a transpile_task via API HTTP para debuggear Sprint 8.5
"""
import requests
import json
from supabase import create_client

# Config
API_BASE = "http://127.0.0.1:8085"
SUPABASE_URL = "https://qdsdfityyxmalyipqbfm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFkc2RmaXR5eXhtYWx5aXBxYmZtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODg2NTczOSwiZXhwIjoyMDg0NDQxNzM5fQ.f4Ge4MPpeDoFLgLSD9e79V2N-ND-aU9YqwNp2VrOgC0"

project_id = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"
asset_id = "0f5f8da5-bf6b-4e3e-b55a-a754b2cc5e30"  # CORE object
tenant_id = "daac0ee6-3b28-412d-8acd-43ec51149188"

def test_transpile_task_api():
    """Call transpile endpoint via HTTP"""
    print("\n" + "="*80)
    print("LLAMAR transpile_task VIA HTTP")
    print("="*80)
def test_transpile_task_api():
    """Call transpile endpoint via HTTP"""
    print("\n" + "="*80)
    print("LLAMAR transpile_task VIA HTTP")
    print("="*80)
    
    # Build payload similar to what frontend sends
    payload = {
        "node_data": {
            "project_id": project_id,
            "asset_id": asset_id,
            "object_id": asset_id,
            "tech_id": "pyspark",
            "target_tech": "pyspark",
            "source_tech": "mssql",
            "layer": "bronze"
        },
        "context": {}
    }
    
    print(f"\nPayload:")
    print(json.dumps(payload, indent=2))
    
    print("\n" + "="*80)
    print("POST /transpile/task")
    print("="*80)
    
    try:
        response = requests.post(
            f"{API_BASE}/transpile/task",
            json=payload,
            headers={
                "X-Tenant-ID": tenant_id,
                "Content-Type": "application/json"
            },
            timeout=120
        )
        
        print(f"\nStatus: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ transpile_task COMPLETADO")
            print(f"\nCódigo generado:")
            print(f"   bronze_code: {len(data.get('bronze_code', '')) if data.get('bronze_code') else 0} chars")
            
            # Show first 200 chars
            if data.get('bronze_code'):
                print(f"\n   Preview:")
                print(f"   {data['bronze_code'][:200]}...")
        else:
            print(f"\n❌ ERROR: {response.status_code}")
            print(response.text)
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Backend no está corriendo en {API_BASE}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False
    
    # Verify Sprint 8.5 data was saved
    print("\n" + "="*80)
    print("VERIFICAR SI SPRINT 8.5 GUARDÓ DATOS")
    print("="*80)
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    result = supabase.table("utm_objects") \
        .select("object_id, source_connection, source_type, transformations, complexity_score, data_flow_analysis, updated_at") \
        .eq("object_id", asset_id) \
        .execute()
    
    if result.data and len(result.data) > 0:
        obj = result.data[0]
        
        print(f"\n📊 Datos en utm_objects:")
        print(f"   updated_at: {obj.get('updated_at')}")
        print(f"   source_connection: {'✅ SET' if obj.get('source_connection') else '❌ NULL'}")
        print(f"   source_type: {obj.get('source_type') or '❌ NULL'}")
        print(f"   transformations: {'✅ SET' if obj.get('transformations') else '❌ NULL'}")
        print(f"   complexity_score: {obj.get('complexity_score') if obj.get('complexity_score') is not None else '❌ NULL'}")
        print(f"   data_flow_analysis: {'✅ SET' if obj.get('data_flow_analysis') else '❌ NULL'}")
        
        if obj.get('transformations'):
            trans = json.loads(obj.get('transformations')) if isinstance(obj.get('transformations'), str) else obj.get('transformations')
            print(f"\n   ✅ {len(trans)} transformaciones guardadas:")
            for t in trans:
                print(f"      - {t['type']}: {t['name']}")
        
        if obj.get('transformations') and obj.get('complexity_score') is not None and obj.get('data_flow_analysis'):
            print("\n" + "="*80)
            print("🎉 ÉXITO - Sprint 8.5 se ejecutó automáticamente durante transpile_task")
            print("="*80)
            return True
        else:
            print("\n" + "="*80)
            print("⚠️  PARCIAL - Algunos datos de Sprint 8.5 faltan")
            print("="*80)
            print("\n💡 Tip: Revisa los logs del backend terminal para:")
            print("   [AgentC Sprint8.5] Extracting origin analysis...")
            print("   [AgentC Sprint8.5] ✅ Origin analysis complete...")
            return False
    else:
        print("\n❌ No se pudo recuperar el objeto")
        return False

if __name__ == "__main__":
    success = test_transpile_task_api()
    exit(0 if success else 1)

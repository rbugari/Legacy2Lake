"""
Trigger Triage via HTTP API y luego verificar datos Sprint 8.5
"""
import requests
import json
from supabase import create_client, Client

# Config
API_BASE = "http://127.0.0.1:8085"
PROJECT_ID = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"
TENANT_ID = "daac0ee6-3b28-412d-8acd-43ec51149188"

# Supabase
SUPABASE_URL = "https://qdsdfityyxmalyipqbfm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFkc2RmaXR5eXhtYWx5aXBxYmZtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODg2NTczOSwiZXhwIjoyMDg0NDQxNzM5fQ.f4Ge4MPpeDoFLgLSD9e79V2N-ND-aU9YqwNp2VrOgC0"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def test_origin_analysis_endpoints():
    """Test all 3 Sprint 8.5 endpoints"""
    print("\n" + "="*80)
    print("PROBAR ENDPOINTS SPRINT 8.5")
    print("="*80)
    
    endpoints = [
        f"/projects/{PROJECT_ID}/origin-analysis",
        f"/projects/{PROJECT_ID}/transformations",
        f"/projects/{PROJECT_ID}/source-queries"
    ]
    
    for endpoint in endpoints:
        print(f"\n{'='*80}")
        print(f"GET {endpoint}")
        print(f"{'='*80}")
        
        try:
            response = requests.get(f"{API_BASE}{endpoint}", timeout=10)
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ SUCCESS")
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                print(f"❌ ERROR: {response.status_code}")
                print(response.text)
        
        except requests.exceptions.ConnectionError:
            print(f"❌ ERROR: Backend no está corriendo en {API_BASE}")
            print(f"   Ejecuta: uvicorn main:app --reload --port 8085 --host 0.0.0.0")
            return False
        except Exception as e:
            print(f"❌ ERROR: {e}")
    
    return True

def check_sprint85_data():
    """Check if Sprint 8.5 data exists in database"""
    print("\n" + "="*80)
    print("VERIFICAR DATOS SPRINT 8.5 EN BASE DE DATOS")
    print("="*80)
    
    result = supabase.table("utm_objects") \
        .select("object_id, object_name, source_connection, source_type, transformations, complexity_score, data_flow_analysis") \
        .eq("project_id", PROJECT_ID) \
        .eq("type", "CORE") \
        .limit(1) \
        .execute()
    
    if result.data and len(result.data) > 0:
        obj = result.data[0]
        
        print(f"\nObject ID: {obj.get('object_id')}")
        print(f"Object Name: {obj.get('object_name')}")
        
        has_data = False
        
        if obj.get('source_connection'):
            conn = json.loads(obj.get('source_connection')) if isinstance(obj.get('source_connection'), str) else obj.get('source_connection')
            print(f"\n✅ source_connection: {len(conn)} connections")
            has_data = True
        else:
            print(f"\n❌ source_connection: NULL")
        
        if obj.get('source_type'):
            print(f"✅ source_type: {obj.get('source_type')}")
            has_data = True
        else:
            print(f"❌ source_type: NULL")
        
        if obj.get('transformations'):
            trans = json.loads(obj.get('transformations')) if isinstance(obj.get('transformations'), str) else obj.get('transformations')
            print(f"✅ transformations: {len(trans)} items")
            
            # Show first transformation
            if len(trans) > 0:
                print(f"\n   Primera transformación:")
                print(f"   Type: {trans[0].get('type')}")
                print(f"   Name: {trans[0].get('name')}")
                print(f"   Complexity: {trans[0].get('complexity_factor')}")
            
            has_data = True
        else:
            print(f"❌ transformations: NULL")
        
        if obj.get('complexity_score') is not None:
            print(f"\n✅ complexity_score: {obj.get('complexity_score')}/100")
            has_data = True
        else:
            print(f"❌ complexity_score: NULL")
        
        if obj.get('data_flow_analysis'):
            dfa = json.loads(obj.get('data_flow_analysis')) if isinstance(obj.get('data_flow_analysis'), str) else obj.get('data_flow_analysis')
            print(f"✅ data_flow_analysis:")
            print(f"   Queries: {len(dfa.get('queries', []))}")
            print(f"   Transformations count: {dfa.get('transformations_count', 0)}")
            
            # Show origin
            origin = dfa.get('origin', {})
            if origin:
                print(f"\n   Origin:")
                print(f"   Source type: {origin.get('source_type')}")
                print(f"   Server: {origin.get('server')}")
                print(f"   Database: {origin.get('database')}")
                print(f"   Connections: {len(origin.get('connections', []))}")
            
            has_data = True
        else:
            print(f"❌ data_flow_analysis: NULL")
        
        print("\n" + "="*80)
        if has_data:
            print("✅ HAY DATOS SPRINT 8.5 - Los endpoints deberían funcionar")
            return True
        else:
            print("❌ NO HAY DATOS SPRINT 8.5 - El código no guardó la información")
            print("\nProbablemente el backend no se reinició después de los cambios")
            print("Reinicia uvicorn y vuelve a correr Triage desde el frontend")
            return False
    else:
        print("\n❌ No se encontró objeto CORE en el proyecto")
        return False

if __name__ == "__main__":
    print("\n" + "="*80)
    print("TEST SPRINT 8.5: ORIGIN ANALYSIS DASHBOARD")
    print("="*80)
    
    # First check if data exists
    has_data = check_sprint85_data()
    
    # Then test endpoints
    if has_data:
        test_origin_analysis_endpoints()
    else:
        print("\n⚠️  Necesitas:")
        print("   1. Reiniciar backend (para cargar código actualizado)")
        print("   2. Correr Triage desde frontend")
        print("   3. Volver a ejecutar este script")

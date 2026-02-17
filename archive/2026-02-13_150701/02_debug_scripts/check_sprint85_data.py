"""
Verificar si Sprint 8.5 guardó datos en utm_objects después del Triage
"""
from supabase import create_client, Client
import json

SUPABASE_URL = "https://qdsdfityyxmalyipqbfm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFkc2RmaXR5eXhtYWx5aXBxYmZtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODg2NTczOSwiZXhwIjoyMDg0NDQxNzM5fQ.f4Ge4MPpeDoFLgLSD9e79V2N-ND-aU9YqwNp2VrOgC0"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

project_id = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"

print("\n" + "="*80)
print("VERIFICAR DATOS SPRINT 8.5 DESPUÉS DEL TRIAGE")
print("="*80)

# Get Sprint 8.5 columns data
result = supabase.table("utm_objects") \
    .select("object_name, source_connection, source_type, transformations, complexity_score, data_flow_analysis, source_query, updated_at") \
    .eq("project_id", project_id) \
    .order("updated_at", desc=True) \
    .limit(5) \
    .execute()

if result.data and len(result.data) > 0:
    print(f"\n✅ Encontrados {len(result.data)} objetos en el proyecto\n")
    
    has_data = False
    for idx, obj in enumerate(result.data):
        print(f"\n{'='*80}")
        print(f"OBJETO {idx + 1}: {obj.get('object_name')}")
        print(f"{'='*80}")
        print(f"   Updated: {obj.get('updated_at')}")
        
        # Check each Sprint 8.5 column
        if obj.get('source_connection'):
            has_data = True
            print(f"\n   ✅ source_connection: {obj.get('source_connection')[:200]}...")
        else:
            print(f"   ❌ source_connection: NULL")
        
        if obj.get('source_type'):
            has_data = True
            print(f"   ✅ source_type: {obj.get('source_type')}")
        else:
            print(f"   ❌ source_type: NULL")
        
        if obj.get('transformations'):
            has_data = True
            trans = obj.get('transformations')
            if isinstance(trans, str):
                trans = json.loads(trans)
            print(f"   ✅ transformations: {len(trans) if isinstance(trans, list) else 'N/A'} transformaciones")
        else:
            print(f"   ❌ transformations: NULL")
        
        if obj.get('complexity_score') is not None:
            has_data = True
            print(f"   ✅ complexity_score: {obj.get('complexity_score')}")
        else:
            print(f"   ❌ complexity_score: NULL")
        
        if obj.get('data_flow_analysis'):
            has_data = True
            dfa = obj.get('data_flow_analysis')
            if isinstance(dfa, str):
                dfa = json.loads(dfa)
            print(f"   ✅ data_flow_analysis: {len(str(dfa))} chars")
        else:
            print(f"   ❌ data_flow_analysis: NULL")
        
        if obj.get('source_query'):
            has_data = True
            print(f"   ✅ source_query: {obj.get('source_query')[:100]}...")
        else:
            print(f"   ❌ source_query: NULL")
    
    print("\n" + "="*80)
    if has_data:
        print("✅ HAY DATOS SPRINT 8.5 - Los endpoints deberían funcionar")
    else:
        print("❌ NO HAY DATOS SPRINT 8.5 - El código no guardó la información")
        print("\nPosibles causas:")
        print("   1. El asset no tiene 'logical_medulla' en metadata")
        print("   2. El código de agent_c_service.py no se ejecutó")
        print("   3. Error silencioso en _persist_origin_analysis()")
else:
    print("\n❌ No hay objetos en el proyecto")
    print(f"   project_id: {project_id}")

"""
Verificar si el asset tiene logical_medulla en metadata (prerequisito para Sprint 8.5)
"""
from supabase import create_client, Client
import json

SUPABASE_URL = "https://qdsdfityyxmalyipqbfm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFkc2RmaXR5eXhtYWx5aXBxYmZtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODg2NTczOSwiZXhwIjoyMDg0NDQxNzM5fQ.f4Ge4MPpeDoFLgLSD9e79V2N-ND-aU9YqwNp2VrOgC0"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

project_id = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"

print("\n" + "="*80)
print("VERIFICAR LOGICAL_MEDULLA EN ASSETS")
print("="*80)

# Get assets from utm_objects (Discovery phase)
result = supabase.table("utm_objects") \
    .select("object_id, object_name, type, metadata") \
    .eq("project_id", project_id) \
    .order("updated_at", desc=True) \
    .limit(5) \
    .execute()

if result.data and len(result.data) > 0:
    print(f"\n✅ Encontrados {len(result.data)} objects\n")
    
    for idx, obj in enumerate(result.data):
        print(f"\n{'='*80}")
        print(f"OBJECT {idx + 1}: {obj.get('object_name')}")
        print(f"{'='*80}")
        print(f"   ID: {obj.get('object_id')}")
        print(f"   Type: {obj.get('type')}")
        
        metadata = obj.get('metadata', {})
        if isinstance(metadata, str):
            metadata = json.loads(metadata)
        
        # Check for logical_medulla
        if metadata.get('logical_medulla'):
            medulla = metadata['logical_medulla']
            print(f"\n   ✅ logical_medulla EXISTE")
            print(f"      Tamaño: {len(str(medulla))} chars")
            
            # Check structure
            if isinstance(medulla, dict):
                print(f"      Keys: {list(medulla.keys())}")
                if 'data_flow_logic' in medulla:
                    print(f"      ✅ data_flow_logic presente")
                if 'components' in medulla:
                    print(f"      ✅ components presente ({len(medulla['components'])} componentes)")
            else:
                print(f"      ⚠️ medulla no es dict: {type(medulla)}")
        else:
            print(f"\n   ❌ logical_medulla NO EXISTE")
            print(f"      Metadata keys: {list(metadata.keys())}")
        
        # Check connections
        if metadata.get('connections'):
            connections = metadata['connections']
            print(f"\n   ✅ connections EXISTE ({len(connections)} conexiones)")
        else:
            print(f"\n   ❌ connections NO EXISTE")
    
    print("\n" + "="*80)
    print("CONCLUSIÓN:")
    print("="*80)
    print("Si NO hay logical_medulla, el código Sprint 8.5 NO se ejecutará.")
    print("Discovery (SSISCartridge) debe extraer la medulla primero.")
    
else:
    print("\n❌ No hay objects en utm_objects")
    print(f"   project_id: {project_id}")
    print("\n⚠️ Necesitas correr DISCOVERY primero")

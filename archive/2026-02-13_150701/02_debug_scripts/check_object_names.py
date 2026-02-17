"""
Verificar qué object_name tienen los objetos y si el UPDATE está funcionando
"""
from supabase import create_client, Client
import json

SUPABASE_URL = "https://qdsdfityyxmalyipqbfm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFkc2RmaXR5eXhtYWx5aXBxYmZtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODg2NTczOSwiZXhwIjoyMDg0NDQxNzM5fQ.f4Ge4MPpeDoFLgLSD9e79V2N-ND-aU9YqwNp2VrOgC0"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

project_id = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"

print("\n" + "="*80)
print("VERIFICAR object_name Y object_id EN utm_objects")
print("="*80)

result = supabase.table("utm_objects") \
    .select("object_id, object_name, type, source_path, generated_code") \
    .eq("project_id", project_id) \
    .order("updated_at", desc=True) \
    .execute()

if result.data:
    print(f"\n✅ {len(result.data)} objects en el proyecto\n")
    
    for idx, obj in enumerate(result.data):
        print(f"\n{'='*80}")
        print(f"OBJECT {idx + 1}")
        print(f"{'='*80}")
        print(f"   object_id: {obj.get('object_id')}")
        print(f"   object_name: {obj.get('object_name')}")
        print(f"   type: {obj.get('type')}")
        print(f"   source_path: {obj.get('source_path')}")
        print(f"   has generated_code: {'YES' if obj.get('generated_code') else 'NO'}")
        
        if obj.get('object_name') is None:
            print(f"\n   ⚠️  object_name is NULL - UPDATE podría no funcionar correctamente")
            print(f"   Usa object_id para UPDATE: {obj.get('object_id')}")
    
    print("\n" + "="*80)
    print("RECOMENDACIÓN")
    print("="*80)
    print("Si object_name es NULL, cambia _persist_origin_analysis para usar:")
    print("   .eq('object_id', object_id)  # En lugar de object_name")
else:
    print("❌ No hay objects")

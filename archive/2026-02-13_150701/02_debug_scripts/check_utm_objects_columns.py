"""
Verificar qué columnas tiene utm_objects actualmente
"""
from supabase import create_client, Client

SUPABASE_URL = "https://qdsdfityyxmalyipqbfm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFkc2RmaXR5eXhtYWx5aXBxYmZtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODg2NTczOSwiZXhwIjoyMDg0NDQxNzM5fQ.f4Ge4MPpeDoFLgLSD9e79V2N-ND-aU9YqwNp2VrOgC0"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("\n" + "="*80)
print("COLUMNAS ACTUALES EN utm_objects")
print("="*80)

# Get one row to see all columns
result = supabase.table("utm_objects") \
    .select("*") \
    .limit(1) \
    .execute()

if result.data and len(result.data) > 0:
    columns = list(result.data[0].keys())
    print(f"\n✅ Total columnas: {len(columns)}\n")
    
    for col in sorted(columns):
        print(f"   • {col}")
    
    # Check Sprint 8.5 columns
    sprint85_cols = ['source_connection', 'source_type', 'transformations', 
                      'complexity_score', 'data_flow_analysis', 'source_query']
    
    print("\n" + "="*80)
    print("VERIFICACIÓN SPRINT 8.5")
    print("="*80)
    
    missing = []
    for col in sprint85_cols:
        if col in columns:
            print(f"   ✅ {col}")
        else:
            print(f"   ❌ {col} - NO EXISTE")
            missing.append(col)
    
    if missing:
        print(f"\n⚠️  FALTAN {len(missing)} COLUMNAS - Necesitas ejecutar la migración:")
        print("   migrations/sprint8.5_origin_analysis_columns.sql")
    else:
        print("\n🎉 TODAS las columnas Sprint 8.5 existen!")
else:
    print("❌ No hay datos en utm_objects")

"""
Aplicar actualización retroactiva del esquema directamente a Supabase
"""
import json
import re
from supabase import create_client, Client

# Supabase credentials
SUPABASE_URL = "https://qdsdfityyxmalyipqbfm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFkc2RmaXR5eXhtYWx5aXBxYmZtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODg2NTczOSwiZXhwIjoyMDg0NDQxNzM5fQ.f4Ge4MPpeDoFLgLSD9e79V2N-ND-aU9YqwNp2VrOgC0"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

project_id = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"
object_name = "DimCustomers.dtsx"

print("\n" + "="*60)
print("APLICANDO ACTUALIZACIÓN RETROACTIVA DE ESQUEMA")
print("="*60)

# 1. Get current code from database
print(f"\n📥 Obteniendo código actual de la BD...")
result = supabase.table('utm_objects') \
    .select('generated_code, schema_metadata') \
    .eq('project_id', project_id) \
    .eq('object_name', object_name) \
    .order('updated_at', desc=True) \
    .limit(1) \
    .execute()

if not result.data:
    print(f"❌ No se encontró el objeto en la BD")
    exit(1)

code = result.data[0].get('generated_code', '')
current_schema = result.data[0].get('schema_metadata', {})

print(f"✅ Código obtenido: {len(code)} chars")
print(f"📊 Esquema actual: {len(current_schema.get('columns', []))} columnas")

# 2. Extract schema using Pattern 4
print(f"\n🔍 Extrayendo esquema con Pattern 4...")
pattern4 = r'(?:enforced_schema|schema)\s*=\s*"""(.*?)"""'
match4 = re.search(pattern4, code, re.DOTALL)

columns = []
if match4:
    schema_block = match4.group(1)
    line_pattern = r'^\s*(\w+)\s+([\w\(\)]+)\s*,?\s*$'
    
    for line in schema_block.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        col_match = re.match(line_pattern, line)
        if col_match:
            col_name = col_match.group(1).lower()
            col_type = col_match.group(2).upper()
            columns.append({
                'name': col_name,
                'type': col_type,
                'nullable': True,
                'is_primary_key': False,
                'is_foreign_key': False
            })

if not columns:
    print(f"❌ No se pudieron extraer columnas")
    exit(1)

print(f"✅ Extracción exitosa: {len(columns)} columnas")
for col in columns:
    print(f"   - {col['name']}: {col['type']}")

# 3. Build new schema_metadata
schema_metadata = {
    'table_name': object_name,
    'columns': columns,
    'primary_key': [],
    'foreign_keys': [],
    'row_count': None
}

# 4. Update database
print(f"\n💾 Actualizando base de datos...")
try:
    update_result = supabase.table('utm_objects') \
        .update({
            'schema_metadata': schema_metadata,
            'column_count': len(columns)
        }) \
        .eq('project_id', project_id) \
        .eq('object_name', object_name) \
        .execute()
    
    print(f"✅ Actualización exitosa!")
    print(f"✅ Columnas actualizadas: {len(columns)}")
    
except Exception as e:
    print(f"❌ Error al actualizar: {str(e)}")
    exit(1)

# 5. Verify update
print(f"\n🔍 Verificando actualización...")
verify_result = supabase.table('utm_objects') \
    .select('schema_metadata, column_count') \
    .eq('project_id', project_id) \
    .eq('object_name', object_name) \
    .order('updated_at', desc=True) \
    .limit(1) \
    .execute()

if verify_result.data:
    updated_schema = verify_result.data[0].get('schema_metadata', {})
    updated_count = verify_result.data[0].get('column_count', 0)
    
    print(f"✅ Verificación exitosa:")
    print(f"   - Columnas en schema_metadata: {len(updated_schema.get('columns', []))}")
    print(f"   - column_count: {updated_count}")
    
    if updated_count == len(columns):
        print(f"\n🎉 ¡Actualización completada correctamente!")
        print(f"🔄 Ahora recarga el frontend para ver las 7 columnas en SchemaViewer")
    else:
        print(f"\n⚠️ Advertencia: column_count no coincide")

print("\n" + "="*60)

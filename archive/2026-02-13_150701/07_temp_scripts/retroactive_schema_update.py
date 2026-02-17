"""
Actualizar esquema en la BD usando extracción retroactiva
"""
import requests
import json
import re

project_id = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"

print("\n" + "="*60)
print("ACTUALIZACIÓN RETROACTIVA DE ESQUEMA")
print("="*60)

# 1. Get current code
url_code = f"http://127.0.0.1:8085/projects/{project_id}/generated-code"
print(f"\n📥 Descargando código actual...")
response = requests.get(url_code)

if response.status_code != 200:
    print(f"❌ Error al obtener código: {response.status_code}")
    exit(1)

data = response.json()
code = data.get('code', '')
print(f"✅ Código obtenido: {len(code)} chars")

# 2. Extract schema using Pattern 4
print(f"\n🔍 Extrayendo esquema...")
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

if columns:
    print(f"✅ Extracción exitosa: {len(columns)} columnas")
    for col in columns:
        print(f"   - {col['name']}: {col['type']}")
else:
    print(f"❌ No se pudieron extraer columnas")
    exit(1)

# 3. Build schema_metadata JSON
schema_metadata = {
    'table_name': 'DimCustomers.dtsx',
    'columns': columns,
    'primary_key': [],
    'foreign_keys': [],
    'row_count': None
}

print(f"\n✅ Schema metadata construido:")
print(json.dumps(schema_metadata, indent=2))

# 4. Update database via endpoint
# Note: We'll need to use the internal Supabase update or create a new endpoint
# For now, let's create a test endpoint call

print(f"\n🔄 Para actualizar la BD, ejecuta este SQL en Supabase:")
print(f"\n" + "-"*60)
print(f"""
UPDATE utm_objects 
SET 
    schema_metadata = '{json.dumps(schema_metadata)}'::jsonb,
    column_count = {len(columns)},
    updated_at = NOW()
WHERE project_id = '{project_id}'
  AND object_name = 'DimCustomers.dtsx'
  AND created_at = (
      SELECT MAX(created_at) 
      FROM utm_objects 
      WHERE project_id = '{project_id}' 
        AND object_name = 'DimCustomers.dtsx'
  );
""")
print("-"*60)

print(f"\n💡 O puedes usar el script Python con dotenv para actualizar directamente")

print("\n" + "="*60)

"""
Verificar esquema después de la última ejecución
"""
import os
import sys
from supabase import create_client
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase connection
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

project_id = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"

print("\n" + "="*60)
print("VERIFICACIÓN DE ESQUEMA - ÚLTIMA EJECUCIÓN")
print("="*60)

# Get most recent object
response = supabase.table("utm_objects").select(
    "asset_id, object_name, generated_code, schema_metadata, column_count, created_at"
).eq(
    "project_id", project_id
).order(
    "created_at", desc=True
).limit(1).execute()

if response.data:
    obj = response.data[0]
    print(f"\n📊 Objeto más reciente:")
    print(f"   Asset ID: {obj['asset_id']}")
    print(f"   Nombre: {obj['object_name']}")
    print(f"   Creado: {obj['created_at']}")
    print(f"   Código: {len(obj.get('generated_code', '') or '')} chars")
    print(f"   Columnas: {obj.get('column_count', 0)}")
    
    # Show schema metadata
    schema = obj.get('schema_metadata')
    if schema:
        print(f"\n✅ Schema metadata presente:")
        if isinstance(schema, str):
            schema = json.loads(schema)
        print(f"   Columnas en metadata: {len(schema.get('columns', []))}")
        if schema.get('columns'):
            print(f"\n   Columnas:")
            for col in schema['columns']:
                print(f"      - {col.get('name')}: {col.get('type')}")
    else:
        print(f"\n❌ NO HAY schema_metadata")
    
    # Show first 1000 chars of code to see structure
    code = obj.get('generated_code', '')
    if code:
        print(f"\n📝 Primeros 1000 chars del código:")
        print("-" * 60)
        print(code[:1000])
        print("-" * 60)
        
        # Check for patterns
        print(f"\n🔍 Patrones encontrados en el código:")
        if 'inferred_schema = [' in code:
            print("   ✅ Patrón 1: inferred_schema = [...] ENCONTRADO")
        else:
            print("   ❌ Patrón 1: inferred_schema = [...] NO ENCONTRADO")
        
        if 'StructType([' in code:
            print("   ✅ Patrón 2: StructType([...]) ENCONTRADO")
        else:
            print("   ❌ Patrón 2: StructType([...]) NO ENCONTRADO")
        
        if 'CREATE TABLE' in code:
            print("   ✅ Patrón 3: CREATE TABLE ENCONTRADO")
        else:
            print("   ❌ Patrón 3: CREATE TABLE NO ENCONTRADO")
        
        # Check if columns are mentioned
        target_cols = ['custid', 'contactname', 'city', 'country', 'address', 'phone', 'postalcode']
        cols_found = [col for col in target_cols if col in code]
        print(f"\n   Columnas mencionadas en el código: {cols_found}")
else:
    print("\n❌ No se encontró ningún objeto")

print("\n" + "="*60)

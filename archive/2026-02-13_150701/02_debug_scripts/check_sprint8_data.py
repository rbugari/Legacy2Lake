"""
Revisar qué datos de Sprint 8 (Discovery & Triage) están disponibles
para mostrar análisis del origen
"""
from supabase import create_client, Client
import json

# Supabase credentials
SUPABASE_URL = "https://qdsdfityyxmalyipqbfm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFkc2RmaXR5eXhtYWx5aXBxYmZtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODg2NTczOSwiZXhwIjoyMDg0NDQxNzM5fQ.f4Ge4MPpeDoFLgLSD9e79V2N-ND-aU9YqwNp2VrOgC0"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

project_id = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"

print("\n" + "="*70)
print("COLUMNAS SPRINT 8 (DISCOVERY & TRIAGE) - ANÁLISIS DEL ORIGEN")
print("="*70)

# Get Sprint 8 columns
result = supabase.table('utm_objects') \
    .select('*') \
    .eq('project_id', project_id) \
    .eq('object_name', 'DimCustomers.dtsx') \
    .order('updated_at', desc=True) \
    .limit(1) \
    .execute()

if not result.data:
    print("❌ No se encontró el objeto")
    exit(1)

obj = result.data[0]

print("\n📊 COLUMNAS SPRINT 8 DISPONIBLES:")
print("-"*70)

# Sprint 8 columns
sprint8_cols = {
    'source_connection': 'Conexión origen (OLEDB, ODBC, etc)',
    'source_type': 'Tipo de fuente (SQL Server, Oracle, File, etc)',
    'source_query': 'Query/Tabla origen',
    'transformations': 'Transformaciones detectadas (JSON)',
    'complexity_score': 'Score de complejidad (0-100)',
    'data_flow_analysis': 'Análisis de flujo de datos'
}

has_sprint8_data = False

for col, desc in sprint8_cols.items():
    value = obj.get(col)
    if value:
        has_sprint8_data = True
        print(f"\n✅ {col}:")
        print(f"   Descripción: {desc}")
        if isinstance(value, (dict, list)):
            print(f"   Valor: {json.dumps(value, indent=6)}")
        else:
            print(f"   Valor: {value}")
    else:
        print(f"\n⚠️  {col}: VACÍO")
        print(f"   Descripción: {desc}")

if not has_sprint8_data:
    print("\n" + "="*70)
    print("❌ NO HAY DATOS DE SPRINT 8 (DISCOVERY & TRIAGE)")
    print("="*70)
    print("\n💡 Estos son los datos que deberían mostrarse:")
    print("   - Análisis de conexión origen (tipo, server, database)")
    print("   - Transformaciones detectadas en SSIS (Lookup, Merge, etc)")
    print("   - Complejidad del paquete (simple, medium, complex)")
    print("   - Flujo de datos y dependencias")
    print("   - Queries SQL originales")
    print("\n🎯 PROPUESTA: Dashboard de Discovery & Triage")
    print("   - Origin Analysis: Conexión, tipo, queries")
    print("   - Transformations Matrix: Lista de transformaciones detectadas")
    print("   - Complexity Breakdown: Métricas de complejidad")
    print("   - Dependencies Graph: Dependencias entre objetos")

print("\n" + "="*70)
print("COLUMNAS SPRINT 13 (CÓDIGO GENERADO) - LO QUE TENEMOS AHORA")
print("="*70)

sprint13_cols = {
    'generated_code': 'Código PySpark generado',
    'schema_metadata': 'Esquema extraído del código',
    'quality_metrics': 'Métricas de calidad del código',
    'performance_metrics': 'Métricas de performance del código'
}

for col, desc in sprint13_cols.items():
    value = obj.get(col)
    if value:
        print(f"\n✅ {col}:")
        print(f"   Descripción: {desc}")
        if col == 'generated_code':
            print(f"   Tamaño: {len(value)} chars")
        elif isinstance(value, (dict, list)):
            if col == 'schema_metadata':
                cols = value.get('columns', []) if isinstance(value, dict) else []
                print(f"   Columnas: {len(cols)}")
            else:
                print(f"   Datos: {json.dumps(value, indent=6)}")

print("\n" + "="*70)

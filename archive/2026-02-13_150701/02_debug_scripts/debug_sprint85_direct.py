"""
Debug Sprint 8.5: Ejecutar código de origen analysis directamente
"""
from supabase import create_client, Client
import json
import asyncio

SUPABASE_URL = "https://qdsdfityyxmalyipqbfm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFkc2RmaXR5eXhtYWx5aXBxYmZtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODg2NTczOSwiZXhwIjoyMDg0NDQxNzM5fQ.f4Ge4MPpeDoFLgLSD9e79V2N-ND-aU9YqwNp2VrOgC0"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

project_id = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"
object_id = "0f5f8da5-bf6b-4e3e-b55a-a754b2cc5e30"  # CORE object

print("\n" + "="*80)
print("DEBUG SPRINT 8.5: EJECUTAR CÓDIGO DIRECTAMENTE")
print("="*80)

# Step 1: Get asset with medulla
print("\n[STEP 1] Obtener asset con medulla...")
result = supabase.table("utm_objects") \
    .select("object_id, object_name, metadata") \
    .eq("object_id", object_id) \
    .execute()

if not result.data or len(result.data) == 0:
    print("❌ No se encontró el asset")
    exit(1)

asset = result.data[0]
metadata = asset.get('metadata', {})
if isinstance(metadata, str):
    metadata = json.loads(metadata)

medulla = metadata.get('logical_medulla')
connections = metadata.get('connections', [])

if not medulla:
    print("❌ No hay logical_medulla")
    exit(1)

print(f"✅ Asset encontrado")
print(f"   Medulla size: {len(str(medulla))} chars")
print(f"   Connections: {len(connections)}")

# Step 2: Extract transformations
print("\n[STEP 2] Extraer transformations...")
data_flow = medulla.get("data_flow_logic", [])
print(f"   data_flow_logic type: {type(data_flow)}")
print(f"   data_flow_logic length: {len(data_flow) if isinstance(data_flow, list) else 'N/A'}")

transformations = []
for comp in data_flow:
    comp_type = comp.get("type", "UNKNOWN")
    comp_name = comp.get("name", "")
    raw_props = comp.get("raw_properties", {})
    
    sql_query = None
    for prop_key in ["SqlCommand", "OpenRowset", "TableOrViewName", "SqlStatementSource"]:
        if prop_key in raw_props and raw_props[prop_key]:
            sql_query = raw_props[prop_key][:500]
            break
    
    # Complexity map
    complexity_map = {
        "SOURCE_DB": 2,
        "DESTINATION_DB": 2,
        "LOOKUP": 5,
        "MERGE": 8,
        "DERIVED_COLUMN": 3,
        "AGGREGATE": 6,
        "CONDITIONAL": 4,
        "DATA_CONVERSION": 2,
        "SORT": 3,
        "UNION_ALL": 4,
        "MULTICAST": 3,
        "SCRIPT_COMPONENT": 9,
        "UNKNOWN": 1
    }
    
    transformations.append({
        "type": comp_type,
        "name": comp_name,
        "sql_query": sql_query,
        "complexity_factor": complexity_map.get(comp_type, 1)
    })

print(f"✅ Transformations extraídas: {len(transformations)}")
for t in transformations:
    print(f"   - {t['type']}: {t['name']} (complexity: {t['complexity_factor']})")

# Step 3: Calculate complexity
print("\n[STEP 3] Calcular complexity score...")
if len(transformations) == 0:
    complexity_score = 0
else:
    total_complexity = sum(t['complexity_factor'] for t in transformations)
    avg_complexity = total_complexity / len(transformations)
    complexity_score = int(avg_complexity * 10)
    
    if len(transformations) > 10:
        complexity_score += 20
    
    complexity_score = min(complexity_score, 100)

print(f"✅ Complexity score: {complexity_score}/100")

# Step 4: Extract queries
print("\n[STEP 4] Extraer queries...")
queries = []
for comp in data_flow:
    comp_type = comp.get("type", "")
    if comp_type in ["SOURCE_DB", "LOOKUP"]:
        raw_props = comp.get("raw_properties", {})
        sql = raw_props.get("SqlCommand") or raw_props.get("OpenRowset") or ""
        
        if sql:
            queries.append({
                "component_type": comp_type,
                "component_name": comp.get("name", ""),
                "query": sql,
                "language": "sql"
            })

print(f"✅ Queries extraídas: {len(queries)}")
for q in queries:
    print(f"   - {q['component_type']}: {q['query'][:60]}...")

# Step 5: Extract origin (aunque connections esté vacío)
print("\n[STEP 5] Extraer origin info...")
origin = {
    "source_type": None,
    "server": None,
    "database": None,
    "connections": []
}

if len(connections) > 0:
    print(f"✅ Hay {len(connections)} connections")
else:
    print(f"⚠️  No hay connections - origin será NULL")

# Step 6: Persist
print("\n[STEP 6] Guardar en utm_objects...")
updates = {
    "source_connection": json.dumps(origin.get("connections", [])),
    "source_type": origin.get("source_type"),
    "source_query": queries[0].get("query") if queries else None,
    "transformations": json.dumps(transformations),
    "complexity_score": complexity_score,
    "data_flow_analysis": json.dumps({
        "origin": origin,
        "queries": queries,
        "transformations_count": len(transformations)
    })
}

print(f"   Updates payload:")
print(f"   - source_connection: {len(updates['source_connection'])} chars")
print(f"   - source_type: {updates['source_type']}")
print(f"   - source_query: {updates['source_query'][:60] if updates['source_query'] else 'NULL'}...")
print(f"   - transformations: {len(updates['transformations'])} chars")
print(f"   - complexity_score: {updates['complexity_score']}")
print(f"   - data_flow_analysis: {len(updates['data_flow_analysis'])} chars")

try:
    result = supabase.table("utm_objects") \
        .update(updates) \
        .eq("object_id", object_id) \
        .execute()
    
    print(f"\n✅ UPDATE ejecutado exitosamente")
    print(f"   Affected rows: {len(result.data) if result.data else 0}")
    
    if result.data and len(result.data) > 0:
        updated = result.data[0]
        print(f"\n   Datos actualizados:")
        print(f"   - source_type: {updated.get('source_type')}")
        print(f"   - complexity_score: {updated.get('complexity_score')}")
        print(f"   - transformations: {len(updated.get('transformations', '[]'))} chars")
    
except Exception as e:
    print(f"\n❌ ERROR en UPDATE: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Step 7: Verify
print("\n[STEP 7] Verificar datos guardados...")
result = supabase.table("utm_objects") \
    .select("object_id, source_connection, source_type, transformations, complexity_score, data_flow_analysis") \
    .eq("object_id", object_id) \
    .execute()

if result.data and len(result.data) > 0:
    obj = result.data[0]
    
    print(f"\n✅ DATOS VERIFICADOS:")
    print(f"   source_connection: {'✅ SET' if obj.get('source_connection') else '❌ NULL'}")
    print(f"   source_type: {obj.get('source_type') or '❌ NULL'}")
    print(f"   transformations: {'✅ SET' if obj.get('transformations') else '❌ NULL'}")
    print(f"   complexity_score: {obj.get('complexity_score') if obj.get('complexity_score') is not None else '❌ NULL'}")
    print(f"   data_flow_analysis: {'✅ SET' if obj.get('data_flow_analysis') else '❌ NULL'}")
    
    if obj.get('transformations'):
        trans = json.loads(obj.get('transformations')) if isinstance(obj.get('transformations'), str) else obj.get('transformations')
        print(f"\n   Transformations guardadas: {len(trans)}")
        for t in trans:
            print(f"   - {t['type']}: {t['name']}")
    
    print("\n" + "="*80)
    print("🎉 ÉXITO - Sprint 8.5 funcionó correctamente")
    print("="*80)
else:
    print("\n❌ No se pudo verificar los datos")

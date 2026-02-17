"""
Test schema API - verificar qué devuelve ahora
"""
import requests
import json

project_id = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"

print("\n" + "="*60)
print("TEST SCHEMA API - Estado actual")
print("="*60)

# Test schema endpoint
url = f"http://127.0.0.1:8085/projects/{project_id}/schema"
print(f"\n🔍 Consultando: {url}")

try:
    response = requests.get(url)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ SUCCESS!")
        print(f"\n📊 Respuesta:")
        print(json.dumps(data, indent=2))
        
        # Count columns
        columns = data.get('columns', [])
        print(f"\n📈 Resumen:")
        print(f"   Total columnas: {len(columns)}")
        print(f"   Table name: {data.get('table_name')}")
        print(f"   Row count: {data.get('row_count')}")
        
        if columns:
            print(f"\n   Columnas:")
            for col in columns:
                print(f"      - {col.get('name')}: {col.get('type')}")
        else:
            print(f"\n   ❌ NO HAY COLUMNAS")
    else:
        print(f"\n❌ ERROR: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"\n❌ Exception: {e}")

# Also test generated-code endpoint
print(f"\n" + "-"*60)
url2 = f"http://127.0.0.1:8085/projects/{project_id}/generated-code"
print(f"\n🔍 Consultando: {url2}")

try:
    response2 = requests.get(url2)
    print(f"Status: {response2.status_code}")
    
    if response2.status_code == 200:
        data2 = response2.json()
        print(f"\n✅ Code API works!")
        code = data2.get('code', '')
        print(f"   Code length: {len(code)} chars")
        print(f"   Object name: {data2.get('object_name')}")
        print(f"   Tech ID: {data2.get('tech_id')}")
        
        # Check patterns in code
        print(f"\n🔍 Patrones en el código:")
        if 'inferred_schema = [' in code:
            print("   ✅ inferred_schema = [...] ENCONTRADO")
        else:
            print("   ❌ inferred_schema = [...] NO ENCONTRADO")
        
        if 'StructType([' in code:
            print("   ✅ StructType([...]) ENCONTRADO")
        else:
            print("   ❌ StructType([...]) NO ENCONTRADO")
        
        # Show first 800 chars
        print(f"\n📝 Primeros 800 chars del código:")
        print("-" * 60)
        print(code[:800])
        print("-" * 60)
    else:
        print(f"\n❌ ERROR: {response2.status_code}")
except Exception as e:
    print(f"\n❌ Exception: {e}")

print("\n" + "="*60)

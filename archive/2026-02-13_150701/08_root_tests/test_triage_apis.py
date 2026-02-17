"""
Test Sprint 8.5: Triage Dashboard APIs
Valida los 3 nuevos endpoints para el dashboard de análisis de origen
"""
import requests
import json

API_BASE = "http://127.0.0.1:8085"
PROJECT_ID = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"

def test_apis():
    print("\n" + "="*70)
    print("TEST: TRIAGE DASHBOARD APIs")
    print("="*70)
    
    # Test 1: Origin Analysis API
    print("\n1️⃣  Testing GET /projects/{id}/origin-analysis...")
    url = f"{API_BASE}/projects/{PROJECT_ID}/origin-analysis"
    response = requests.get(url)
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Origin Analysis Response:")
        print(json.dumps(data, indent=2))
        
        if data.get("source_type"):
            print(f"\n   📊 Source: {data['source_type']} on {data.get('server', 'N/A')}")
            print(f"   📦 Package: {data.get('package_name', 'N/A')}")
            print(f"   🔗 Connections: {len(data.get('connections', []))}")
        else:
            print(f"\n   ℹ️  {data.get('message', 'No data available')}")
    else:
        print(f"   ❌ Error: {response.text}")
    
    # Test 2: Transformations API
    print("\n\n2️⃣  Testing GET /projects/{id}/transformations...")
    url = f"{API_BASE}/projects/{PROJECT_ID}/transformations"
    response = requests.get(url)
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Transformations Response:")
        print(json.dumps(data, indent=2))
        
        if data.get("transformations_matrix"):
            print(f"\n   📊 Package: {data.get('package_name', 'N/A')}")
            print(f"   🎯 Complexity: {data.get('complexity_score', 0)}/100")
            print(f"   🔧 Transformations: {data.get('total_transformations', 0)}")
            print(f"\n   Matrix:")
            for trans in data["transformations_matrix"]:
                print(f"      - {trans['type']}: {trans['count']} ({trans['details']})")
        else:
            print(f"\n   ℹ️  {data.get('message', 'No data available')}")
    else:
        print(f"   ❌ Error: {response.text}")
    
    # Test 3: Source Queries API
    print("\n\n3️⃣  Testing GET /projects/{id}/source-queries...")
    url = f"{API_BASE}/projects/{PROJECT_ID}/source-queries"
    response = requests.get(url)
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Source Queries Response:")
        print(json.dumps(data, indent=2))
        
        if data.get("queries"):
            print(f"\n   📊 Package: {data.get('package_name', 'N/A')}")
            print(f"   📜 Total Queries: {data.get('total_queries', 0)}")
            print(f"\n   Queries:")
            for query in data["queries"]:
                print(f"\n      [{query['component_type']}] {query['component_name']}")
                print(f"      {query['query'][:80]}...")
        else:
            print(f"\n   ℹ️  {data.get('message', 'No data available')}")
    else:
        print(f"   ❌ Error: {response.text}")
    
    print("\n" + "="*70)
    print("✅ API TESTS COMPLETED")
    print("="*70)

if __name__ == "__main__":
    test_apis()

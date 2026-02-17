"""
Script para testear el login con el nuevo sistema v3.9
"""
import requests
import json

API_URL = "http://localhost:8085"

def test_login(username, password):
    """Test login endpoint"""
    print(f"\n{'='*60}")
    print(f"Testing login: {username}")
    print(f"{'='*60}")
    
    response = requests.post(
        f"{API_URL}/login",
        json={"username": username, "password": password},
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Login exitoso!")
        print(f"   Tenant ID: {data.get('tenant_id')}")
        print(f"   User ID:   {data.get('user_id')}")
        print(f"   Client ID: {data.get('client_id')}")
        print(f"   Role:      {data.get('role')}")
        print(f"   Message:   {data.get('message')}")
        return data
    else:
        print("❌ Login fallido!")
        try:
            error = response.json()
            print(f"   Error: {error.get('detail', response.text)}")
        except:
            print(f"   Error: {response.text}")
        return None

def main():
    print("="*60)
    print("TEST DE LOGIN v3.9 - Multi-Usuario")
    print("="*60)
    
    # Testear con usuarios DEMO
    test_cases = [
        ("demo1@demo.local", "demo123"),
        ("demo2@demo.local", "demo123"),
        ("demo3@demo.local", "demo123"),
        ("DEMO1", "demo123"),  # Backward compat: login con username
        ("demo1", "demo123"),  # Username en minúsculas
    ]
    
    results = []
    for username, password in test_cases:
        result = test_login(username, password)
        results.append({
            "username": username,
            "success": result is not None
        })
    
    # Resumen
    print("\n" + "="*60)
    print("RESUMEN")
    print("="*60)
    
    successful = sum(1 for r in results if r["success"])
    print(f"Exitosos: {successful}/{len(results)}")
    
    for r in results:
        status = "✅" if r["success"] else "❌"
        print(f"   {status} {r['username']}")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: No se pudo conectar al servidor")
        print("   Asegúrate de que el servidor esté corriendo en http://localhost:8085")
        print("   Ejecuta: python run.py")

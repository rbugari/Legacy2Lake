import requests

print("🔍 Testeando backend...")
print("-" * 60)

headers = {"X-Tenant-ID": "daac0ee6-3b28-412d-8acd-43ec51149188"}

try:
    print("\n→ Llamando GET /projects")
    r = requests.get("http://localhost:8085/projects", headers=headers)
    print(f"✅ Status: {r.status_code}")
    
    data = r.json()
    if isinstance(data, dict) and 'value' in data:
        print(f"📊 Projects count: {len(data['value'])}")
    elif isinstance(data, list):
        print(f"📊 Projects count: {len(data)}")
    
    print("\n" + "=" * 60)
    print("⚠️  REVISA LA VENTANA 'Legacy2Lake API (Port 8085)'")
    print("=" * 60)
    print("   Deberías ver:")
    print("   → GET /projects")
    print("   ✅ 200 (XXms) [tenant:daac0ee6...]")
    print("\n" + "=" * 60)
    print("Si NO ves esos logs arriba ☝️")
    print("Cierra la ventana del backend y ejecuta: python run.py")
    print("=" * 60)
except Exception as e:
    print(f"❌ Error: {e}")
    print("\n¿El backend está corriendo?")
    print("Ejecuta: python run.py")

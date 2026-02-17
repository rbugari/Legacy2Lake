import requests
import json

# Get project UUID by name
url = 'http://localhost:8000/api/v1/projects'
headers = {
    'X-Tenant-ID': 'daac0ee6-3b28-412d-8acd-43ec51149188'
}

print("Buscando proyecto 'ttt'...")
try:
    response = requests.get(url, headers=headers, timeout=10)
    projects = response.json()
    
    # Find project with name='ttt'
    ttt_project = None
    for proj in projects:
        if proj.get('name') == 'ttt' or proj.get('project_name') == 'ttt':
            ttt_project = proj
            break
    
    if ttt_project:
        project_id = ttt_project.get('project_id') or ttt_project.get('id')
        print(f"✅ Proyecto 'ttt' encontrado:")
        print(f"   project_id: {project_id}")
        print(f"   name: {ttt_project.get('name') or ttt_project.get('project_name')}")
    else:
        print("❌ Proyecto 'ttt' no encontrado")
        print(f"\nProyectos disponibles:")
        for proj in projects[:5]:
            name = proj.get('name') or proj.get('project_name')
            pid = proj.get('project_id') or proj.get('id')
            print(f"  - {name}: {pid}")
            
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

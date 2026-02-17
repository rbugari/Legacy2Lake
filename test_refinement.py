import requests
import json
from datetime import datetime

url = 'http://localhost:8000/refine/start'
headers = {
    'X-Tenant-ID': 'daac0ee6-3b28-412d-8acd-43ec51149188',
    'Content-Type': 'application/json'
}
body = {'project_id': 'ttt'}

print(f'[{datetime.now().strftime("%H:%M:%S")}] ▶️ POST /refine/start iniciado...')
try:
    start = datetime.now()
    response = requests.post(url, headers=headers, json=body, timeout=180)
    duration = (datetime.now() - start).total_seconds()
    print(f'[{datetime.now().strftime("%H:%M:%S")}] ✅ Completado en {duration:.1f}s')
    print(f'Status: {response.status_code}')
    print(f'\n📊 RESPONSE:')
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f'❌ ERROR: {e}')
    import traceback
    traceback.print_exc()

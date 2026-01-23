import requests
import json

url = "http://localhost:8085/transpile/orchestrate"
payload = {
    "project_id": "base", # Pass Name instead of UUID
    "limit": 1
}
headers = {
    'Content-Type': 'application/json',
    'X-Tenant-ID': 'd127a303-fd01-44b3-a7b3-827238d76d1f',
    'X-Client-ID': '27ff46c8-06e9-4220-912a-5d09a3dd1a36'
}

print(f"Triggering migration for {payload['project_id']} on port 8085...")
try:
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    print(f"Status: {response.status_code}")
    print(response.text[:1000])
except Exception as e:
    print(f"Error: {e}")

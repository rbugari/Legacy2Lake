"""
Debug login for DEMO34
"""
import requests
import json

API_BASE = "http://localhost:8085"

print("Attempting login as DEMO34...")
print("=" * 60)

response = requests.post(
    f"{API_BASE}/auth/login",
    json={
        "username": "DEMO34",
        "password": "Test1234"
    }
)

print(f"Status Code: {response.status_code}")
print(f"Headers: {dict(response.headers)}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
print("=" * 60)

# Try with lowercase
print("\nTrying with lowercase 'demo34'...")
response2 = requests.post(
    f"{API_BASE}/auth/login",
    json={
        "username": "demo34",
        "password": "Test1234"
    }
)

print(f"Status Code: {response2.status_code}")
print(f"Response: {json.dumps(response2.json(), indent=2)}")

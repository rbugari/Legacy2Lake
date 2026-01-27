"""
Test script to verify the /projects/{project_id}/triage endpoint
"""
import requests
import json

BASE_URL = "http://localhost:8089"
PROJECT_ID = "test-project-001"  # Replace with your actual project ID

print("\n" + "="*70)
print("TESTING TRIAGE ENDPOINT")
print("="*70 + "\n")

# Test the triage endpoint
print(f"Testing: POST /projects/{PROJECT_ID}/triage")
print(f"URL: {BASE_URL}/projects/{PROJECT_ID}/triage\n")

try:
    response = requests.post(
        f"{BASE_URL}/projects/{PROJECT_ID}/triage",
        headers={
            "Content-Type": "application/json",
            "X-Tenant-ID": "00000000-0000-0000-0000-000000000001",
            "X-Client-ID": "client-001"
        },
        json={
            "system_prompt": "Test prompt",
            "user_context": "Test context"
        },
        timeout=30
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"\nResponse Headers:")
    for key, value in response.headers.items():
        print(f"  {key}: {value}")
    
    print(f"\nResponse Body:")
    try:
        data = response.json()
        print(json.dumps(data, indent=2))
    except:
        print(response.text[:500])
        
    if response.status_code == 200:
        print("\n✅ Endpoint is working!")
    elif response.status_code == 404:
        print("\n❌ Project not found - create a project first")
    else:
        print(f"\n⚠️  Unexpected status code: {response.status_code}")
        
except requests.exceptions.Timeout:
    print("❌ Request timed out after 30 seconds")
except requests.exceptions.ConnectionError:
    print("❌ Could not connect to server - is it running?")
except Exception as e:
    print(f"❌ Error: {str(e)}")

print("\n" + "="*70 + "\n")

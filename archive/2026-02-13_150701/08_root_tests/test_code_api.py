"""
Test the code API endpoint
"""
import requests

def test_code_api():
    project_id = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"
    url = f"http://localhost:8085/projects/{project_id}/generated-code"
    
    print(f"Testing: {url}")
    
    try:
        response = requests.get(url)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ SUCCESS!")
            
            code = data.get('code', '')
            metadata = data.get('metadata', {})
            
            print(f"\nCode Length: {len(code)} chars")
            print(f"Object Name: {metadata.get('object_name')}")
            print(f"Tech ID: {metadata.get('tech_id')}")
            print(f"Layer: {metadata.get('layer')}")
            
            print(f"\n--- First 300 chars of code ---")
            print(code[:300])
            
            print(f"\n--- Last 150 chars of code ---")
            print(code[-150:])
        else:
            print(f"\n❌ Error: {response.text}")
    
    except Exception as e:
        print(f"\n❌ Exception: {e}")

if __name__ == "__main__":
    test_code_api()

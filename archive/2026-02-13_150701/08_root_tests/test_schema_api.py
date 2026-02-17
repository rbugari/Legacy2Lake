"""
Test the schema API endpoint
"""
import requests
import json

def test_api():
    project_id = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"
    url = f"http://localhost:8085/projects/{project_id}/schema"
    
    print(f"Testing: {url}")
    
    try:
        response = requests.get(url)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ SUCCESS!")
            print(f"\nSchema Data:")
            print(json.dumps(data, indent=2))
            
            if 'columns' in data:
                print(f"\n📊 Columns: {len(data['columns'])}")
                for col in data['columns']:
                    print(f"  - {col.get('name')}: {col.get('type')}")
        else:
            print(f"\n❌ Error: {response.text}")
    
    except Exception as e:
        print(f"\n❌ Exception: {e}")

if __name__ == "__main__":
    test_api()

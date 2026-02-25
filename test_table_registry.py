"""
Test Table Registry endpoints
"""
import requests

project_id = "ec771d1a-4fe4-4499-970d-54e28de4d926"
tenant_id = "daac0ee6-e94a-48cd-8464-ad3cf08ed69e"
base_url = "http://localhost:8085"

headers = {
    "X-Tenant-ID": tenant_id
}

print("\n" + "="*80)
print("Testing Table Registry APIs")
print("="*80 + "\n")

# Test 1: Get tables summary
print("1. Getting tables summary...")
response = requests.get(f"{base_url}/projects/{project_id}/tables/summary", headers=headers)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    tables = response.json()
    print(f"\nFound {len(tables)} tables:")
    
    # Print first table raw to debug
    if tables:
        print(f"\nFirst table raw JSON:")
        import json
        print(json.dumps(tables[0], indent=2))
    
    for table in tables[:5]:  # First 5
        print(f"  - {table.get('full_name', 'NO_FULL_NAME')}")
        print(f"    Readers: {table.get('reader_count', 'N/A')}, Writers: {table.get('writer_count', 'N/A')}")
        print(f"    Operations: {', '.join(table.get('operations', []))}")
    if len(tables) > 5:
        print(f"  ... and {len(tables) - 5} more")
else:
    print(f"Error: {response.text}")

# Test 2: Get detail of first table
if response.status_code == 200 and tables:
    print(f"\n2. Getting detail of table '{tables[0]['full_name']}'...")
    detail_response = requests.get(
        f"{base_url}/projects/{project_id}/tables/{tables[0]['full_name']}/detail",
        headers=headers
    )
    print(f"Status: {detail_response.status_code}")
    
    if detail_response.status_code == 200:
        detail = detail_response.json()
        print(f"\nTable: {detail['full_name']}")
        print(f"  Readers: {len(detail['readers'])}")
        print(f"  Writers: {len(detail['writers'])}")
        
        if detail['readers']:
            print(f"\n  Sample reader:")
            reader = detail['readers'][0]
            print(f"    Asset: {reader['asset_name']}")
            print(f"    Operation: {reader['operation']}")
            if reader['columns_affected']:
                print(f"    Columns: {', '.join(reader['columns_affected'][:3])}")
    else:
        print(f"Error: {detail_response.text}")

print("\n" + "="*80)

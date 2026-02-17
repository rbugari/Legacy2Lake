"""
Re-run Discovery + Triage with updated parser
"""
import requests
import time

project_id = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"
tenant_id = "daac0ee6-3b28-412d-8acd-43ec51149188"
base_url = "http://localhost:8085"

headers = {
    "X-Tenant-ID": tenant_id,
    "Content-Type": "application/json"
}

print("="*70)
print("🔄 Re-executing Discovery + Triage with updated parser")
print("="*70)

# Wait for backend to be ready
print("\n⏳ Waiting for backend...")
for _ in range(10):
    try:
        resp = requests.get(f"{base_url}/health", timeout=2)
        if resp.status_code == 200:
            print("✅ Backend ready")
            break
    except:
        pass
    time.sleep(1)
else:
    print("❌ Backend not responding")
    exit(1)

# Execute Triage (includes Discovery)
print(f"\n🚀 Running Triage for project {project_id}")
print("   (This will run Discovery first, then Triage)")

try:
    response = requests.post(
        f"{base_url}/projects/{project_id}/triage",
        headers=headers,
        json={"system_prompt": None, "user_context": None},
        timeout=180
    )
    
    if response.status_code == 200:
        result = response.json()
        print("\n✅ Triage completed successfully!")
        print(f"   - Discovery processed: {result.get('discovery', {}).get('files_processed', 0)} files")
        print(f"   - Assets saved: {result.get('triage', {}).get('assets_processed', 0)} assets")
    else:
        print(f"\n❌ Triage failed: {response.status_code}")
        print(f"   Error: {response.text}")
        exit(1)
        
except requests.exceptions.Timeout:
    print("\n⏱️ Request timed out (may still be processing)")
except Exception as e:
    print(f"\n❌ Error: {e}")
    exit(1)

print("\n" + "="*70)
print("✅ Discovery + Triage completed")
print("="*70)
print("\n💡 Now run: python check_discovery_result.py")
print("   to verify connections were extracted correctly")
print("\n" + "="*70)

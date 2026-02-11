"""Quick test to verify Sprint 4 security fixes are active"""
import requests

print("Testing Sprint 4 Security Fixes...")
print("=" * 60)

# Test 1: SQL Injection (should return 403 if fixed)
print("\n[TEST 1] SQL Injection: ' OR '1'='1")
r1 = requests.get(
    'http://localhost:8085/system/catalog',
    headers={'X-Tenant-ID': "' OR '1'='1"}
)
print(f"Status: {r1.status_code}")
print(f"Expected: 403 (Forbidden)")
print(f"Result: {'✅ PASS' if r1.status_code == 403 else '🚨 FAIL - CODE NOT ACTIVE'}")

# Test 2: Empty header (should return 400 if fixed)
print("\n[TEST 2] Empty X-Tenant-ID")
r2 = requests.get(
    'http://localhost:8085/system/catalog',
    headers={'X-Tenant-ID': ""}
)
print(f"Status: {r2.status_code}")
print(f"Expected: 400 (Bad Request)")
print(f"Result: {'✅ PASS' if r2.status_code == 400 else '🚨 FAIL - CODE NOT ACTIVE'}")

# Test 3: Valid UUID (should work)
print("\n[TEST 3] Valid UUID")
r3 = requests.get(
    'http://localhost:8085/system/catalog',
    headers={'X-Tenant-ID': "aaaaaaaa-1111-4111-8111-111111111111"}
)
print(f"Status: {r3.status_code}")
print(f"Expected: 200 or 404")
print(f"Result: {'✅ PASS' if r3.status_code in [200, 404] else f'🚨 UNEXPECTED: {r3.status_code}'}")

print("\n" + "=" * 60)
if r1.status_code == 403 and r2.status_code == 400:
    print("✅ Sprint 4 security code IS ACTIVE")
else:
    print("🚨 Sprint 4 security code NOT ACTIVE - API needs restart")

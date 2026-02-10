"""
Verify DEMO34 password hash
"""
import bcrypt
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

# Get hash from DB
result = client.table("utm_users").select("username, password_hash_bcrypt").eq(
    "username", "DEMO34"
).limit(1).execute()

if not result.data:
    print("❌ DEMO34 not found")
    exit(1)

stored_hash = result.data[0]["password_hash_bcrypt"]
print(f"Stored hash: {stored_hash}")
print(f"Hash length: {len(stored_hash)}")

# Test passwords
test_passwords = ["Test1234", "test1234", "TEST1234", "demo1234", "DEMO34"]

print("\nTesting passwords:")
for pwd in test_passwords:
    try:
        match = bcrypt.checkpw(pwd.encode(), stored_hash.encode())
        print(f"  {pwd:15} : {' ✅ MATCH' if match else '❌ no match'}")
        if match:
            print(f"\n🎯 CORRECT PASSWORD: {pwd}")
            break
    except Exception as e:
        print(f"  {pwd:15} : ERROR - {e}")

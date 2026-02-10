"""Find ADMIN users in the database"""
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

print("Connecting to database...")
client = create_client(url, key)
print("Connected!")

# Find ADMIN users
res = client.table('utm_users').select(
    'user_id, tenant_id, username, email, role'
).eq('role', 'ADMIN').execute()

print("\n=== ADMIN USERS ===")
if res.data:
    for u in res.data:
        print(f"\nUsername: {u['username']}")
        print(f"Email: {u['email']}")
        print(f"User ID: {u['user_id']}")
        print(f"Tenant ID: {u['tenant_id']}")
else:
    print("No ADMIN users found")

# Also check all users (to find admin)
print("\n=== ALL USERS (ordered by role) ===")
all_users = client.table('utm_users').select(
    'username, email, role'
).order('role').execute()

for u in all_users.data[:15]:  # First 15
    print(f"{u['role']:15} | {u['username']:20} | {u['email']}")


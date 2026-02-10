"""
Create platform ADMIN user (one-time setup)
"""
import os
import bcrypt
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
client = create_client(url, key)

# Fixed IDs
PLATFORM_CLIENT_ID = "PLATFORM"  # VARCHAR, not UUID
PLATFORM_TENANT_ID = "00000000-0000-0000-0000-000000000001"
ADMIN_USER_ID = "00000000-0000-0000-0000-000000000001"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Admin123!"

print("🔧 Creating Platform ADMIN user...")

# 1. Create PLATFORM tenant (if not exists)
existing_tenant = client.table('utm_tenants').select('tenant_id').eq('tenant_id', PLATFORM_TENANT_ID).execute()

if not existing_tenant.data:
    print("  → Creating PLATFORM tenant...")
    client.table('utm_tenants').insert({
        'tenant_id': PLATFORM_TENANT_ID,
        'client_id': PLATFORM_CLIENT_ID,  # VARCHAR field, not UUID
        'org_name': 'Platform Admin Organization',
        'tier': 'ENTERPRISE',
        'is_active': True
    }).execute()
    print("  ✅ PLATFORM tenant created")
else:
    print("  ℹ️  PLATFORM tenant already exists")

# 2. Create ADMIN user (if not exists)
existing_user = client.table('utm_users').select('user_id').eq('user_id', ADMIN_USER_ID).execute()

if not existing_user.data:
    print(f"  → Creating ADMIN user: {ADMIN_USERNAME}")
    
    # Hash password with bcrypt
    password_hash = bcrypt.hashpw(ADMIN_PASSWORD.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')
    
    client.table('utm_users').insert({
        'user_id': ADMIN_USER_ID,
        'tenant_id': PLATFORM_TENANT_ID,
        'username': ADMIN_USERNAME,
        'email': 'admin@platform.local',
        'password_hash_bcrypt': password_hash,
        'role': 'ADMIN',
        'is_active': True,
        'display_name': 'Platform Administrator'
    }).execute()
    
    print("  ✅ ADMIN user created")
    print("\n" + "="*60)
    print("🎉 Platform ADMIN created successfully!")
    print("="*60)
    print(f"\n  Username: {ADMIN_USERNAME}")
    print(f"  Password: {ADMIN_PASSWORD}")
    print(f"\n  🔐 Login at: http://localhost:3005")
    print("\n  ⚠️  Remember to change the password after first login!")
    print("="*60)
else:
    print("  ℹ️  ADMIN user already exists")
    print(f"\n  Username: {ADMIN_USERNAME}")
    print(f"  Password: {ADMIN_PASSWORD}")

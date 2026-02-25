#!/usr/bin/env python3
"""
Update user role to ADMIN for testing
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
TENANT_ID = "daac0ee6-3b28-412d-8acd-43ec51149188"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("🔧 Updating user role to ADMIN...")

# Get users for this tenant
result = supabase.table("utm_users").select("*").eq("tenant_id", TENANT_ID).execute()

if result.data:
    admin_user_id = None
    for user in result.data:
        user_id = user["user_id"]
        current_role = user.get("role", "VIEWER")
        
        print(f"User: {user.get('email', 'N/A')} | Current role: {current_role} | user_id: {user_id}")
        
        if current_role != "ADMIN":
            # Update to ADMIN
            update_result = supabase.table("utm_users").update({"role": "ADMIN"}).eq("user_id", user_id).execute()
            print(f"  ✅ Updated to ADMIN")
            admin_user_id = user_id
        else:
            print(f"  ✓ Already ADMIN")
            if not admin_user_id:
                admin_user_id = user_id
    
    if admin_user_id:
        print(f"\n📝 Use this user_id for testing: {admin_user_id}")
else:
    print("❌ No users found for tenant")

print("\nDone!")

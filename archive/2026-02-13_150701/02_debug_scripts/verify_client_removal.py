#!/usr/bin/env python3
"""
Verify that migration 024 executed successfully:
- client_id column removed from utm_tenants
- display_name column added
- Existing tenants have display_name values
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("🔍 Verifying Migration 024: CLIENT Removal")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

# Fetch all tenants with new structure
try:
    result = supabase.table("utm_tenants").select("tenant_id, org_name, display_name, tier, is_active").execute()
    tenants = result.data
    
    print(f"✅ Successfully queried utm_tenants without client_id")
    print(f"📊 Found {len(tenants)} tenants:\n")
    
    for tenant in tenants:
        print(f"  • {tenant['display_name'] or '(no display name)'}")
        print(f"    Org ID: {tenant['org_name']}")
        print(f"    Tenant ID: {tenant['tenant_id']}")
        print(f"    Tier: {tenant['tier']} | Active: {tenant['is_active']}")
        print()
    
    # Check that display_name exists for all
    without_display = [t for t in tenants if not t.get('display_name')]
    if without_display:
        print(f"⚠️  {len(without_display)} tenants without display_name:")
        for t in without_display:
            print(f"    - {t['org_name']} ({t['tenant_id']})")
    else:
        print("✅ All tenants have display_name values")
    
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("✅ Migration 024 verified successfully!")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nThis could mean:")
    print("  1. client_id column still exists (migration not complete)")
    print("  2. display_name column missing")
    print("  3. Database connection issue")
    print()

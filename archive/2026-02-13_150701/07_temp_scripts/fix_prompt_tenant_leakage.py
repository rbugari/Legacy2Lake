"""
Sprint 4 - Security Hardening: Fix Prompt Cross-Tenant Leakage

CRITICAL ISSUE (Sprint 3 Test Results):
- 9 prompts have tenant_id = NULL
- These prompts are accessible by ALL tenants (data leakage)
- Security test: test_multi_tenant_isolation.py → test_prompt_cross_tenant_leakage FAILED

ROOT CAUSE:
- utm_prompts.tenant_id column is nullable
- Historical data migrated without tenant_id values
- No database constraint to prevent NULL values

FIX STRATEGY:
1. Assign NULL prompts to default tenant ('demo3')
2. Add NOT NULL constraint to tenant_id column
3. Verify no cross-tenant access after fix

IMPACT:
- Fixes CRITICAL vulnerability (6/10 severity)
- Prevents unauthorized access to prompts
- Blocks Sprint 3 deployment

ROLLBACK:
If issues occur:
  ALTER TABLE utm_prompts ALTER COLUMN tenant_id DROP NOT NULL;
  UPDATE utm_prompts SET tenant_id = NULL WHERE tenant_id = 'aaaaaaaa-1111-4111-8111-111111111111';
"""

import os
from supabase import create_client

# Supabase credentials
SUPABASE_URL = "https://qdsdfityyxmalyipqbfm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFkc2RmaXR5eXhtYWx5aXBxYmZtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODg2NTczOSwiZXhwIjoyMDg0NDQxNzM5fQ.f4Ge4MPpeDoFLgLSD9e79V2N-ND-aU9YqwNp2VrOgC0"

# Default tenant for orphaned prompts
DEFAULT_TENANT_ID = "aaaaaaaa-1111-4111-8111-111111111111"  # Test Tenant Alpha (ENTERPRISE)

def main():
    """Execute SQL migration to fix prompt tenant leakage."""
    
    print("=" * 80)
    print("SPRINT 4 - SECURITY HARDENING: Fix Prompt Cross-Tenant Leakage")
    print("=" * 80)
    
    # Initialize Supabase client
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Step 1: Check for NULL tenant_id prompts
    print("\n[1/4] Checking for orphaned prompts (tenant_id IS NULL)...")
    response = client.table("utm_prompts").select("prompt_id, version, tenant_id").is_("tenant_id", "null").execute()
    
    orphaned_count = len(response.data) if response.data else 0
    print(f"      Found {orphaned_count} prompts with NULL tenant_id")
    
    if orphaned_count > 0:
        print("\n      Orphaned prompts:")
        for prompt in response.data[:5]:  # Show first 5
            print(f"      - {prompt['prompt_id']} (v{prompt['version']})")
        if orphaned_count > 5:
            print(f"      ... and {orphaned_count - 5} more")
    
    # Step 2: Assign orphaned prompts to default tenant
    if orphaned_count > 0:
        print(f"\n[2/4] Assigning {orphaned_count} orphaned prompts to default tenant...")
        print(f"      Default Tenant: {DEFAULT_TENANT_ID} (Test Tenant Alpha)")
        
        # Update using RPC or direct SQL
        # Note: Supabase Python client doesn't support UPDATE with IS NULL directly
        # We'll update each prompt individually
        updated_count = 0
        for prompt in response.data:
            try:
                update_response = client.table("utm_prompts").update({
                    "tenant_id": DEFAULT_TENANT_ID
                }).eq("prompt_id", prompt["prompt_id"]).execute()
                updated_count += 1
            except Exception as e:
                print(f"      ERROR updating prompt {prompt['prompt_id']}: {e}")
        
        print(f"      ✅ Updated {updated_count}/{orphaned_count} prompts")
    else:
        print(f"\n[2/4] No orphaned prompts found. Skipping assignment step.")
    
    # Step 3: Verify no remaining NULL tenant_id values
    print("\n[3/4] Verifying all prompts have tenant_id...")
    verify_response = client.table("utm_prompts").select("prompt_id").is_("tenant_id", "null").execute()
    remaining_nulls = len(verify_response.data) if verify_response.data else 0
    
    if remaining_nulls == 0:
        print(f"      ✅ All prompts have tenant_id assigned")
    else:
        print(f"      ⚠️  WARNING: {remaining_nulls} prompts still have NULL tenant_id")
        print(f"      Manual intervention required before adding NOT NULL constraint")
        return
    
    # Step 4: Add NOT NULL constraint (SQL execution)
    print("\n[4/4] Adding NOT NULL constraint to utm_prompts.tenant_id...")
    print("      ⚠️  NOTE: This requires SQL execution with ALTER TABLE privileges")
    print("      Manual SQL required (cannot execute via Supabase Python client):")
    print("")
    print("      SQL Command:")
    print("      ------------")
    print("      ALTER TABLE utm_prompts ALTER COLUMN tenant_id SET NOT NULL;")
    print("")
    print("      Execute this SQL in Supabase SQL Editor:")
    print("      1. Go to: https://qdsdfityyxmalyipqbfm.supabase.co")
    print("      2. Navigate to: SQL Editor")
    print("      3. Run the ALTER TABLE command above")
    print("      4. Verify with: SELECT COUNT(*) FROM utm_prompts WHERE tenant_id IS NULL;")
    print("")
    
    # Final summary
    print("=" * 80)
    print("MIGRATION SUMMARY")
    print("=" * 80)
    print(f"✅ Orphaned prompts found: {orphaned_count}")
    print(f"✅ Prompts updated: {updated_count if orphaned_count > 0 else 0}")
    print(f"✅ Remaining NULLs: {remaining_nulls}")
    print(f"⚠️  NOT NULL constraint: MANUAL SQL REQUIRED (see above)")
    print("")
    print("NEXT STEPS:")
    print("1. Execute ALTER TABLE SQL in Supabase SQL Editor")
    print("2. Re-run security tests: python test_multi_tenant_security.py")
    print("3. Verify test_prompt_cross_tenant_leakage passes")
    print("=" * 80)

if __name__ == "__main__":
    main()

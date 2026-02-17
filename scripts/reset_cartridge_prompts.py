#!/usr/bin/env python3
"""
Reset Cartridge Prompts
Purpose: Delete existing cartridge prompts to force fresh auto-seeding
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.api.services.persistence_service import SupabasePersistence

def reset_cartridge_prompts(tenant_id: str = None, force: bool = False):
    """Delete all cartridge_databricks_* prompts to trigger re-seeding"""
    
    print("=" * 70)
    print("Resetting Cartridge Prompts")
    print("=" * 70)
    
    db = SupabasePersistence()
    
    try:
        # Query existing cartridge prompts
        query = db.client.table('utm_prompts').select(
            'prompt_id, tenant_id'
        ).like('prompt_id', 'cartridge_databricks_%')
        
        if tenant_id:
            query = query.eq('tenant_id', tenant_id)
            print(f"\nTarget: Tenant-specific prompts (tenant_id={tenant_id})")
        else:
            print(f"\nTarget: All global cartridge prompts")
        
        result = query.execute()
        
        if not result.data:
            print("\n✅ No cartridge prompts found - already clean")
            return True
        
        print(f"\n📋 Found {len(result.data)} prompt(s) to delete:")
        for prompt in result.data:
            print(f"   - {prompt['prompt_id']} (tenant: {prompt.get('tenant_id', 'GLOBAL')})")
        
        # Confirm deletion (unless forced)
        if not force:
            print("\n⚠️  WARNING: This will delete all cartridge prompts!")
            print("After deletion, restart the backend to trigger auto-seeding.\n")
            
            confirm = input("Type 'DELETE' to confirm: ")
            
            if confirm.strip().upper() != 'DELETE':
                print("\n❌ Cancelled - no changes made")
                return False
        else:
            print("\n⚠️  FORCE MODE: Deleting without confirmation")
        
        # Delete prompts
        print("\nDeleting prompts...")
        
        delete_query = db.client.table('utm_prompts').delete().like(
            'prompt_id', 'cartridge_databricks_%'
        )
        
        if tenant_id:
            delete_query = delete_query.eq('tenant_id', tenant_id)
        
        delete_result = delete_query.execute()
        
        print(f"✅ Deleted {len(result.data)} prompt(s)")
        print("\n" + "=" * 70)
        print("NEXT STEPS:")
        print("=" * 70)
        print("1. Restart the backend:")
        print("   PS> .\\restart.ps1")
        print("\n2. Monitor logs for auto-seeding:")
        print("   PS> .\\watch_logs.ps1")
        print("\n3. Look for these log messages:")
        print("   [PromptService] Auto-seeded: cartridge_databricks_bronze")
        print("   [PromptService] Auto-seeded: cartridge_databricks_silver")
        print("   [PromptService] Auto-seeded: cartridge_databricks_gold")
        print("\n4. Verify with:")
        print("   PS> python scripts\\verify_cartridge_prompts.py")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    # Use the main tenant ID from the project
    TENANT_ID = "daac0ee6-3b28-412d-8acd-43ec51149188"
    
    # Check for --force flag
    force = '--force' in sys.argv
    
    success = reset_cartridge_prompts(tenant_id=TENANT_ID, force=force)
    sys.exit(0 if success else 1)

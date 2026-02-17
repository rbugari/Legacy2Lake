#!/usr/bin/env python3
"""
Verify Cartridge Prompts in Database
Purpose: Check if Bronze, Silver, and Gold cartridge prompts are loaded in utm_prompts
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.api.services.persistence_service import SupabasePersistence

def verify_cartridge_prompts():
    """Query utm_prompts to verify all cartridge prompts are loaded"""
    
    print("=" * 70)
    print("Verifying Cartridge Prompts in Database")
    print("=" * 70)
    
    # Initialize persistence (global prompts don't need tenant_id)
    db = SupabasePersistence()
    
    try:
        # Query all cartridge prompts
        result = db.client.table('utm_prompts').select(
            'prompt_id, tenant_id, is_active, created_at'
        ).like('prompt_id', 'cartridge_databricks_%').execute()
        
        if not result.data:
            print("\n❌ NO CARTRIDGE PROMPTS FOUND")
            print("\nAction required:")
            print("  1. Restart the backend to trigger auto-seeding")
            print("  2. Check logs for '[PromptService] Auto-seeded' messages")
            return False
        
        # Display found prompts
        print(f"\n✅ Found {len(result.data)} cartridge prompt(s):\n")
        
        expected = {
            'cartridge_databricks_bronze': 8117,
            'cartridge_databricks_silver': 13909,
            'cartridge_databricks_gold': 18228
        }
        
        found_prompts = {}
        
        for prompt in result.data:
            prompt_id = prompt['prompt_id']
            tenant = prompt.get('tenant_id', 'GLOBAL')
            is_active = prompt.get('is_active', False)
            created = prompt.get('created_at', 'N/A')
            
            # Get content length
            content_result = db.client.table('utm_prompts').select(
                'content'
            ).eq('prompt_id', prompt_id).limit(1).execute()
            
            char_count = len(content_result.data[0]['content']) if content_result.data else 0
            found_prompts[prompt_id] = char_count
            
            status = "✅" if is_active else "⚠️"
            print(f"  {status} {prompt_id}")
            print(f"     Size: {char_count:,} chars")
            print(f"     Tenant: {tenant}")
            print(f"     Active: {is_active}")
            print(f"     Created: {created[:19] if created != 'N/A' else 'N/A'}")
            print()
        
        # Check completeness
        print("=" * 70)
        print("Completeness Check:")
        print("=" * 70)
        
        all_present = True
        for prompt_id, expected_size in expected.items():
            if prompt_id in found_prompts:
                actual_size = found_prompts[prompt_id]
                size_match = abs(actual_size - expected_size) < 100  # Allow 100 char variance
                
                if size_match:
                    print(f"✅ {prompt_id}: Present ({actual_size:,} chars)")
                else:
                    print(f"⚠️  {prompt_id}: Size mismatch (expected ~{expected_size:,}, got {actual_size:,})")
            else:
                print(f"❌ {prompt_id}: MISSING")
                all_present = False
        
        print("=" * 70)
        
        if all_present and len(found_prompts) == 3:
            print("\n🎉 SUCCESS: All cartridge prompts are properly loaded!")
            return True
        else:
            print("\n⚠️  WARNING: Some cartridge prompts are missing or incorrect")
            print("\nAction required:")
            print("  1. Check /apps/api/prompts/ directory has all .md files")
            print("  2. Restart backend to trigger auto-seeding")
            print("  3. Monitor logs for '[PromptService] Auto-seeded' messages")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\nPossible causes:")
        print("  - Database connection issue")
        print("  - utm_prompts table doesn't exist")
        print("  - Missing environment variables")
        return False

if __name__ == "__main__":
    success = verify_cartridge_prompts()
    sys.exit(0 if success else 1)

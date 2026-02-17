#!/usr/bin/env python3
"""
Force Cartridge Auto-Seeding
Purpose: Trigger auto-seeding of all cartridge prompts by requesting them
"""

import sys
import os
import asyncio

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.api.services.persistence_service import SupabasePersistence

async def force_auto_seed(tenant_id: str):
    """Force auto-seeding by requesting all cartridge prompts"""
    
    print("=" * 70)
    print("Force Auto-Seeding Cartridge Prompts")
    print("=" * 70)
    
    cartridges = [
        "cartridge_databricks_bronze",
        "cartridge_databricks_silver",
        "cartridge_databricks_gold"
    ]
    
    db = SupabasePersistence(tenant_id=tenant_id)
    
    results = {}
    
    for prompt_id in cartridges:
        print(f"\n📥 Requesting prompt: {prompt_id}")
        
        try:
            # This will trigger auto-seed if prompt doesn't exist
            content = await db.get_prompt(prompt_id)
            
            if content:
                char_count = len(content)
                results[prompt_id] = {
                    "status": "✅ SUCCESS",
                    "size": f"{char_count:,} chars"
                }
                print(f"   ✅ Loaded/Seeded: {char_count:,} chars")
            else:
                results[prompt_id] = {
                    "status": "❌ FAILED",
                    "size": "0 chars"
                }
                print(f"   ❌ Failed to load/seed")
                
        except Exception as e:
            results[prompt_id] = {
                "status": "❌ ERROR",
                "size": str(e)
            }
            print(f"   ❌ Error: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    for prompt_id, result in results.items():
        print(f"{result['status']} {prompt_id}: {result['size']}")
    
    # Check success
    success_count = sum(1 for r in results.values() if "SUCCESS" in r["status"])
    total_count = len(cartridges)
    
    print("\n" + "=" * 70)
    
    if success_count == total_count:
        print(f"🎉 All {total_count} cartridge prompts are loaded!")
        print("\n✅ You can now test Silver and Gold layer generation")
        return True
    else:
        print(f"⚠️  Only {success_count}/{total_count} cartridges loaded")
        print("\nAction required:")
        print("  1. Check /apps/api/prompts/ directory has all .md files")
        print("  2. Check file permissions (read access)")
        print("  3. Verify database connection")
        return False

if __name__ == "__main__":
    TENANT_ID = "daac0ee6-3b28-412d-8acd-43ec51149188"
    
    success = asyncio.run(force_auto_seed(TENANT_ID))
    sys.exit(0 if success else 1)

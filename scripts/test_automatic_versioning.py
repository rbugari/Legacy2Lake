"""
v4.0: Test Automatic Versioning Trigger
Purpose: Verify utm_prompts_history trigger saves old versions automatically
Author: Legacy2Lake Engineering
Date: 2026-02-15
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from apps.api.services.persistence_service import SupabasePersistence
except ImportError:
    try:
        from services.persistence_service import SupabasePersistence
    except ImportError:
        from ..apps.api.services.persistence_service import SupabasePersistence


async def test_automatic_versioning():
    """Test that trigger automatically saves old version when prompt is updated"""
    
    print("=" * 70)
    print("v4.0: Test Automatic Versioning Trigger")
    print("=" * 70)
    print()
    
    db = SupabasePersistence()
    test_prompt_id = "coding_standards"  # Use existing prompt
    
    try:
        # Step 1: Get current content
        print("📋 Step 1: Get current prompt content...")
        current_content = await db.get_prompt(test_prompt_id)
        if not current_content:
            print(f"   ❌ Failed to load prompt '{test_prompt_id}'")
            return False
        
        print(f"   ✅ Current content: {len(current_content)} chars")
        print()
        
        # Step 2: Check current history count
        print("📋 Step 2: Check current history count...")
        history_result = db.client.table("utm_prompts_history") \
            .select("*") \
            .eq("prompt_id", test_prompt_id) \
            .execute()
        
        history_count_before = len(history_result.data) if history_result.data else 0
        print(f"   📊 History entries before update: {history_count_before}")
        print()
        
        # Step 3: Update prompt with new content
        print("📋 Step 3: Update prompt with new content...")
        test_content = f"""# Test Version - {datetime.now().isoformat()}

This is a TEST version created by test_automatic_versioning.py script.
The trigger should save the previous version to utm_prompts_history table.

Original content length: {len(current_content)} chars

---
Original content preview:
{current_content[:200]}...
"""
        
        success = await db.save_prompt(
            prompt_id=test_prompt_id,
            content=test_content,
            metadata={
                "test_run": True,
                "test_timestamp": datetime.now().isoformat(),
                "original_length": len(current_content)
            }
        )
        
        if not success:
            print("   ❌ Failed to update prompt")
            return False
        
        print(f"   ✅ Prompt updated successfully")
        print()
        
        # Step 4: Check history count increased
        print("📋 Step 4: Verify history was saved by trigger...")
        await asyncio.sleep(1)  # Give DB time to process trigger
        
        history_result_after = db.client.table("utm_prompts_history") \
            .select("*") \
            .eq("prompt_id", test_prompt_id) \
            .order("changed_at", desc=True) \
            .execute()
        
        history_count_after = len(history_result_after.data) if history_result_after.data else 0
        print(f"   📊 History entries after update: {history_count_after}")
        
        if history_count_after > history_count_before:
            print(f"   ✅ Trigger worked! New history entry created")
            print()
            
            # Show latest history entry
            latest_history = history_result_after.data[0]
            print("📄 Latest History Entry:")
            print(f"   History ID: {latest_history['history_id']}")
            print(f"   Changed at: {latest_history['changed_at']}")
            print(f"   Content length: {len(latest_history['content'])} chars")
            print(f"   Preview: {latest_history['content'][:100]}...")
            print()
        else:
            print(f"   ⚠️  Trigger may not have fired (count unchanged)")
            print()
        
        # Step 5: Restore original content
        print("📋 Step 5: Restore original content...")
        restore_success = await db.save_prompt(
            prompt_id=test_prompt_id,
            content=current_content,
            metadata={
                "restored": True,
                "restored_at": datetime.now().isoformat()
            }
        )
        
        if restore_success:
            print(f"   ✅ Original content restored")
        else:
            print(f"   ⚠️  Failed to restore original content")
        print()
        
        # Step 6: Final verification
        print("📋 Step 6: Final verification...")
        final_history = db.client.table("utm_prompts_history") \
            .select("*") \
            .eq("prompt_id", test_prompt_id) \
            .execute()
        
        final_count = len(final_history.data) if final_history.data else 0
        print(f"   📊 Total history entries: {final_count}")
        print()
        
        # Summary
        print("=" * 70)
        print("📊 SUMMARY")
        print("=" * 70)
        print(f"   Test prompt: {test_prompt_id}")
        print(f"   History before: {history_count_before}")
        print(f"   History after test: {history_count_after}")
        print(f"   History after restore: {final_count}")
        print(f"   New versions created: {final_count - history_count_before}")
        print()
        
        if final_count > history_count_before:
            print("✅ Automatic versioning trigger is WORKING!")
            print()
            print("📋 Key Points:")
            print("   - Trigger saves OLD version before UPDATE")
            print("   - Only fires when content changes")
            print("   - History is READ-ONLY for ADMIN analysis")
            print("   - No manual action needed for versioning")
            print()
            return True
        else:
            print("⚠️  Trigger may not be working correctly")
            print()
            print("💡 Troubleshooting:")
            print("   1. Check trigger exists: SELECT * FROM pg_trigger WHERE tgname = 'prompt_version_trigger';")
            print("   2. Check function exists: SELECT * FROM pg_proc WHERE proname = 'save_prompt_version';")
            print("   3. Re-run migration: migrations/sprint_v4.0_prompts.sql")
            print()
            return False
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_automatic_versioning())
    sys.exit(0 if success else 1)

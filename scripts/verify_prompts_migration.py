"""
v4.0: Verify Prompts Migration
Purpose: Check that utm_prompts tables were created successfully
Author: Legacy2Lake Engineering
Date: 2026-02-15
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from apps.api.services.persistence_service import SupabasePersistence
    from apps.api.utils.logger import logger
except ImportError:
    try:
        from services.persistence_service import SupabasePersistence
        from utils.logger import logger
    except ImportError:
        from ..apps.api.services.persistence_service import SupabasePersistence
        from ..apps.api.utils.logger import logger


async def verify_migration():
    """Verify that utm_prompts tables were created successfully"""
    
    print("=" * 70)
    print("v4.0 Prompts Migration Verification")
    print("=" * 70)
    print()
    
    try:
        # Connect to database
        print("📋 Step 1: Connecting to Supabase...")
        db = SupabasePersistence()
        print("   ✅ Connected")
        print()
        
        # Check utm_prompts table exists
        print("📋 Step 2: Checking utm_prompts table...")
        try:
            result = db.client.table("utm_prompts").select("count", count="exact").execute()
            prompt_count = result.count if hasattr(result, 'count') else 0
            print(f"   ✅ Table exists")
            print(f"   📊 Current prompts: {prompt_count}")
        except Exception as e:
            print(f"   ❌ Table NOT found: {e}")
            return False
        print()
        
        # Check utm_prompts_history table exists
        print("📋 Step 3: Checking utm_prompts_history table...")
        try:
            result = db.client.table("utm_prompts_history").select("count", count="exact").execute()
            history_count = result.count if hasattr(result, 'count') else 0
            print(f"   ✅ Table exists")
            print(f"   📊 History entries: {history_count}")
        except Exception as e:
            print(f"   ❌ Table NOT found: {e}")
            return False
        print()
        
        # Check trigger exists (via attempting to query pg_trigger)
        print("📋 Step 4: Checking automatic versioning trigger...")
        try:
            # We can't directly query pg_trigger from client, so we'll test by updating
            # For now, just note it should exist
            print("   ⚠️  Cannot verify trigger from Python client")
            print("   💡 Run this SQL to verify:")
            print("      SELECT tgname FROM pg_trigger WHERE tgrelid = 'utm_prompts'::regclass;")
            print("   Expected: prompt_version_trigger")
        except Exception as e:
            print(f"   ⚠️  Could not verify trigger: {e}")
        print()
        
        # Summary
        print("=" * 70)
        print("📊 SUMMARY")
        print("=" * 70)
        print(f"   ✅ utm_prompts table: EXISTS ({prompt_count} prompts)")
        print(f"   ✅ utm_prompts_history table: EXISTS ({history_count} history entries)")
        print()
        
        if prompt_count == 0:
            print("⚠️  No prompts loaded yet!")
            print()
            print("📋 Next Steps:")
            print("   1. Run: python scripts/init_prompts_v4.py --dry-run")
            print("   2. Run: python scripts/init_prompts_v4.py")
            print("   3. Verify: python scripts/verify_prompts_migration.py")
            print()
        else:
            print("✅ Prompts loaded successfully!")
            print()
            print("📋 Test automatic versioning:")
            print("   1. Update a prompt via SQL or save_prompt()")
            print("   2. Check utm_prompts_history table")
            print()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(verify_migration())
    sys.exit(0 if success else 1)

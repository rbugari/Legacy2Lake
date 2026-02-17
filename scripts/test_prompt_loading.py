"""
v4.0: Test Prompt Loading from Database
Purpose: Verify backend can load prompts using get_prompt() method
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
except ImportError:
    try:
        from services.persistence_service import SupabasePersistence
    except ImportError:
        from ..apps.api.services.persistence_service import SupabasePersistence


async def test_prompt_loading():
    """Test loading prompts via get_prompt() method"""
    
    print("=" * 70)
    print("v4.0: Test Backend Prompt Loading")
    print("=" * 70)
    print()
    
    db = SupabasePersistence()
    
    # Test cases
    test_prompts = [
        {
            "prompt_id": "agent_c_interpreter",
            "description": "Agent C interpreter prompt",
            "expected_min_chars": 1000
        },
        {
            "prompt_id": "cartridge_databricks_bronze", 
            "description": "Databricks bronze layer cartridge",
            "expected_min_chars": 500
        },
        {
            "prompt_id": "agent_c_bronze_pyspark",
            "description": "PySpark bronze cartridge",
            "expected_min_chars": 500
        },
        {
            "prompt_id": "coding_standards",
            "description": "Coding standards prompt",
            "expected_min_chars": 100
        }
    ]
    
    results = []
    
    for test in test_prompts:
        print(f"📋 Testing: {test['description']}")
        print(f"   Prompt ID: {test['prompt_id']}")
        
        try:
            # Load prompt using get_prompt()
            content = await db.get_prompt(test['prompt_id'])
            
            if content:
                char_count = len(content)
                min_expected = test['expected_min_chars']
                
                if char_count >= min_expected:
                    print(f"   ✅ Loaded successfully: {char_count} chars (>= {min_expected})")
                    results.append(True)
                else:
                    print(f"   ⚠️  Loaded but too short: {char_count} chars (expected >= {min_expected})")
                    results.append(False)
                
                # Show first 100 chars as preview
                preview = content[:100].replace('\n', ' ')
                print(f"   📄 Preview: {preview}...")
            else:
                print(f"   ❌ FAILED: No content returned")
                results.append(False)
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            results.append(False)
        
        print()
    
    # Summary
    print("=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    total = len(results)
    passed = sum(results)
    failed = total - passed
    
    print(f"   Total tests: {total}")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print()
    
    if failed == 0:
        print("✅ All tests passed! Backend can load prompts from database.")
        print()
        print("📋 Next: Test automatic versioning by updating a prompt")
        return True
    else:
        print(f"⚠️  {failed} test(s) failed. Check database and get_prompt() method.")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_prompt_loading())
    sys.exit(0 if success else 1)

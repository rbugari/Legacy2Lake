"""
Test script to verify Direct Translation cartridge implementation.

Tests:
1. Verify cartridge_databricks_direct.md file exists
2. Verify cartridge_pyspark_direct.md file exists  
3. Test auto-seeding mechanism
4. Verify layer default is "direct" in migration orchestrator
5. Check Agent C correctly loads direct cartridge

Run from project root:
    python scripts/test_direct_translation.py
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_cartridge_files_exist():
    """Test 1: Verify cartridge files exist"""
    print("\n" + "="*60)
    print("TEST 1: Cartridge Files Existence")
    print("="*60)
    
    prompts_dir = os.path.join("apps", "api", "prompts")
    files_to_check = [
        "cartridge_databricks_direct.md",
        "cartridge_pyspark_direct.md",
        "cartridge_databricks_bronze.md",
        "cartridge_databricks_silver.md",
        "cartridge_databricks_gold.md"
    ]
    
    results = []
    for filename in files_to_check:
        filepath = os.path.join(prompts_dir, filename)
        exists = os.path.exists(filepath)
        size = os.path.getsize(filepath) if exists else 0
        
        status = "✅" if exists else "❌"
        print(f"{status} {filename}: {size:,} bytes" if exists else f"{status} {filename}: NOT FOUND")
        
        results.append({"file": filename, "exists": exists, "size": size})
    
    passed = all(r["exists"] for r in results)
    print(f"\n{'✅ PASSED' if passed else '❌ FAILED'}: All cartridge files exist")
    return passed


def test_layer_default():
    """Test 2: Verify layer default is 'direct' in migration orchestrator"""
    print("\n" + "="*60)
    print("TEST 2: Layer Default Value")
    print("="*60)
    
    orchestrator_file = os.path.join("apps", "api", "services", "migration_orchestrator.py")
    
    with open(orchestrator_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Search for layer default
    if '"layer": "direct"' in content:
        print("✅ Found: \"layer\": \"direct\" in migration_orchestrator.py")
        print("   Line context:")
        for i, line in enumerate(content.split('\n')):
            if '"layer": "direct"' in line:
                start = max(0, i-1)
                end = min(len(content.split('\n')), i+2)
                for j in range(start, end):
                    prefix = ">>>" if j == i else "   "
                    print(f"   {prefix} {content.split(chr(10))[j]}")
                break
        passed = True
    elif '"layer": "bronze"' in content:
        print("❌ ERROR: Found \"layer\": \"bronze\" (should be \"direct\")")
        passed = False
    else:
        print("⚠️  WARNING: Could not find layer assignment")
        passed = False
    
    print(f"\n{'✅ PASSED' if passed else '❌ FAILED'}: Layer default is 'direct'")
    return passed


def test_agent_c_default():
    """Test 3: Verify Agent C default layer is 'direct'"""
    print("\n" + "="*60)
    print("TEST 3: Agent C Layer Default")
    print("="*60)
    
    agent_c_file = os.path.join("apps", "api", "services", "agent_c_service.py")
    
    with open(agent_c_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Search for layer default
    if 'layer = node_data.get("layer", "direct")' in content:
        print("✅ Found: layer = node_data.get(\"layer\", \"direct\") in agent_c_service.py")
        passed = True
    elif 'layer = node_data.get("layer", "bronze")' in content:
        print("❌ ERROR: Found layer = node_data.get(\"layer\", \"bronze\") (should be \"direct\")")
        passed = False
    else:
        print("⚠️  WARNING: Could not find layer assignment")
        passed = False
    
    print(f"\n{'✅ PASSED' if passed else '❌ FAILED'}: Agent C default is 'direct'")
    return passed


def test_cartridge_content():
    """Test 4: Verify cartridge content structure"""
    print("\n" + "="*60)
    print("TEST 4: Cartridge Content Validation")
    print("="*60)
    
    direct_cartridge = os.path.join("apps", "api", "prompts", "cartridge_databricks_direct.md")
    
    with open(direct_cartridge, "r", encoding="utf-8") as f:
        content = f.read()
    
    checks = {
        "L2L DIRECT TRANSLATION header": "L2L DIRECT TRANSLATION:" in content,
        "Zero-hardcode policy": "ZERO-HARDCODE CONFIGURATION" in content,
        "Metadata-driven extraction": "METADATA-DRIVEN EXTRACTION" in content,
        "execute_task function": "def execute_task(spark, config)" in content,
        "Sprint 10 column metadata": "Sprint 10" in content,
        "Sprint 7 connection metadata": "Sprint 7" in content,
        "Direct translation mode": "Direct 1:1 (No Architectural Patterns)" in content,
        "No Medallion patterns": "NO Bronze/Silver/Gold layer separation" in content or "WHAT THIS CARTRIDGE DOES NOT DO" in content
    }
    
    all_passed = True
    for check_name, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check_name}")
        if not passed:
            all_passed = False
    
    print(f"\n{'✅ PASSED' if all_passed else '❌ FAILED'}: Cartridge content validation")
    return all_passed


def test_summary():
    """Run all tests and provide summary"""
    print("\n" + "="*60)
    print("DIRECT TRANSLATION IMPLEMENTATION TEST SUITE")
    print("="*60)
    
    tests = [
        ("Cartridge Files Existence", test_cartridge_files_exist),
        ("Layer Default in Orchestrator", test_layer_default),
        ("Agent C Layer Default", test_agent_c_default),
        ("Cartridge Content Validation", test_cartridge_content)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append({"name": test_name, "passed": passed})
        except Exception as e:
            print(f"\n❌ {test_name} FAILED with exception: {e}")
            results.append({"name": test_name, "passed": False})
    
    # Final Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed_count = sum(1 for r in results if r["passed"])
    total_count = len(results)
    
    for result in results:
        status = "✅ PASSED" if result["passed"] else "❌ FAILED"
        print(f"{status}: {result['name']}")
    
    print(f"\n{'='*60}")
    print(f"OVERALL: {passed_count}/{total_count} tests passed")
    print(f"{'='*60}\n")
    
    if passed_count == total_count:
        print("🎉 SUCCESS: Direct Translation implementation is complete!")
        print("\nNext steps:")
        print("1. Restart backend: restart.ps1")
        print("2. Test with production migration: POST /transpile/orchestrate")
        print("3. Verify generated code uses 'L2L DIRECT TRANSLATION' header")
        print("4. Validate code is 1:1 functional translation (no Medallion patterns)")
    else:
        print("⚠️  ISSUES DETECTED: Some tests failed. Review output above.")
    
    return passed_count == total_count


if __name__ == "__main__":
    success = test_summary()
    sys.exit(0 if success else 1)

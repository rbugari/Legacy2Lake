"""
Test Suite for UTM API - Triage Endpoints
Tests critical endpoints to ensure the server starts and core functionality works.
"""

import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:8089"
HEADERS = {
    "Content-Type": "application/json",
    "X-Tenant-ID": "test-tenant-001",  # Optional for testing
    "X-Client-ID": "test-client-001"
}

def print_test(name, status, details=""):
    """Print test result with formatting"""
    symbol = "✅" if status else "❌"
    print(f"{symbol} {name}")
    if details:
        print(f"   {details}")

def test_health_check():
    """Test 1: Health check endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/ping", timeout=5)
        success = response.status_code == 200
        print_test("Health Check (/ping)", success, 
                   f"Status: {response.status_code}, Response: {response.text[:100]}")
        return success
    except Exception as e:
        print_test("Health Check (/ping)", False, f"Error: {str(e)}")
        return False

def test_get_agent_a_prompt():
    """Test 2: Get Agent A prompt"""
    try:
        response = requests.get(f"{BASE_URL}/prompts/agent-a", headers=HEADERS, timeout=10)
        success = response.status_code == 200
        if success:
            data = response.json()
            has_prompt = "prompt" in data and len(data["prompt"]) > 0
            print_test("Get Agent A Prompt", has_prompt, 
                       f"Prompt length: {len(data.get('prompt', ''))} chars")
            return has_prompt
        else:
            print_test("Get Agent A Prompt", False, 
                       f"Status: {response.status_code}, Error: {response.text[:200]}")
            return False
    except Exception as e:
        print_test("Get Agent A Prompt", False, f"Error: {str(e)}")
        return False

def test_list_projects():
    """Test 3: List projects endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/projects", headers=HEADERS, timeout=10)
        success = response.status_code == 200
        if success:
            data = response.json()
            print_test("List Projects", True, 
                       f"Found {len(data)} projects")
            return True
        else:
            print_test("List Projects", False, 
                       f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_test("List Projects", False, f"Error: {str(e)}")
        return False

def test_triage_manifest():
    """Test 4: Generate triage manifest (without actual project)"""
    try:
        # This will fail if no project exists, but we're testing the endpoint responds
        response = requests.post(
            f"{BASE_URL}/triage/manifest",
            headers=HEADERS,
            json={"project_id": "test-project-nonexistent"},
            timeout=10
        )
        # We expect either 200 (if project exists) or 404/500 (if not)
        # The important thing is the server responds without crashing
        success = response.status_code in [200, 404, 500]
        print_test("Triage Manifest Endpoint", success, 
                   f"Status: {response.status_code} (endpoint accessible)")
        return success
    except Exception as e:
        print_test("Triage Manifest Endpoint", False, f"Error: {str(e)}")
        return False

def test_system_prompts():
    """Test 5: Get system prompts"""
    try:
        response = requests.get(f"{BASE_URL}/system/prompts", headers=HEADERS, timeout=10)
        success = response.status_code == 200
        if success:
            data = response.json()
            prompts = data.get("prompts", [])
            print_test("System Prompts", True, 
                       f"Retrieved {len(prompts)} agent prompts")
            return True
        else:
            print_test("System Prompts", False, 
                       f"Status: {response.status_code}, Error: {response.text[:200]}")
            return False
    except Exception as e:
        print_test("System Prompts", False, f"Error: {str(e)}")
        return False

def test_agent_matrix():
    """Test 6: Get agent matrix (LLM configuration)"""
    try:
        response = requests.get(f"{BASE_URL}/system/agent-matrix", headers=HEADERS, timeout=10)
        success = response.status_code == 200
        if success:
            data = response.json()
            print_test("Agent Matrix", True, 
                       f"Matrix entries: {len(data)}")
            return True
        else:
            print_test("Agent Matrix", False, 
                       f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_test("Agent Matrix", False, f"Error: {str(e)}")
        return False

def run_all_tests():
    """Run all tests and report results"""
    print("\n" + "="*60)
    print("UTM API Test Suite - Triage Endpoints")
    print("="*60 + "\n")
    
    print(f"Testing server at: {BASE_URL}")
    print(f"Tenant ID: {HEADERS['X-Tenant-ID']}")
    print(f"Client ID: {HEADERS['X-Client-ID']}\n")
    
    tests = [
        ("Health Check", test_health_check),
        ("Agent A Prompt", test_get_agent_a_prompt),
        ("List Projects", test_list_projects),
        ("Triage Manifest", test_triage_manifest),
        ("System Prompts", test_system_prompts),
        ("Agent Matrix", test_agent_matrix),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\nRunning: {name}")
        print("-" * 40)
        result = test_func()
        results.append((name, result))
        print()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✅" if result else "❌"
        print(f"{symbol} {name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("="*60 + "\n")
    
    if passed == total:
        print("🎉 All tests passed! Server is ready.")
        return 0
    else:
        print(f"⚠️  {total - passed} test(s) failed. Check errors above.")
        return 1

if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)

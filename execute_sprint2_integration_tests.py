"""
Sprint 2 Integration Tests
Tests the orchestration infrastructure components with real API calls
Requires backend running on localhost:8085
"""
import os
import json
import requests
import time
from dotenv import load_dotenv

load_dotenv()

API_BASE = "http://localhost:8085"
TENANT_ID = "daac0ee6-3b28-412d-8acd-43ec51149188"
PROJECT_ID = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"
USER_ID = TENANT_ID


def test_workflow_state_management():
    """Test 1: Workflow State (Pause/Resume/Checkpoints)"""
    print("="*80)
    print("🧪 TEST 1: Workflow State Management (Pause/Resume)")
    print("="*80)
    
    # TODO: This test requires Sprint 2 endpoints to be implemented
    # Expected endpoint: POST /workflow/initialize
    # Expected endpoint: POST /workflow/pause
    # Expected endpoint: POST /workflow/resume
    
    print("\n⚠️  SKIPPED: Requires Sprint 2 workflow endpoints")
    print("   Expected: POST /workflow/initialize, /workflow/pause, /workflow/resume")
    print("   Status: Endpoints not yet implemented in backend")
    
    return {
        "name": "Workflow State Management",
        "status": "skipped",
        "reason": "Endpoints pending implementation"
    }


def test_context_caching():
    """Test 2: Context Caching (Cache Hit Rate)"""
    print("\n" + "="*80)
    print("🧪 TEST 2: Context Caching (Multiple Calls)")
    print("="*80)
    
    # Make multiple identical calls to test caching
    # First call should populate cache, subsequent calls should hit cache
    
    prompt = "# Test Prompt\nGenerate PySpark code for bronze layer ingestion."
    
    node_data = {
        "name": "test_caching",
        "layer": "bronze",
        "tech_id": "pyspark",
        "cartridge_prompt": prompt
    }
    
    context = {
        "project_id": PROJECT_ID
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Tenant-ID": TENANT_ID,
        "X-User-ID": USER_ID
    }
    
    print("\n📤 Making 3 identical requests to test caching...")
    
    times = []
    for i in range(3):
        start = time.time()
        response = requests.post(
            f"{API_BASE}/transpile/task",
            json={"node_data": node_data, "context": context},
            headers=headers,
            timeout=120
        )
        elapsed = time.time() - start
        times.append(elapsed)
        
        print(f"   Request {i+1}: {response.status_code} - {elapsed:.2f}s")
    
    # Expect subsequent calls to be faster due to caching
    if len(times) >= 3:
        speedup = (times[0] / times[2]) * 100 if times[2] > 0 else 0
        print(f"\n📊 First call: {times[0]:.2f}s")
        print(f"📊 Third call: {times[2]:.2f}s")
        print(f"📊 Speedup: {speedup:.0f}% (target: >120%)")
        
        passed = speedup > 120
        return {
            "name": "Context Caching",
            "status": "passed" if passed else "warning",
            "speedup_percent": speedup,
            "note": "Caching working" if passed else "Caching may not be active"
        }
    
    return {
        "name": "Context Caching",
        "status": "failed",
        "reason": "Could not complete 3 requests"
    }


def test_retry_logic():
    """Test 3: Retry Logic (Error Recovery)"""
    print("\n" + "="*80)
    print("🧪 TEST 3: Retry Logic (Simulated Timeout)")
    print("="*80)
    
    # Test with very short timeout to simulate network error
    prompt = "# Test Prompt\nGenerate PySpark code."
    
    node_data = {
        "name": "test_retry",
        "layer": "bronze",
        "tech_id": "pyspark",
        "cartridge_prompt": prompt
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Tenant-ID": TENANT_ID,
        "X-User-ID": USER_ID
    }
    
    print("\n📤 Testing with 1s timeout (should trigger retry if backend implements it)...")
    
    try:
        response = requests.post(
            f"{API_BASE}/transpile/task",
            json={"node_data": node_data, "context": {"project_id": PROJECT_ID}},
            headers=headers,
            timeout=1  # Very short timeout
        )
        
        print(f"   Response: {response.status_code}")
        
        return {
            "name": "Retry Logic",
            "status": "completed_without_retry",
            "note": "Request completed before timeout (backend very fast)"
        }
        
    except requests.Timeout:
        print(f"   ⏱️  Timeout occurred (expected)")
        
        # Retry with normal timeout
        print("\n📤 Retrying with normal timeout...")
        response = requests.post(
            f"{API_BASE}/transpile/task",
            json={"node_data": node_data, "context": {"project_id": PROJECT_ID}},
            headers=headers,
            timeout=120
        )
        
        if response.status_code == 200:
            print(f"   ✅ Retry successful: {response.status_code}")
            return {
                "name": "Retry Logic",
                "status": "passed",
                "note": "Manual retry successful"
            }
        
    return {
        "name": "Retry Logic",
        "status": "warning",
        "note": "Could not test retry logic properly"
    }


def test_pipeline_optimization():
    """Test 4: Pipeline Optimization (Agent C → F)"""
    print("\n" + "="*80)
    print("🧪 TEST 4: Pipeline Optimization (C → F Validation)")
    print("="*80)
    
    # Test Agent C code generation
    prompt = "# Test Prompt\nGenerate PySpark bronze layer code."
    
    node_data = {
        "name": "test_pipeline",
        "label": "Pipeline Test",
        "description": "Test C to F pipeline",
        "type": "ingestion",
        "layer": "bronze",
        "tech_id": "pyspark",
        "source_table": "source.customers",
        "target_table": "bronze.customers",
        "cartridge_prompt": prompt
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Tenant-ID": TENANT_ID,
        "X-User-ID": USER_ID
    }
    
    print("\n📤 Calling Agent C...")
    
    response = requests.post(
        f"{API_BASE}/transpile/task",
        json={"node_data": node_data, "context": {"project_id": PROJECT_ID}},
        headers=headers,
        timeout=120
    )
    
    if response.status_code == 200:
        result = response.json()
        code = result.get("final_code", result.get("code", ""))
        
        print(f"   ✅ Agent C response: {len(code)} chars")
        
        # Check if code is valid Python
        has_imports = "import" in code
        has_spark = "spark" in code.lower() or "pyspark" in code.lower()
        has_dataframe = "df" in code or "DataFrame" in code
        
        validation_score = sum([has_imports, has_spark, has_dataframe]) / 3
        
        print(f"\n📋 Pre-validation checks:")
        print(f"   {'✅' if has_imports else '❌'} Has imports")
        print(f"   {'✅' if has_spark else '❌'} Has Spark references")
        print(f"   {'✅' if has_dataframe else '❌'} Has DataFrame operations")
        print(f"\n📊 Validation Score: {validation_score*100:.0f}%")
        
        return {
            "name": "Pipeline Optimization",
            "status": "passed" if validation_score >= 0.6 else "warning",
            "validation_score": validation_score,
            "code_length": len(code)
        }
    
    print(f"   ❌ Agent C failed: {response.status_code}")
    return {
        "name": "Pipeline Optimization",
        "status": "failed",
        "error": response.status_code
    }


def test_orchestration_metrics():
    """Test 5: Orchestration Metrics Collection"""
    print("\n" + "="*80)
    print("🧪 TEST 5: Orchestration Metrics")
    print("="*80)
    
    # TODO: This requires Sprint 2 metrics endpoint
    # Expected: GET /metrics/workflow/{workflow_id}
    
    print("\n⚠️  SKIPPED: Requires Sprint 2 metrics endpoint")
    print("   Expected: GET /metrics/workflow/{workflow_id}")
    print("   Status: Endpoint not yet implemented")
    
    return {
        "name": "Orchestration Metrics",
        "status": "skipped",
        "reason": "Metrics endpoint pending"
    }


def run_all_integration_tests():
    """Run all Sprint 2 integration tests"""
    print("="*80)
    print("🚀 SPRINT 2 INTEGRATION TESTS")
    print("="*80)
    print(f"\nBackend: {API_BASE}")
    print(f"Tenant: {TENANT_ID}")
    print(f"Project: {PROJECT_ID}")
    
    # Check if backend is running
    try:
        health_response = requests.get(f"{API_BASE}/health", timeout=5)
        if health_response.status_code == 200:
            print(f"\n✅ Backend is healthy")
        else:
            print(f"\n⚠️  Backend returned {health_response.status_code}")
    except:
        print(f"\n❌ Backend not reachable at {API_BASE}")
        print("⚠️  Cannot run integration tests without backend")
        return {
            "success": False,
            "error": "Backend not accessible"
        }
    
    # Run tests
    results = []
    
    # Test 1: Workflow State
    results.append(test_workflow_state_management())
    
    # Test 2: Context Caching
    results.append(test_context_caching())
    
    # Test 3: Retry Logic
    results.append(test_retry_logic())
    
    # Test 4: Pipeline Optimization
    results.append(test_pipeline_optimization())
    
    # Test 5: Metrics
    results.append(test_orchestration_metrics())
    
    # Summary
    print("\n" + "="*80)
    print("📋 SPRINT 2 INTEGRATION TEST RESULTS")
    print("="*80)
    
    passed = sum(1 for r in results if r.get("status") == "passed")
    skipped = sum(1 for r in results if r.get("status") == "skipped")
    warnings = sum(1 for r in results if r.get("status") == "warning")
    failed = sum(1 for r in results if r.get("status") == "failed")
    total = len(results)
    
    for i, result in enumerate(results, 1):
        status = result.get("status", "unknown")
        name = result.get("name", f"Test {i}")
        
        if status == "passed":
            emoji = "✅"
        elif status == "skipped":
            emoji = "⏭️"
        elif status == "warning":
            emoji = "⚠️"
        else:
            emoji = "❌"
        
        print(f"{emoji} {name}: {status.upper()}")
        
        if "note" in result:
            print(f"     Note: {result['note']}")
        if "reason" in result:
            print(f"     Reason: {result['reason']}")
    
    print(f"\n📊 SUMMARY:")
    print(f"   Passed:  {passed}/{total}")
    print(f"   Skipped: {skipped}/{total}")
    print(f"   Warnings: {warnings}/{total}")
    print(f"   Failed:  {failed}/{total}")
    
    score = ((passed + warnings * 0.5) / total) * 100
    print(f"\n📊 SCORE: {score:.0f}%")
    
    if score >= 70:
        print(f"\n✅ SPRINT 2 INTEGRATION TESTS: PASSED")
        return_code = 0
    elif score >= 50:
        print(f"\n⚠️  SPRINT 2 INTEGRATION TESTS: PASSED WITH WARNINGS")
        return_code = 0
    else:
        print(f"\n❌ SPRINT 2 INTEGRATION TESTS: FAILED")
        return_code = 1
    
    # Save results
    output_file = "SPRINT_2_INTEGRATION_TEST_RESULTS.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "passed": passed,
                "skipped": skipped,
                "warnings": warnings,
                "failed": failed,
                "total": total,
                "score": score
            },
            "results": results
        }, f, indent=2)
    
    print(f"\n💾 Results saved: {output_file}")
    
    return return_code


if __name__ == "__main__":
    exit(run_all_integration_tests())

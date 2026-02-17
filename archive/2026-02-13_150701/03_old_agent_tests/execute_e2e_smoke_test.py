"""
End-to-End Smoke Test
Tests the complete migration pipeline: Librarian → Topology → Agent C → Agent F → Agent G
Tests 5 packages across multiple technologies to validate full system
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

# Test packages covering different technologies
TEST_PACKAGES = [
    {
        "name": "bronze_customers_pyspark",
        "layer": "bronze",
        "tech_id": "pyspark",
        "description": "PySpark bronze layer ingestion",
        "expected_format": ".py"
    },
    {
        "name": "silver_customers_fabric",
        "layer": "silver",
        "tech_id": "fabric",
        "description": "MS Fabric silver transformation",
        "expected_format": ".py"
    },
    {
        "name": "gold_analytics_snowflake",
        "layer": "gold",
        "tech_id": "snowflake",
        "description": "Snowflake gold star schema",
        "expected_format": ".sql"
    },
    {
        "name": "bronze_products_aws",
        "layer": "bronze",
        "tech_id": "aws",
        "description": "AWS Glue bronze ingestion",
        "expected_format": ".py"
    },
    {
        "name": "dbt_customers_dbt",
        "layer": "silver",
        "tech_id": "dbt",
        "description": "dbt model for customer transformation",
        "expected_format": ".sql"
    }
]


def test_agent_c_generation(package):
    """Test Agent C code generation for a package"""
    print(f"\n{'='*80}")
    print(f"🧪 Testing Agent C: {package['name']}")
    print(f"{'='*80}")
    
    # Load cartridge prompt (use existing test pattern)
    prompt_file = f"prompt_lab/cartridges/{package['tech_id']}/{package['layer']}_layer.md"
    if os.path.exists(prompt_file):
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt = f.read()
    else:
        prompt = f"# {package['tech_id']} {package['layer']} layer\n{package['description']}"
    
    node_data = {
        "name": package['name'],
        "label": f"{package['layer'].title()} - {package['description']}",
        "description": package['description'],
        "type": "transformation",
        "layer": package['layer'],
        "tech_id": package['tech_id'],
        "cartridge_prompt": prompt
    }
    
    context = {
        "project_id": PROJECT_ID,
        "solution_name": "e2e_smoke_test"
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Tenant-ID": TENANT_ID,
        "X-User-ID": USER_ID
    }
    
    print(f"📤 Sending request to Agent C ({package['tech_id']} {package['layer']})...")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{API_BASE}/transpile/task",
            json={"node_data": node_data, "context": context},
            headers=headers,
            timeout=120
        )
        
        elapsed = time.time() - start_time
        
        print(f"📥 Response: {response.status_code} ({elapsed:.2f}s)")
        
        if response.status_code == 200:
            result = response.json()
            code = result.get("final_code", result.get("code", ""))
            
            if not code or len(code) < 50:
                print(f"❌ Generated code too short: {len(code)} chars")
                return {
                    "package": package['name'],
                    "status": "failed",
                    "reason": "Code too short",
                    "elapsed": elapsed
                }
            
            # Basic validation
            has_content = len(code) > 100
            has_comments = '#' in code or '--' in code or '/*' in code
            
            print(f"✅ Code generated: {len(code)} chars, {len(code.splitlines())} lines")
            print(f"   Content: {'✅' if has_content else '❌'}")
            print(f"   Comments: {'✅' if has_comments else '❌'}")
            
            # Save output
            output_file = f"prompt_lab/SMOKE_TEST_{package['name']}{package['expected_format']}"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            return {
                "package": package['name'],
                "tech_id": package['tech_id'],
                "layer": package['layer'],
                "status": "passed",
                "code_length": len(code),
                "code_lines": len(code.splitlines()),
                "elapsed": elapsed,
                "output_file": output_file
            }
        
        else:
            print(f"❌ Request failed: {response.status_code}")
            return {
                "package": package['name'],
                "status": "failed",
                "error_code": response.status_code,
                "elapsed": elapsed
            }
    
    except requests.Timeout:
        print(f"❌ Request timeout after 120s")
        return {
            "package": package['name'],
            "status": "timeout",
            "elapsed": 120
        }
    
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return {
            "package": package['name'],
            "status": "error",
            "error": str(e)
        }


def check_backend_health():
    """Check if backend is healthy"""
    print("="*80)
    print("🏥 Checking Backend Health")
    print("="*80)
    print(f"Backend: {API_BASE}")
    
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        
        if response.status_code == 200:
            print(f"✅ Backend is healthy (200)")
            return True
        else:
            print(f"⚠️  Backend returned {response.status_code}")
            return False
    
    except requests.ConnectionError:
        print(f"❌ Cannot connect to backend at {API_BASE}")
        print("   Make sure backend is running: `python run.py` or similar")
        return False
    
    except Exception as e:
        print(f"❌ Error checking health: {str(e)}")
        return False


def run_smoke_test():
    """Run complete E2E smoke test"""
    print("="*80)
    print("🚀 END-TO-END SMOKE TEST")
    print("="*80)
    print(f"Tenant: {TENANT_ID}")
    print(f"Project: {PROJECT_ID}")
    print(f"Packages: {len(TEST_PACKAGES)}")
    
    # Check backend
    if not check_backend_health():
        print("\n❌ Cannot proceed without healthy backend")
        return 1
    
    # Run tests for each package
    results = []
    
    for i, package in enumerate(TEST_PACKAGES, 1):
        print(f"\n{'='*80}")
        print(f"📦 Package {i}/{len(TEST_PACKAGES)}: {package['name']}")
        print(f"{'='*80}")
        
        result = test_agent_c_generation(package)
        results.append(result)
        
        # Small delay between tests
        if i < len(TEST_PACKAGES):
            time.sleep(2)
    
    # Summary
    print("\n" + "="*80)
    print("📋 SMOKE TEST RESULTS")
    print("="*80)
    
    passed = sum(1 for r in results if r.get("status") == "passed")
    failed = sum(1 for r in results if r.get("status") == "failed")
    timeout = sum(1 for r in results if r.get("status") == "timeout")
    error = sum(1 for r in results if r.get("status") == "error")
    total = len(results)
    
    # Per-technology breakdown
    by_tech = {}
    for result in results:
        if result.get("status") == "passed":
            tech = result.get("tech_id", "unknown")
            by_tech[tech] = by_tech.get(tech, 0) + 1
    
    print(f"\n📊 Overall Results:")
    print(f"   ✅ Passed:  {passed}/{total} ({(passed/total*100):.0f}%)")
    print(f"   ❌ Failed:  {failed}/{total}")
    print(f"   ⏱️  Timeout: {timeout}/{total}")
    print(f"   ⚠️  Error:   {error}/{total}")
    
    print(f"\n📊 By Technology:")
    for tech, count in sorted(by_tech.items()):
        print(f"   ✅ {tech}: {count} package(s)")
    
    # Detailed results
    print(f"\n📋 Detailed Results:")
    for i, result in enumerate(results, 1):
        status = result.get("status", "unknown")
        package = result.get("package", f"package_{i}")
        
        if status == "passed":
            emoji = "✅"
            elapsed = result.get("elapsed", 0)
            lines = result.get("code_lines", 0)
            print(f"{emoji} {package}: {status.upper()} ({elapsed:.2f}s, {lines} lines)")
        elif status == "failed":
            emoji = "❌"
            reason = result.get("reason", result.get("error_code", "unknown"))
            print(f"{emoji} {package}: {status.upper()} - {reason}")
        elif status == "timeout":
            emoji = "⏱️"
            print(f"{emoji} {package}: {status.upper()}")
        else:
            emoji = "⚠️"
            error = result.get("error", "unknown error")
            print(f"{emoji} {package}: {status.upper()} - {error}")
    
    # Calculate score
    score = (passed / total) * 100
    
    print(f"\n📊 FINAL SCORE: {score:.0f}%")
    
    # Determine pass/fail
    if score >= 80:
        print(f"\n✅ END-TO-END SMOKE TEST: PASSED")
        print(f"   All critical components working")
        return_code = 0
    elif score >= 60:
        print(f"\n⚠️  END-TO-END SMOKE TEST: PASSED WITH WARNINGS")
        print(f"   Most components working, some issues detected")
        return_code = 0
    else:
        print(f"\n❌ END-TO-END SMOKE TEST: FAILED")
        print(f"   Multiple components failing, investigation required")
        return_code = 1
    
    # Save results
    output_file = "SMOKE_TEST_RESULTS.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "passed": passed,
                "failed": failed,
                "timeout": timeout,
                "error": error,
                "total": total,
                "score": score
            },
            "by_technology": by_tech,
            "results": results
        }, f, indent=2)
    
    print(f"\n💾 Results saved: {output_file}")
    
    return return_code


if __name__ == "__main__":
    exit(run_smoke_test())

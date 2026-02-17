"""
Batch test execution - Silver/Gold layers for working cartridges
Executes tests for: PySpark, Snowflake, Fabric, AWS, Generic
"""
import subprocess
import json
import time

def run_test(script_name, test_name):
    """Execute a test script and capture results"""
    print(f"\n{'='*80}")
    print(f"Ejecutando: {test_name}")
    print(f"{'='*80}")
    
    start_time = time.time()
    try:
        result = subprocess.run(
            ["python", script_name],
            capture_output=True,
            text=True,
            timeout=180,
            encoding='utf-8',
            errors='replace'
        )
        
        elapsed = time.time() - start_time
        
        # Extract score from output
        score = "N/A"
        if "SCORE:" in result.stdout or "Quick checks:" in result.stdout:
            for line in result.stdout.split('\n'):
                if "SCORE:" in line or "Quick checks:" in line:
                    score = line.strip()
                    break
        
        status = "✅ PASS" if result.returncode == 0 else "❌ FAIL"
        
        return {
            "test": test_name,
            "script": script_name,
            "status": status,
            "score": score,
            "elapsed": f"{elapsed:.1f}s",
            "return_code": result.returncode
        }
    
    except subprocess.TimeoutExpired:
        return {
            "test": test_name,
            "script": script_name,
            "status": "⏱️ TIMEOUT",
            "score": "N/A",
            "elapsed": "180s+",
            "return_code": -1
        }
    except Exception as e:
        return {
            "test": test_name,
            "script": script_name,
            "status": "💥 ERROR",
            "score": str(e),
            "elapsed": "N/A",
            "return_code": -1
        }

# Test definitions - Silver/Gold for working cartridges
tests = [
    # PySpark already tested Bronze, now Silver/Gold completed
    ("execute_agent_c_silver_test.py", "PYSPARK-SILVER-01"),
    ("execute_agent_c_gold_test.py", "PYSPARK-GOLD-01"),
    
    # Snowflake Silver/Gold
    ("execute_agent_c_snowflake_silver_test.py", "SNOWFLAKE-SILVER-01"),
    ("execute_agent_c_snowflake_gold_test.py", "SNOWFLAKE-GOLD-01"),
    
    # MS Fabric Silver/Gold
    ("execute_agent_c_fabric_silver_test.py", "FABRIC-SILVER-01"),
    ("execute_agent_c_fabric_gold_test.py", "FABRIC-GOLD-01"),
    
    # AWS Glue Silver/Gold
    ("execute_agent_c_aws_silver_test.py", "AWS-SILVER-01"),
    ("execute_agent_c_aws_gold_test.py", "AWS-GOLD-01"),
    
    # Base Generic Silver/Gold
    ("execute_agent_c_generic_silver_test.py", "GENERIC-SILVER-01"),
    ("execute_agent_c_generic_gold_test.py", "GENERIC-GOLD-01"),
]

print("="*80)
print("BATCH TEST EXECUTION - Sprint 0 Day 4")
print(f"Tests to execute: {len(tests)}")
print("="*80)

results = []
for script, test_name in tests:
    result = run_test(script, test_name)
    results.append(result)
    
    # Brief summary after each test
    print(f"\n{result['status']} {test_name} - {result['score']} ({result['elapsed']})")

# Final summary
print("\n" + "="*80)
print("BATCH EXECUTION SUMMARY")
print("="*80)

passed = sum(1 for r in results if r['return_code'] == 0)
failed = sum(1 for r in results if r['return_code'] != 0)

print(f"\nTotal tests: {len(results)}")
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print(f"Pass rate: {passed/len(results)*100:.1f}%")

print("\n" + "-"*80)
print("DETAILED RESULTS:")
print("-"*80)

for r in results:
    print(f"{r['status']} {r['test']:30s} | {r['score']:30s} | {r['elapsed']}")

# Save results to JSON
with open('batch_test_results.json', 'w') as f:
    json.dump(results, f, indent=2)
    
print(f"\n💾 Results saved to: batch_test_results.json")

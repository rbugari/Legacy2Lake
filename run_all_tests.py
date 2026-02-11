"""
Master Test Runner - Execute All Tests and Generate Final Report
Runs all Sprint 0 + Sprint 2 tests in sequence and generates comprehensive report
"""
import os
import sys
import subprocess
import json
import time
from datetime import datetime

# Test categories
CARTRIDGE_TESTS = {
    "PySpark": [
        ("execute_agent_c_test.py", "Bronze"),
        ("execute_agent_c_silver_test.py", "Silver"),
        ("execute_agent_c_gold_test.py", "Gold")
    ],
    "MS Fabric": [
        ("execute_agent_c_fabric_bronze_test.py", "Bronze"),
        ("execute_agent_c_fabric_silver_test.py", "Silver"),
        ("execute_agent_c_fabric_gold_test.py", "Gold")
    ],
    "Generic": [
        ("execute_agent_c_generic_bronze_test.py", "Bronze"),
        ("execute_agent_c_generic_silver_test.py", "Silver"),
        ("execute_agent_c_generic_gold_test.py", "Gold")
    ],
    "dbt": [
        ("execute_agent_c_dbt_bronze_test.py", "Bronze")
    ],
    "GCP BigQuery": [
        ("execute_agent_c_gcp_bronze_test.py", "Bronze")
    ],
    "AWS Glue": [
        ("execute_agent_c_aws_bronze_test.py", "Bronze"),
        ("execute_agent_c_aws_silver_test.py", "Silver"),
        ("execute_agent_c_aws_gold_test.py", "Gold")
    ],
    "Snowflake": [
        ("execute_agent_c_snowflake_bronze_test.py", "Bronze"),
        ("execute_agent_c_snowflake_silver_test.py", "Silver"),
        ("execute_agent_c_snowflake_gold_test.py", "Gold")
    ],
    "Salesforce Data Cloud": [
        ("execute_agent_c_salesforce_bronze_test.py", "Bronze"),
        ("execute_agent_c_salesforce_silver_test.py", "Silver"),
        ("execute_agent_c_salesforce_gold_test.py", "Gold")
    ]
}

INTEGRATION_TESTS = [
    ("execute_sprint2_integration_tests.py", "Sprint 2 Integration Tests"),
    ("execute_e2e_smoke_test.py", "End-to-End Smoke Test")
]


def run_test(script_path, test_name):
    """Run a single test script and return result"""
    print(f"\n{'='*80}")
    print(f"🧪 Running: {test_name}")
    print(f"   Script: {script_path}")
    print(f"{'='*80}")
    
    if not os.path.exists(script_path):
        print(f"⚠️  SKIPPED: Script not found")
        return {
            "name": test_name,
            "script": script_path,
            "status": "skipped",
            "reason": "Script not found"
        }
    
    start_time = time.time()
    
    try:
        # Run test script with UTF-8 encoding
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',  # Replace unencodable characters
            timeout=180  # 3 minutes max per test
        )
        
        elapsed = time.time() - start_time
        
        # Determine status from return code
        if result.returncode == 0:
            status = "passed"
            emoji = "✅"
        else:
            status = "failed"
            emoji = "❌"
        
        print(f"\n{emoji} {test_name}: {status.upper()} ({elapsed:.2f}s)")
        
        # Show last 20 lines of output
        output_lines = result.stdout.splitlines() if result.stdout else []
        if output_lines:
            print(f"\n📄 Output (last 20 lines):")
            for line in output_lines[-20:]:
                print(f"   {line}")
        
        if result.stderr:
            print(f"\n⚠️  Errors:")
            for line in result.stderr.splitlines()[-10:]:
                print(f"   {line}")
        
        return {
            "name": test_name,
            "script": script_path,
            "status": status,
            "return_code": result.returncode,
            "elapsed": elapsed,
            "output_lines": len(output_lines),
            "has_errors": bool(result.stderr)
        }
    
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        print(f"\n⏱️  TIMEOUT: Test exceeded 180s limit")
        return {
            "name": test_name,
            "script": script_path,
            "status": "timeout",
            "elapsed": elapsed
        }
    
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n❌ ERROR: {str(e)}")
        return {
            "name": test_name,
            "script": script_path,
            "status": "error",
            "error": str(e),
            "elapsed": elapsed
        }


def run_all_tests():
    """Run all tests and generate comprehensive report"""
    print("="*80)
    print("🚀 MASTER TEST RUNNER - ALL TESTS")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Cartridge Tests: {sum(len(tests) for tests in CARTRIDGE_TESTS.values())}")
    print(f"Total Integration Tests: {len(INTEGRATION_TESTS)}")
    
    overall_start = time.time()
    
    # Results storage
    all_results = {
        "cartridge_tests": {},
        "integration_tests": []
    }
    
    # Run cartridge tests by technology
    print(f"\n{'='*80}")
    print("📦 CARTRIDGE TESTS (Agent C Code Generation)")
    print(f"{'='*80}")
    
    for tech_name, tests in CARTRIDGE_TESTS.items():
        print(f"\n🔧 Technology: {tech_name}")
        tech_results = []
        
        for script, layer in tests:
            test_name = f"{tech_name} - {layer}"
            result = run_test(script, test_name)
            tech_results.append(result)
            
            # Small delay between tests
            time.sleep(1)
        
        all_results["cartridge_tests"][tech_name] = tech_results
    
    # Run integration tests
    print(f"\n{'='*80}")
    print("🔗 INTEGRATION TESTS")
    print(f"{'='*80}")
    
    for script, test_name in INTEGRATION_TESTS:
        result = run_test(script, test_name)
        all_results["integration_tests"].append(result)
        
        time.sleep(2)
    
    overall_elapsed = time.time() - overall_start
    
    # Generate comprehensive report
    print(f"\n{'='*80}")
    print("📊 FINAL TEST EXECUTION REPORT")
    print(f"{'='*80}")
    
    # Cartridge test summary
    print(f"\n📦 Cartridge Tests by Technology:")
    cartridge_totals = {"passed": 0, "failed": 0, "skipped": 0, "timeout": 0, "error": 0}
    
    for tech_name, tech_results in all_results["cartridge_tests"].items():
        passed = sum(1 for r in tech_results if r.get("status") == "passed")
        total = len(tech_results)
        percentage = (passed / total * 100) if total > 0 else 0
        
        # Update totals
        for result in tech_results:
            status = result.get("status", "error")
            cartridge_totals[status] = cartridge_totals.get(status, 0) + 1
        
        if percentage == 100:
            emoji = "✅"
        elif percentage >= 66:
            emoji = "⚠️"
        else:
            emoji = "❌"
        
        print(f"   {emoji} {tech_name}: {passed}/{total} ({percentage:.0f}%)")
    
    cartridge_total = sum(cartridge_totals.values())
    cartridge_passed = cartridge_totals["passed"]
    cartridge_score = (cartridge_passed / cartridge_total * 100) if cartridge_total > 0 else 0
    
    print(f"\n   Totals:")
    print(f"   ✅ Passed:  {cartridge_totals['passed']}/{cartridge_total} ({cartridge_score:.0f}%)")
    print(f"   ❌ Failed:  {cartridge_totals['failed']}/{cartridge_total}")
    print(f"   ⏭️  Skipped: {cartridge_totals['skipped']}/{cartridge_total}")
    print(f"   ⏱️  Timeout: {cartridge_totals['timeout']}/{cartridge_total}")
    print(f"   ⚠️  Error:   {cartridge_totals['error']}/{cartridge_total}")
    
    # Integration test summary
    print(f"\n🔗 Integration Tests:")
    integration_passed = sum(1 for r in all_results["integration_tests"] if r.get("status") == "passed")
    integration_total = len(all_results["integration_tests"])
    
    for result in all_results["integration_tests"]:
        status = result.get("status", "error")
        name = result.get("name", "Unknown")
        
        if status == "passed":
            emoji = "✅"
        elif status == "skipped":
            emoji = "⏭️"
        else:
            emoji = "❌"
        
        elapsed = result.get("elapsed", 0)
        print(f"   {emoji} {name}: {status.upper()} ({elapsed:.2f}s)")
    
    integration_score = (integration_passed / integration_total * 100) if integration_total > 0 else 0
    print(f"\n   Score: {integration_passed}/{integration_total} ({integration_score:.0f}%)")
    
    # Overall summary
    total_tests = cartridge_total + integration_total
    total_passed = cartridge_passed + integration_passed
    overall_score = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n{'='*80}")
    print(f"📊 OVERALL SUMMARY")
    print(f"{'='*80}")
    print(f"Total Tests:     {total_tests}")
    print(f"Passed:          {total_passed} ({overall_score:.0f}%)")
    print(f"Failed:          {total_tests - total_passed}")
    print(f"Execution Time:  {overall_elapsed:.2f}s ({overall_elapsed/60:.1f} min)")
    
    # Determine final status
    if overall_score >= 90:
        final_status = "✅ EXCELLENT - Production Ready"
        return_code = 0
    elif overall_score >= 80:
        final_status = "✅ PASSED - Minor issues to address"
        return_code = 0
    elif overall_score >= 70:
        final_status = "⚠️  PASSED WITH WARNINGS - Investigation needed"
        return_code = 0
    elif overall_score >= 50:
        final_status = "⚠️  MARGINAL - Significant issues detected"
        return_code = 1
    else:
        final_status = "❌ FAILED - Major system issues"
        return_code = 1
    
    print(f"\n🎯 FINAL STATUS: {final_status}")
    
    # Save comprehensive report
    report_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "execution_time_seconds": overall_elapsed,
        "summary": {
            "total_tests": total_tests,
            "passed": total_passed,
            "failed": total_tests - total_passed,
            "overall_score": overall_score,
            "cartridge_score": cartridge_score,
            "integration_score": integration_score
        },
        "cartridge_tests": all_results["cartridge_tests"],
        "integration_tests": all_results["integration_tests"],
        "final_status": final_status
    }
    
    report_file = "TEST_EXECUTION_FINAL_REPORT.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\n💾 Full report saved: {report_file}")
    
    # Create markdown report
    md_report = generate_markdown_report(report_data)
    md_file = "TEST_EXECUTION_FINAL_REPORT.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(md_report)
    
    print(f"💾 Markdown report saved: {md_file}")
    
    print(f"\n{'='*80}")
    print("✨ TEST EXECUTION COMPLETE")
    print(f"{'='*80}")
    
    return return_code


def generate_markdown_report(report_data):
    """Generate a markdown report from results"""
    md = []
    md.append("# Test Execution Final Report\n")
    md.append(f"**Generated:** {report_data['timestamp']}\n")
    md.append(f"**Execution Time:** {report_data['execution_time_seconds']:.2f}s ({report_data['execution_time_seconds']/60:.1f} min)\n")
    
    md.append("\n## Executive Summary\n")
    summary = report_data['summary']
    md.append(f"- **Total Tests:** {summary['total_tests']}")
    md.append(f"- **Passed:** {summary['passed']} ({summary['overall_score']:.0f}%)")
    md.append(f"- **Failed:** {summary['failed']}")
    md.append(f"- **Final Status:** {report_data['final_status']}\n")
    
    md.append("\n## Cartridge Tests (Agent C Code Generation)\n")
    md.append(f"**Overall Score:** {summary['cartridge_score']:.0f}%\n")
    md.append("\n### By Technology\n")
    
    for tech_name, tech_results in report_data['cartridge_tests'].items():
        passed = sum(1 for r in tech_results if r.get('status') == 'passed')
        total = len(tech_results)
        percentage = (passed / total * 100) if total > 0 else 0
        
        status_emoji = "✅" if percentage == 100 else ("⚠️" if percentage >= 66 else "❌")
        
        md.append(f"\n#### {status_emoji} {tech_name}: {passed}/{total} ({percentage:.0f}%)\n")
        
        for result in tech_results:
            status = result.get('status', 'error')
            name = result.get('name', 'Unknown')
            elapsed = result.get('elapsed', 0)
            
            emoji = "✅" if status == "passed" else ("⏭️" if status == "skipped" else "❌")
            md.append(f"- {emoji} {name}: {status.upper()} ({elapsed:.2f}s)")
    
    md.append("\n\n## Integration Tests\n")
    md.append(f"**Score:** {summary['integration_score']:.0f}%\n")
    
    for result in report_data['integration_tests']:
        status = result.get('status', 'error')
        name = result.get('name', 'Unknown')
        elapsed = result.get('elapsed', 0)
        
        emoji = "✅" if status == "passed" else ("⏭️" if status == "skipped" else "❌")
        md.append(f"- {emoji} {name}: {status.upper()} ({elapsed:.2f}s)")
    
    md.append("\n\n## Recommendations\n")
    
    if summary['overall_score'] >= 90:
        md.append("- ✅ System is production-ready")
        md.append("- ✅ All critical components validated")
        md.append("- ✅ Proceed with deployment")
    elif summary['overall_score'] >= 80:
        md.append("- ⚠️ Address minor issues before production")
        md.append("- ✅ Core functionality working")
        md.append("- 📝 Document known issues")
    elif summary['overall_score'] >= 70:
        md.append("- ⚠️ Investigation required for failing tests")
        md.append("- ⚠️ Validate critical path manually")
        md.append("- 📝 Create fix plan for failures")
    else:
        md.append("- ❌ DO NOT DEPLOY - Major issues detected")
        md.append("- ❌ Debug failing components")
        md.append("- ❌ Re-run tests after fixes")
    
    return "\n".join(md)


if __name__ == "__main__":
    exit(run_all_tests())

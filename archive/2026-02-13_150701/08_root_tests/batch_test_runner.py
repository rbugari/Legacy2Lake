"""
Sprint 5: Batch Testing Framework
Parallel test execution with result aggregation and historical tracking
"""
import subprocess
import concurrent.futures
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import sys

class BatchTestRunner:
    """
    Executes multiple test suites in parallel and aggregates results.
    Supports historical tracking and performance metrics.
    """
    
    def __init__(self, output_dir: str = "test_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.start_time = None
        self.end_time = None
        
    def discover_tests(self) -> List[Dict[str, Any]]:
        """
        Auto-discover test files in workspace.
        Returns list of test configurations.
        """
        test_files = []
        
        # Pattern 1: execute_agent_c_*_test.py (20 cartridge tests)
        cartridge_tests = list(Path(".").glob("execute_agent_c_*_test.py"))
        for test_file in cartridge_tests:
            test_files.append({
                "name": test_file.stem.replace("execute_", "").replace("_test", ""),
                "file": str(test_file),
                "category": "cartridge",
                "timeout": 300  # 5 minutes per cartridge test
            })
        
        # Pattern 2: test_*_integration.py (integration tests)
        integration_tests = list(Path(".").glob("test_*_integration.py"))
        for test_file in integration_tests:
            test_files.append({
                "name": test_file.stem,
                "file": str(test_file),
                "category": "integration",
                "timeout": 600  # 10 minutes for integration
            })
        
        # Pattern 3: test_multi_tenant_*.py (security tests)
        security_tests = list(Path(".").glob("test_multi_tenant_*.py"))
        for test_file in security_tests:
            test_files.append({
                "name": test_file.stem,
                "file": str(test_file),
                "category": "security",
                "timeout": 120  # 2 minutes for security
            })
        
        print(f"📋 Discovered {len(test_files)} test suites:")
        print(f"   - Cartridge tests: {len([t for t in test_files if t['category'] == 'cartridge'])}")
        print(f"   - Integration tests: {len([t for t in test_files if t['category'] == 'integration'])}")
        print(f"   - Security tests: {len([t for t in test_files if t['category'] == 'security'])}")
        
        return test_files
    
    def run_test(self, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single test suite and capture results.
        Returns test result with timing and status.
        """
        test_name = test_config["name"]
        test_file = test_config["file"]
        timeout = test_config["timeout"]
        
        print(f"\n🧪 Running: {test_name} ({test_config['category']})")
        
        result = {
            "name": test_name,
            "file": test_file,
            "category": test_config["category"],
            "start_time": datetime.now().isoformat(),
            "status": "unknown",
            "duration_seconds": 0,
            "exit_code": None,
            "output": "",
            "error": ""
        }
        
        try:
            start = time.time()
            
            # Run test with subprocess
            process = subprocess.run(
                [sys.executable, test_file],
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='replace'
            )
            
            duration = time.time() - start
            
            result.update({
                "end_time": datetime.now().isoformat(),
                "duration_seconds": round(duration, 2),
                "exit_code": process.returncode,
                "output": process.stdout,
                "error": process.stderr,
                "status": "passed" if process.returncode == 0 else "failed"
            })
            
            # Extract pass/fail counts from output if available
            output = process.stdout + process.stderr
            if "tests passing" in output.lower() or "passed" in output.lower():
                result["status"] = "passed"
            elif "failed" in output.lower() or "error" in output.lower():
                result["status"] = "failed"
            
            status_icon = "✅" if result["status"] == "passed" else "❌"
            print(f"   {status_icon} {test_name}: {result['status']} ({duration:.1f}s)")
            
        except subprocess.TimeoutExpired:
            result.update({
                "end_time": datetime.now().isoformat(),
                "duration_seconds": timeout,
                "status": "timeout",
                "error": f"Test exceeded {timeout}s timeout"
            })
            print(f"   ⏱️  {test_name}: TIMEOUT ({timeout}s)")
            
        except Exception as e:
            result.update({
                "end_time": datetime.now().isoformat(),
                "status": "error",
                "error": str(e)
            })
            print(f"   ⚠️  {test_name}: ERROR - {str(e)}")
        
        return result
    
    def run_parallel(self, test_configs: List[Dict[str, Any]], max_workers: int = 4) -> List[Dict[str, Any]]:
        """
        Execute tests in parallel using thread pool.
        Returns list of all test results.
        """
        print(f"\n🚀 Starting parallel execution with {max_workers} workers...")
        print("=" * 80)
        
        self.start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_test = {
                executor.submit(self.run_test, test): test 
                for test in test_configs
            }
            
            results = []
            for future in concurrent.futures.as_completed(future_to_test):
                test = future_to_test[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print(f"   ⚠️  Exception in {test['name']}: {e}")
                    results.append({
                        "name": test["name"],
                        "file": test["file"],
                        "category": test["category"],
                        "status": "exception",
                        "error": str(e)
                    })
        
        self.end_time = time.time()
        
        return results
    
    def aggregate_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate test results into summary statistics.
        """
        total_tests = len(results)
        passed = len([r for r in results if r.get("status") == "passed"])
        failed = len([r for r in results if r.get("status") == "failed"])
        timeout = len([r for r in results if r.get("status") == "timeout"])
        error = len([r for r in results if r.get("status") in ["error", "exception"]])
        
        total_duration = sum(r.get("duration_seconds", 0) for r in results)
        
        # Category breakdown
        by_category = {}
        for result in results:
            category = result.get("category", "unknown")
            if category not in by_category:
                by_category[category] = {
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "timeout": 0,
                    "error": 0
                }
            by_category[category]["total"] += 1
            status = result.get("status", "unknown")
            if status in by_category[category]:
                by_category[category][status] += 1
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "timeout": timeout,
            "error": error,
            "pass_rate": round((passed / total_tests * 100) if total_tests > 0 else 0, 2),
            "total_duration_seconds": round(total_duration, 2),
            "parallel_duration_seconds": round(self.end_time - self.start_time, 2),
            "speedup": round(total_duration / (self.end_time - self.start_time), 2) if self.end_time > self.start_time else 1,
            "by_category": by_category
        }
        
        return summary
    
    def save_results(self, results: List[Dict[str, Any]], summary: Dict[str, Any]):
        """
        Save test results to JSON files with historical tracking.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed results
        results_file = self.output_dir / f"batch_results_{timestamp}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": summary,
                "results": results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {results_file}")
        
        # Update historical tracking
        history_file = self.output_dir / "test_history.json"
        history = []
        
        if history_file.exists():
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        
        history.append({
            "timestamp": summary["timestamp"],
            "total_tests": summary["total_tests"],
            "passed": summary["passed"],
            "failed": summary["failed"],
            "pass_rate": summary["pass_rate"],
            "duration": summary["parallel_duration_seconds"]
        })
        
        # Keep last 100 runs
        history = history[-100:]
        
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2)
        
        print(f"📈 History updated: {history_file} ({len(history)} runs tracked)")
    
    def print_dashboard(self, summary: Dict[str, Any], results: List[Dict[str, Any]]):
        """
        Print ASCII dashboard with test results.
        """
        print("\n" + "=" * 80)
        print("📊 BATCH TEST EXECUTION DASHBOARD")
        print("=" * 80)
        
        # Overall statistics
        print(f"\n{'OVERALL RESULTS':^80}")
        print("-" * 80)
        print(f"Total Tests:     {summary['total_tests']}")
        print(f"✅ Passed:       {summary['passed']} ({summary['pass_rate']}%)")
        print(f"❌ Failed:       {summary['failed']}")
        print(f"⏱️  Timeout:      {summary['timeout']}")
        print(f"⚠️  Errors:       {summary['error']}")
        print(f"\n⏰ Sequential Time: {summary['total_duration_seconds']:.1f}s")
        print(f"⚡ Parallel Time:   {summary['parallel_duration_seconds']:.1f}s")
        print(f"🚀 Speedup:         {summary['speedup']:.2f}x faster")
        
        # Category breakdown
        print(f"\n{'RESULTS BY CATEGORY':^80}")
        print("-" * 80)
        for category, stats in summary["by_category"].items():
            pass_rate = round((stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0, 1)
            print(f"\n{category.upper()} Tests:")
            print(f"  Total: {stats['total']} | Passed: {stats['passed']} | Failed: {stats['failed']} | Pass Rate: {pass_rate}%")
        
        # Failed tests detail
        failed_tests = [r for r in results if r.get("status") in ["failed", "timeout", "error"]]
        if failed_tests:
            print(f"\n{'FAILED TESTS DETAIL':^80}")
            print("-" * 80)
            for test in failed_tests:
                print(f"\n❌ {test['name']} ({test['category']})")
                print(f"   Status: {test.get('status', 'unknown')}")
                print(f"   Duration: {test.get('duration_seconds', 0):.1f}s")
                if test.get('error'):
                    error_lines = test['error'].split('\n')[:3]
                    print(f"   Error: {error_lines[0][:70]}")
        
        print("\n" + "=" * 80)
        
        # Status summary
        if summary['passed'] == summary['total_tests']:
            print("🎉 ALL TESTS PASSED! 🎉")
        elif summary['pass_rate'] >= 90:
            print(f"✅ EXCELLENT: {summary['pass_rate']}% pass rate")
        elif summary['pass_rate'] >= 70:
            print(f"⚠️  GOOD: {summary['pass_rate']}% pass rate (some failures)")
        else:
            print(f"🚨 NEEDS ATTENTION: {summary['pass_rate']}% pass rate")
        
        print("=" * 80 + "\n")


def main():
    """Main entry point for batch test execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Batch Test Runner - Execute tests in parallel")
    parser.add_argument("--workers", type=int, default=4, help="Number of parallel workers (default: 4)")
    parser.add_argument("--category", type=str, help="Filter by category: cartridge, integration, security")
    parser.add_argument("--output", type=str, default="test_results", help="Output directory for results")
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("🧪 SPRINT 5: BATCH TESTING FRAMEWORK")
    print("=" * 80)
    print(f"Workers: {args.workers}")
    print(f"Output: {args.output}")
    if args.category:
        print(f"Filter: {args.category} tests only")
    print("=" * 80)
    
    runner = BatchTestRunner(output_dir=args.output)
    
    # Discover tests
    test_configs = runner.discover_tests()
    
    # Filter by category if specified
    if args.category:
        test_configs = [t for t in test_configs if t["category"] == args.category]
        print(f"\n🔍 Filtered to {len(test_configs)} {args.category} tests")
    
    if not test_configs:
        print("\n⚠️  No tests found to execute!")
        return
    
    # Execute tests in parallel
    results = runner.run_parallel(test_configs, max_workers=args.workers)
    
    # Aggregate and display results
    summary = runner.aggregate_results(results)
    runner.print_dashboard(summary, results)
    
    # Save results
    runner.save_results(results, summary)
    
    # Exit with appropriate code
    sys.exit(0 if summary['failed'] == 0 and summary['error'] == 0 else 1)


if __name__ == "__main__":
    main()

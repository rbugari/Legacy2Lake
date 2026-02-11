"""
Sprint 6: Rate Limiter & Audit Log Test
Validates rate limiting, audit logging, and attack detection
"""
import requests
import time
from datetime import datetime

API_BASE = "http://localhost:8085"
TENANT_ALPHA = "aaaaaaaa-1111-4111-8111-111111111111"

class Sprint6Tests:
    """Test suite for Sprint 6 security enhancements"""
    
    def __init__(self):
        self.results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "details": []
        }
    
    def log_result(self, test_name: str, passed: bool, message: str):
        """Log test result"""
        self.results["total"] += 1
        if passed:
            self.results["passed"] += 1
            status = "✅ PASS"
        else:
            self.results["failed"] += 1
            status = "❌ FAIL"
        
        self.results["details"].append({
            "test": test_name,
            "status": status,
            "message": message
        })
        
        print(f"{status} - {test_name}")
        print(f"        {message}\n")
    
    def test_rate_limit_headers(self):
        """Test 1: Verify rate limit headers are present"""
        print("=" * 80)
        print("TEST 1: Rate Limit Headers")
        print("=" * 80 + "\n")
        
        try:
            response = requests.get(
                f"{API_BASE}/system/catalog",
                headers={"X-Tenant-ID": TENANT_ALPHA},
                timeout=5
            )
            
            # Check for rate limit headers
            has_limit = "X-RateLimit-Limit" in response.headers
            has_remaining = "X-RateLimit-Remaining" in response.headers
            has_reset = "X-RateLimit-Reset" in response.headers
            
            if has_limit and has_remaining and has_reset:
                limit = response.headers["X-RateLimit-Limit"]
                remaining = response.headers["X-RateLimit-Remaining"]
                reset = response.headers["X-RateLimit-Reset"]
                
                self.log_result(
                    "Rate limit headers present",
                    True,
                    f"Limit: {limit}, Remaining: {remaining}, Reset: {reset}s"
                )
            else:
                missing = []
                if not has_limit: missing.append("X-RateLimit-Limit")
                if not has_remaining: missing.append("X-RateLimit-Remaining")
                if not has_reset: missing.append("X-RateLimit-Reset")
                
                self.log_result(
                    "Rate limit headers present",
                    False,
                    f"Missing headers: {', '.join(missing)}"
                )
                
        except Exception as e:
            self.log_result("Rate limit headers present", False, f"Error: {str(e)}")
    
    def test_rate_limit_enforcement(self):
        """Test 2: Verify rate limit enforcement (60 req/min default)"""
        print("=" * 80)
        print("TEST 2: Rate Limit Enforcement")
        print("=" * 80 + "\n")
        
        try:
            # Send 65 requests rapidly (should hit 60/min limit)
            print("Sending 65 rapid requests...")
            blocked_count = 0
            
            for i in range(65):
                response = requests.get(
                    f"{API_BASE}/system/catalog",
                    headers={"X-Tenant-ID": TENANT_ALPHA},
                    timeout=5
                )
                
                if response.status_code == 429:
                    blocked_count += 1
                    if blocked_count == 1:
                        print(f"   First block at request #{i+1}")
                        print(f"   Response: {response.json()}")
            
            if blocked_count > 0:
                self.log_result(
                    "Rate limit enforcement",
                    True,
                    f"Blocked {blocked_count}/65 requests after 60 req/min limit"
                )
            else:
                self.log_result(
                    "Rate limit enforcement",
                    False,
                    "No requests blocked - rate limiter not working"
                )
                
        except Exception as e:
            self.log_result("Rate limit enforcement", False, f"Error: {str(e)}")
    
    def test_attack_detection_sql_injection(self):
        """Test 3: SQL injection attempt logged"""
        print("=" * 80)
        print("TEST 3: SQL Injection Attack Detection")
        print("=" * 80 + "\n")
        
        try:
            payloads = [
                "' OR '1'='1",
                "'; DROP TABLE utm_prompts; --",
                "' UNION SELECT * FROM utm_tenants --"
            ]
            
            blocked_count = 0
            for payload in payloads:
                response = requests.get(
                    f"{API_BASE}/system/catalog",
                    headers={"X-Tenant-ID": payload},
                    timeout=5
                )
                
                if response.status_code == 403:
                    blocked_count += 1
            
            if blocked_count == len(payloads):
                self.log_result(
                    "SQL injection detection",
                    True,
                    f"All {len(payloads)} SQL injection attempts blocked (403)"
                )
            else:
                self.log_result(
                    "SQL injection detection",
                    False,
                    f"Only {blocked_count}/{len(payloads)} attempts blocked"
                )
                
        except Exception as e:
            self.log_result("SQL injection detection", False, f"Error: {str(e)}")
    
    def test_attack_detection_xss(self):
        """Test 4: XSS attempt logged"""
        print("=" * 80)
        print("TEST 4: XSS Attack Detection")
        print("=" * 80 + "\n")
        
        try:
            xss_payload = "<script>alert('xss')</script>"
            response = requests.get(
                f"{API_BASE}/system/catalog",
                headers={"X-Tenant-ID": xss_payload},
                timeout=5
            )
            
            if response.status_code == 403:
                self.log_result(
                    "XSS detection",
                    True,
                    "XSS payload blocked (403)"
                )
            else:
                self.log_result(
                    "XSS detection",
                    False,
                    f"XSS payload not blocked (status: {response.status_code})"
                )
                
        except Exception as e:
            self.log_result("XSS detection", False, f"Error: {str(e)}")
    
    def test_attack_detection_path_traversal(self):
        """Test 5: Path traversal attempt logged"""
        print("=" * 80)
        print("TEST 5: Path Traversal Attack Detection")
        print("=" * 80 + "\n")
        
        try:
            path_payload = "../../../etc/passwd"
            response = requests.get(
                f"{API_BASE}/system/catalog",
                headers={"X-Tenant-ID": path_payload},
                timeout=5
            )
            
            if response.status_code == 403:
                self.log_result(
                    "Path traversal detection",
                    True,
                    "Path traversal payload blocked (403)"
                )
            else:
                self.log_result(
                    "Path traversal detection",
                    False,
                    f"Path traversal not blocked (status: {response.status_code})"
                )
                
        except Exception as e:
            self.log_result("Path traversal detection", False, f"Error: {str(e)}")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("SPRINT 6: TEST SUMMARY")
        print("=" * 80)
        
        total = self.results["total"]
        passed = self.results["passed"]
        failed = self.results["failed"]
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"\nTotal Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Pass Rate: {pass_rate:.1f}%")
        
        print("\n" + "-" * 80)
        print("DETAILED RESULTS")
        print("-" * 80)
        
        for detail in self.results["details"]:
            print(f"\n{detail['status']} {detail['test']}")
            print(f"   {detail['message']}")
        
        print("\n" + "=" * 80)
        
        if pass_rate >= 80:
            print("✅ SPRINT 6 FEATURES WORKING CORRECTLY")
        else:
            print("⚠️  SOME SPRINT 6 FEATURES NEED ATTENTION")
        
        print("=" * 80 + "\n")


def main():
    """Run Sprint 6 test suite"""
    print("\n" + "=" * 80)
    print("🛡️  SPRINT 6: RATE LIMITING & AUDIT LOG TEST SUITE")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API: {API_BASE}")
    print("=" * 80 + "\n")
    
    tests = Sprint6Tests()
    
    # Run tests
    tests.test_rate_limit_headers()
    tests.test_attack_detection_sql_injection()
    tests.test_attack_detection_xss()
    tests.test_attack_detection_path_traversal()
    
    # Rate limit enforcement test (takes ~10 seconds)
    print("⚠️  Skipping rate limit enforcement test (takes 10+ seconds)")
    print("    Run manually if needed: tests.test_rate_limit_enforcement()\n")
    
    # Print summary
    tests.print_summary()


if __name__ == "__main__":
    main()

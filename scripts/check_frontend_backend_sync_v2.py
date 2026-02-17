"""
Frontend-Backend Synchronization Checker v2.0
==============================================
Detects mismatches between FastAPI endpoints and React API calls.

Improvements over v1:
- Fixed TypeScript file detection bug (*.{ts,tsx} pattern)
- Better path normalization (handles /auth, /system prefixes)
- Enhanced method detection (POST, PATCH, DELETE in options)
- Severity classification (Critical vs Warning)
- Actionable recommendations

Usage:
    python scripts/check_frontend_backend_sync_v2.py [--strict]
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Endpoint:
    """Backend FastAPI endpoint"""
    method: str
    path: str
    router_file: str
    line_number: int
    
    def normalized_path(self) -> str:
        """Remove /api/v1 prefix for comparison"""
        path = self.path
        if path.startswith('/api/v1/'):
            return path[8:]
        return path.lstrip('/')


@dataclass
class APICall:
    """Frontend API call via fetchWithAuth"""
    path: str
    method: str
    component_file: str
    line_number: int
    has_error_handling: bool
    
    def normalized_path(self) -> str:
        """Normalize for comparison with backend"""
        path = self.path
        if path.startswith('/api/v1/'):
            return path[8:]
        return path.lstrip('/')


@dataclass
class Issue:
    """Synchronization issue"""
    severity: str  # critical, warning, info
    type: str      # orphaned_call, unused_endpoint, missing_error_handling
    message: str
    file: str
    line_number: int
    suggestion: str = ""


class SyncChecker:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backend_root = project_root / "apps" / "api"
        self.frontend_root = project_root / "apps" / "web"
        
        self.endpoints: List[Endpoint] = []
        self.api_calls: List[APICall] = []
        self.issues: List[Issue] = []
        self.router_mount_prefixes: Dict[str, str] = {}  # router name -> mount prefix
    
    def run(self, strict: bool = False):
        """Run all checks"""
        print("🔍 Starting Frontend-Backend Sync Check v2.0...")
        print(f"   Backend: {self.backend_root}")
        print(f"   Frontend: {self.frontend_root}")
        print()
        
        # Parse main.py for mount prefixes
        self._parse_main_py_mount_prefixes()
        
        # Scan
        self.scan_backend_endpoints()
        self.scan_frontend_api_calls()
        
        print()
        print("🔎 Running synchronization checks...")
        
        # Check
        self.check_orphaned_api_calls()
        self.check_unused_endpoints()
        self.check_missing_error_handling()
        
        # Report
        self.generate_report(strict)
    
    def _parse_main_py_mount_prefixes(self):
        """Parse main.py to extract router mount prefixes"""
        main_py = self.backend_root / "main.py"
        if not main_py.exists():
            print("⚠️  main.py not found, skipping mount prefix detection")
            return
        
        try:
            with open(main_py, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Pattern: app.include_router(some_router, prefix="/something")
            # or app.include_router(module.router, prefix="/something")
            pattern = r'app\.include_router\((\w+)(?:\.router)?,\s*prefix=[\'"]([^\'"]+)[\'"]'
            
            for match in re.finditer(pattern, content):
                router_var = match.group(1)  # e.g., "auth_router" or "system"
                mount_prefix = match.group(2)  # e.g., "/auth"
                
                # Normalize router name (remove _router suffix)
                router_name = router_var.replace('_router', '')
                self.router_mount_prefixes[router_name] = mount_prefix
            
            if self.router_mount_prefixes:
                print(f"📍 Found mount prefixes: {self.router_mount_prefixes}")
        
        except Exception as e:
            print(f"⚠️  Error parsing main.py: {e}")
    
    def scan_backend_endpoints(self):
        """Scan FastAPI routers for endpoints"""
        print("📡 Scanning backend endpoints...")
        
        routers_dir = self.backend_root / "routers"
        if not routers_dir.exists():
            print(f"⚠️  Routers directory not found: {routers_dir}")
            return
        
        for router_file in routers_dir.glob("*.py"):
            self._scan_router_file(router_file)
        
        print(f"   Found {len(self.endpoints)} endpoints")
    
    def _scan_router_file(self, file_path: Path):
        """Scan a single router file for endpoints"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Extract router prefix from APIRouter definition
            router_definition_prefix = ""
            prefix_match = re.search(r'APIRouter\(prefix=[\'"]([^\'"]+)[\'"]', content)
            if prefix_match:
                router_definition_prefix = prefix_match.group(1)
            
            # Get mount prefix from main.py (e.g., auth.py -> /auth)
            router_name = file_path.stem  # e.g., "auth" from "auth.py"
            mount_prefix = self.router_mount_prefixes.get(router_name, "")
            
            # Combine prefixes: mount_prefix + router_definition_prefix
            combined_prefix = mount_prefix + router_definition_prefix
            
            # Find endpoint decorators
            decorator_pattern = r'@router\.(get|post|put|patch|delete)\([\'"]([^\'"]*)[\'"]'
            
            for i, line in enumerate(lines):
                match = re.search(decorator_pattern, line)
                if match:
                    method = match.group(1).upper()
                    path = match.group(2)
                    
                    # Combine all prefixes with endpoint path
                    full_path = combined_prefix + path if combined_prefix else path
                    
                    self.endpoints.append(Endpoint(
                        method=method,
                        path=full_path,
                        router_file=str(file_path.relative_to(self.project_root)),
                        line_number=i + 1
                    ))
        
        except Exception as e:
            print(f"⚠️  Error scanning {file_path.name}: {e}")
    
    def scan_frontend_api_calls(self):
        """Scan React components for fetchWithAuth calls"""
        print("🌐 Scanning frontend API calls...")
        
        app_dir = self.frontend_root / "app"
        if not app_dir.exists():
            print(f"⚠️  Frontend app directory not found: {app_dir}")
            return
        
        # Fixed bug: Need to search for .ts and .tsx separately
        ts_files = list(app_dir.rglob("*.ts"))
        tsx_files = list(app_dir.rglob("*.tsx"))
        all_files = ts_files + tsx_files
        
        for ts_file in all_files:
            if "node_modules" in str(ts_file):
                continue
            self._scan_component_file(ts_file)
        
        print(f"   Found {len(self.api_calls)} API calls")
    
    def _scan_component_file(self, file_path: Path):
        """Scan a single component file for fetchWithAuth calls"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Pattern to match fetchWithAuth calls
            # Handles: fetchWithAuth("path") or fetchWithAuth('path') or fetchWithAuth(`path`)
            fetch_pattern = r'fetchWithAuth\([\'"`]([^\'")`]*)[\'"`]'
            method_pattern = r'method:\s*[\'"](\w+)[\'"]'
            
            for i, line in enumerate(lines):
                match = re.search(fetch_pattern, line)
                if match:
                    path = match.group(1)
                    
                    # Default method is GET
                    method = "GET"
                    
                    # Check next few lines for method specification
                    for j in range(i, min(i + 5, len(lines))):
                        method_match = re.search(method_pattern, lines[j])
                        if method_match:
                            method = method_match.group(1).upper()
                            break
                    
                    # Check if there's error handling
                    has_error_handling = self._check_error_handling(lines, i)
                    
                    self.api_calls.append(APICall(
                        path=path,
                        method=method,
                        component_file=str(file_path.relative_to(self.project_root)),
                        line_number=i + 1,
                        has_error_handling=has_error_handling
                    ))
        
        except Exception as e:
            print(f"⚠️  Error scanning {file_path.name}: {e}")
    
    def _check_error_handling(self, lines: List[str], call_line: int) -> bool:
        """Check if API call has try/catch or .catch()"""
        # Look backwards for try statement
        for i in range(max(0, call_line - 10), call_line):
            if re.search(r'\btry\s*{', lines[i]):
                return True
        
        # Look forward for .catch()
        for i in range(call_line, min(len(lines), call_line + 5)):
            if '.catch(' in lines[i]:
                return True
        
        return False
    
    def _normalize_path_for_matching(self, path: str) -> str:
        """
        Normalize path for comparison by:
        1. Removing query parameters (?...)
        2. Converting template literals ${var} to generic pattern
        3. Converting OpenAPI params {param} to generic pattern
        4. Removing leading/trailing slashes
        """
        # Remove query parameters
        if '?' in path:
            path = path.split('?')[0]
        
        # Convert ${...} to placeholder
        path = re.sub(r'\$\{[^}]+\}', '{var}', path)
        
        # Convert {...} to placeholder
        path = re.sub(r'\{[^}]+\}', '{var}', path)
        
        # Remove leading/trailing slashes
        return path.strip('/')
    
    def check_orphaned_api_calls(self):
        """Check for frontend calls to non-existent endpoints"""
        print("   Checking for orphaned API calls...")
        
        # Build map of normalized endpoints
        normalized_endpoints: Dict[Tuple[str, str], Endpoint] = {}
        for endpoint in self.endpoints:
            normalized = self._normalize_path_for_matching(endpoint.normalized_path())
            key = (endpoint.method, normalized)
            normalized_endpoints[key] = endpoint
        
        orphaned_count = 0
        for call in self.api_calls:
            normalized_call = self._normalize_path_for_matching(call.normalized_path())
            key = (call.method, normalized_call)
            
            # Check if it matches
            if key not in normalized_endpoints:
                orphaned_count += 1
                suggestion = f"Add endpoint {call.method} /{call.normalized_path()} to backend"
                self.issues.append(Issue(
                    severity="critical",
                    type="orphaned_call",
                    message=f"Frontend calls non-existent endpoint: {call.method} /{call.normalized_path()}",
                    file=call.component_file,
                    line_number=call.line_number,
                    suggestion=suggestion
                ))
        
        if orphaned_count == 0:
            print("   ✅ No orphaned API calls found")
        else:
            print(f"   🔴 Found {orphaned_count} orphaned API calls")
    
    def check_unused_endpoints(self):
        """Check for backend endpoints not called by frontend"""
        print("   Checking for unused endpoints...")
        
        # Build set of normalized calls
        normalized_calls: Set[Tuple[str, str]] = set()
        for call in self.api_calls:
            normalized = self._normalize_path_for_matching(call.normalized_path())
            normalized_calls.add((call.method, normalized))
        
        unused_count = 0
        for endpoint in self.endpoints:
            normalized_endpoint = self._normalize_path_for_matching(endpoint.normalized_path())
            key = (endpoint.method, normalized_endpoint)
            
            if key not in normalized_calls:
                unused_count += 1
                suggestion = f"Consider removing if truly unused, or add frontend call"
                self.issues.append(Issue(
                    severity="warning",
                    type="unused_endpoint",
                    message=f"Backend endpoint not called by frontend: {endpoint.method} {endpoint.path}",
                    file=endpoint.router_file,
                    line_number=endpoint.line_number,
                    suggestion=suggestion
                ))
        
        if unused_count == 0:
            print("   ✅ All endpoints are used")
        else:
            print(f"   ⚠️  Found {unused_count} unused endpoints")
    
    def check_missing_error_handling(self):
        """Check for API calls without error handling"""
        print("   Checking for missing error handling...")
        
        missing_count = 0
        for call in self.api_calls:
            if not call.has_error_handling:
                missing_count += 1
                suggestion = "Add try/catch block or .catch() handler"
                self.issues.append(Issue(
                    severity="warning",
                    type="missing_error_handling",
                    message=f"API call without error handling: {call.method} /{call.normalized_path()}",
                    file=call.component_file,
                    line_number=call.line_number,
                    suggestion=suggestion
                ))
        
        if missing_count == 0:
            print("   ✅ All API calls have error handling")
        else:
            print(f"   ⚠️  Found {missing_count} calls without error handling")
    
    def generate_report(self, strict: bool):
        """Generate and save report"""
        # Save JSON report
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_endpoints": len(self.endpoints),
                "total_api_calls": len(self.api_calls),
                "total_issues": len(self.issues),
                "critical": len([i for i in self.issues if i.severity == "critical"]),
                "warnings": len([i for i in self.issues if i.severity == "warning"]),
                "info": len([i for i in self.issues if i.severity == "info"])
            },
            "endpoints": [asdict(e) for e in self.endpoints],
            "api_calls": [asdict(c) for c in self.api_calls],
            "issues": [asdict(i) for i in self.issues]
        }
        
        output_file = self.project_root / "output" / "sync_check_report_v2.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)
        
        print()
        print(f"📄 Report saved to: {output_file}")
        
        # Print summary
        self._print_summary(report_data["summary"])
        
        # Print issues
        self._print_issues(strict)
    
    def _print_summary(self, summary: Dict):
        """Print summary table"""
        print()
        print("="*70)
        print("📊 SYNC CHECK SUMMARY")
        print("="*70)
        print(f"Total Backend Endpoints: {summary['total_endpoints']}")
        print(f"Total Frontend API Calls: {summary['total_api_calls']}")
        print(f"Total Issues Found: {summary['total_issues']}")
        print(f"  - Critical: {summary['critical']}")
        print(f"  - Warnings: {summary['warnings']}")
        print(f"  - Info: {summary['info']}")
        print("="*70)
    
    def _print_issues(self, strict: bool):
        """Print issues grouped by severity"""
        critical = [i for i in self.issues if i.severity == "critical"]
        warnings = [i for i in self.issues if i.severity == "warning"]
        info = [i for i in self.issues if i.severity == "info"]
        
        # Critical issues (always show)
        if critical:
            print()
            print("🔴 Critical Issues:")
            for issue in critical[:10]:  # Limit to first 10
                print(f"\n   - {issue.message}")
                print(f"     File: {issue.file}:{issue.line_number}")
                print(f"     💡 {issue.suggestion}")
            
            if len(critical) > 10:
                print(f"\n   ... and {len(critical) - 10} more critical issues")
        
        # Warnings (show first 10 unless strict mode)
        if warnings:
            print()
            print("⚠️  Warnings:")
            limit = len(warnings) if strict else 10
            for issue in warnings[:limit]:
                print(f"\n   - {issue.message}")
                print(f"     File: {issue.file}:{issue.line_number}")
                print(f"     💡 {issue.suggestion}")
            
            if len(warnings) > limit:
                print(f"\n   ... and {len(warnings) - limit} more warnings")
        
        # Info (only in strict mode)
        if info and strict:
            print()
            print("ℹ️  Info:")
            for issue in info[:10]:
                print(f"\n   - {issue.message}")
                print(f"     File: {issue.file}:{issue.line_number}")
        
        # Final verdict
        print()
        if critical:
            print("❌ FAILED: Critical issues found")
            if not strict:
                print("   Run with --strict to see all issues")
        elif warnings:
            print("⚠️  PASSED WITH WARNINGS")
            if not strict:
                print("   Run with --strict to see all issues")
        else:
            print("✅ ALL CHECKS PASSED!")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Check frontend-backend synchronization")
    parser.add_argument("--strict", action="store_true", help="Show all issues (no limits)")
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent
    checker = SyncChecker(project_root)
    checker.run(strict=args.strict)


if __name__ == "__main__":
    main()

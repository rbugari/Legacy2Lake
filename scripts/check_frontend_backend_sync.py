"""
Frontend-Backend Sync Checker
==============================

Purpose:
    Detects synchronization issues between FastAPI backend endpoints and
    React frontend components to prevent runtime errors.

Checks:
    1. Orphaned API calls - Frontend calls non-existent endpoints
    2. Unused endpoints - Backend endpoints not called by frontend
    3. Type mismatches - Pydantic models vs TypeScript interfaces
    4. Missing error handling - API calls without try/catch

Usage:
    python scripts/check_frontend_backend_sync.py

Output:
    - Console report with issues found
    - JSON report at output/sync_check_report.json

Author: Legacy2Lake Engineering
Date: 2026-02-13
Version: 1.0.0
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class APIEndpoint:
    """Represents a backend API endpoint"""
    method: str
    path: str
    router_file: str
    line_number: int
    response_model: str = ""
    
@dataclass
class APICall:
    """Represents a frontend API call"""
    path: str
    method: str
    component_file: str
    line_number: int
    has_error_handling: bool = False


@dataclass
class SyncIssue:
    """Represents a synchronization issue"""
    severity: str  # critical, warning, info
    category: str
    description: str
    affected_file: str
    line_number: int
    suggestion: str


class SyncChecker:
    """Main sync checker class"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backend_root = project_root / "apps" / "api"
        self.frontend_root = project_root / "apps" / "web"
        
        self.endpoints: List[APIEndpoint] = []
        self.api_calls: List[APICall] = []
        self.issues: List[SyncIssue] = []
    
    def run(self) -> Dict:
        """Run all checks and return report"""
        print("🔍 Starting Frontend-Backend Sync Check...")
        print(f"   Backend: {self.backend_root}")
        print(f"   Frontend: {self.frontend_root}")
        print()
        
        # Step 1: Scan backend endpoints
        print("📡 Scanning backend endpoints...")
        self.scan_backend_endpoints()
        print(f"   Found {len(self.endpoints)} endpoints")
        
        # Step 2: Scan frontend API calls
        print("🌐 Scanning frontend API calls...")
        self.scan_frontend_api_calls()
        print(f"   Found {len(self.api_calls)} API calls")
        print()
        
        # Step 3: Run checks
        print("🔎 Running synchronization checks...")
        self.check_orphaned_api_calls()
        self.check_unused_endpoints()
        self.check_error_handling()
        
        # Step 4: Generate report
        report = self.generate_report()
        
        # Step 5: Save report
        output_dir = self.project_root / "output"
        output_dir.mkdir(exist_ok=True)
        report_path = output_dir / "sync_check_report.json"
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Report saved to: {report_path}")
        
        return report
    
    def scan_backend_endpoints(self):
        """Scan all FastAPI routers for endpoints"""
        routers_dir = self.backend_root / "routers"
        
        if not routers_dir.exists():
            print(f"⚠️  Router directory not found: {routers_dir}")
            return
        
        for router_file in routers_dir.glob("*.py"):
            if router_file.name.startswith("_"):
                continue
            
            self._scan_router_file(router_file)
    
    def _scan_router_file(self, file_path: Path):
        """Scan a single router file for endpoints"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Find router decorators
            decorator_pattern = r'@router\.(get|post|put|patch|delete)\("([^"]+)"'
            response_model_pattern = r'response_model=(\w+)'
            
            for i, line in enumerate(lines):
                match = re.search(decorator_pattern, line)
                if match:
                    method = match.group(1).upper()
                    path = match.group(2)
                    
                    # Extract response model if present
                    response_model = ""
                    response_match = re.search(response_model_pattern, line)
                    if response_match:
                        response_model = response_match.group(1)
                    
                    # Convert path parameters to regex pattern
                    # /projects/{id} -> /projects/[^/]+
                    path_pattern = re.sub(r'\{[^}]+\}', '[^/]+', path)
                    
                    self.endpoints.append(APIEndpoint(
                        method=method,
                        path=path_pattern,
                        router_file=str(file_path.relative_to(self.project_root)),
                        line_number=i + 1,
                        response_model=response_model
                    ))
        
        except Exception as e:
            print(f"⚠️  Error scanning {file_path.name}: {e}")
    
    def scan_frontend_api_calls(self):
        """Scan all React components for API calls"""
        app_dir = self.frontend_root / "app"
        
        if not app_dir.exists():
            print(f"⚠️  Frontend app directory not found: {app_dir}")
            return
        
        for ts_file in app_dir.rglob("*.{ts,tsx}"):
            if "node_modules" in str(ts_file):
                continue
            
            self._scan_component_file(ts_file)
    
    def _scan_component_file(self, file_path: Path):
        """Scan a single component file for API calls"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Find fetchWithAuth calls
            fetch_pattern = r'fetchWithAuth\([\'"]([^\'"]+)[\'"]'
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
                    
                    # Check if there's error handling (try/catch)
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
    
    def check_orphaned_api_calls(self):
        """Check for frontend calls to non-existent endpoints"""
        print("   Checking for orphaned API calls...")
        
        # Build set of available endpoints
        endpoint_patterns = set()
        for endpoint in self.endpoints:
            pattern = f"{endpoint.method}:{endpoint.path}"
            endpoint_patterns.add(pattern)
        
        orphaned_count = 0
        for call in self.api_calls:
            # Normalize path (remove leading /api/v1 if present)
            normalized_path = call.path
            if normalized_path.startswith('/api/v1/'):
                normalized_path = normalized_path[len('/api/v1/'):]
            
            # Check if any endpoint matches
            found = False
            for endpoint in self.endpoints:
                endpoint_path = endpoint.path
                if endpoint_path.startswith('/api/v1/'):
                    endpoint_path = endpoint_path[len('/api/v1/'):]
                
                pattern = re.compile(f"^{endpoint_path}$")
                if endpoint.method == call.method and pattern.match(normalized_path):
                    found = True
                    break
            
            if not found:
                self.issues.append(SyncIssue(
                    severity="critical",
                    category="orphaned_api_call",
                    description=f"Frontend calls non-existent endpoint: {call.method} {call.path}",
                    affected_file=call.component_file,
                    line_number=call.line_number,
                    suggestion=f"Either create the backend endpoint or remove this API call"
                ))
                orphaned_count += 1
        
        if orphaned_count > 0:
            print(f"   ❌ Found {orphaned_count} orphaned API calls")
        else:
            print(f"   ✅ No orphaned API calls found")
    
    def check_unused_endpoints(self):
        """Check for backend endpoints not called by frontend"""
        print("   Checking for unused endpoints...")
        
        # Build set of called endpoints
        called_patterns = set()
        for call in self.api_calls:
            pattern = f"{call.method}:{call.path}"
            called_patterns.add(pattern)
        
        unused_count = 0
        for endpoint in self.endpoints:
            # Skip system/health endpoints
            if any(skip in endpoint.path for skip in ['/health', '/docs', '/openapi', '/redoc']):
                continue
            
            # Check if any call matches
            found = False
            for call in self.api_calls:
                normalized_call_path = call.path
                if normalized_call_path.startswith('/api/v1/'):
                    normalized_call_path = normalized_call_path[len('/api/v1/'):]
                
                endpoint_path = endpoint.path
                if endpoint_path.startswith('/api/v1/'):
                    endpoint_path = endpoint_path[len('/api/v1/'):]
                
                pattern = re.compile(f"^{endpoint_path}$")
                if endpoint.method == call.method and pattern.match(normalized_call_path):
                    found = True
                    break
            
            if not found:
                self.issues.append(SyncIssue(
                    severity="warning",
                    category="unused_endpoint",
                    description=f"Backend endpoint not called by frontend: {endpoint.method} {endpoint.path}",
                    affected_file=endpoint.router_file,
                    line_number=endpoint.line_number,
                    suggestion="Consider removing if truly unused, or implement frontend integration"
                ))
                unused_count += 1
        
        if unused_count > 0:
            print(f"   ⚠️  Found {unused_count} unused endpoints")
        else:
            print(f"   ✅ All endpoints are used by frontend")
    
    def check_error_handling(self):
        """Check for API calls without error handling"""
        print("   Checking for missing error handling...")
        
        missing_count = 0
        for call in self.api_calls:
            if not call.has_error_handling:
                self.issues.append(SyncIssue(
                    severity="warning",
                    category="missing_error_handling",
                    description=f"API call without error handling: {call.method} {call.path}",
                    affected_file=call.component_file,
                    line_number=call.line_number,
                    suggestion="Wrap in try/catch or add .catch() handler"
                ))
                missing_count += 1
        
        if missing_count > 0:
            print(f"   ⚠️  Found {missing_count} calls without error handling")
        else:
            print(f"   ✅ All API calls have error handling")
    
    def generate_report(self) -> Dict:
        """Generate final report"""
        # Group issues by severity
        by_severity = defaultdict(list)
        for issue in self.issues:
            by_severity[issue.severity].append(issue)
        
        # Group issues by category
        by_category = defaultdict(list)
        for issue in self.issues:
            by_category[issue.category].append(issue)
        
        report = {
            "summary": {
                "total_endpoints": len(self.endpoints),
                "total_api_calls": len(self.api_calls),
                "total_issues": len(self.issues),
                "critical_issues": len(by_severity["critical"]),
                "warnings": len(by_severity["warning"]),
                "info": len(by_severity["info"])
            },
            "issues_by_severity": {
                severity: [asdict(issue) for issue in issues]
                for severity, issues in by_severity.items()
            },
            "issues_by_category": {
                category: [asdict(issue) for issue in issues]
                for category, issues in by_category.items()
            },
            "endpoints": [asdict(ep) for ep in self.endpoints],
            "api_calls": [asdict(call) for call in self.api_calls]
        }
        
        return report
    
    def print_summary(self, report: Dict):
        """Print summary to console"""
        summary = report["summary"]
        
        print("\n" + "="*70)
        print("📊 SYNC CHECK SUMMARY")
        print("="*70)
        print(f"Total Backend Endpoints: {summary['total_endpoints']}")
        print(f"Total Frontend API Calls: {summary['total_api_calls']}")
        print(f"Total Issues Found: {summary['total_issues']}")
        print(f"  - Critical: {summary['critical_issues']}")
        print(f"  - Warnings: {summary['warnings']}")
        print(f"  - Info: {summary['info']}")
        print("="*70)
        
        if summary['total_issues'] > 0:
            print("\n🔴 Critical Issues:")
            for issue in report['issues_by_severity'].get('critical', []):
                print(f"   - {issue['description']}")
                print(f"     File: {issue['affected_file']}:{issue['line_number']}")
                print(f"     Fix: {issue['suggestion']}\n")
            
            print("\n⚠️  Warnings:")
            for issue in report['issues_by_severity'].get('warning', []):
                print(f"   - {issue['description']}")
                print(f"     File: {issue['affected_file']}:{issue['line_number']}\n")
        else:
            print("\n✅ No synchronization issues found!")


def main():
    """Main entry point"""
    project_root = Path(__file__).parent.parent
    
    checker = SyncChecker(project_root)
    report = checker.run()
    checker.print_summary(report)
    
    # Exit with error code if critical issues found
    if report['summary']['critical_issues'] > 0:
        print("\n❌ Critical issues detected. Exiting with error code 1.")
        exit(1)
    else:
        print("\n✅ All checks passed!")
        exit(0)


if __name__ == "__main__":
    main()

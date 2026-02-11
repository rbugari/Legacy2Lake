"""
Sprint 6: Audit Log Service
Comprehensive logging for security, compliance, and forensics
"""
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
import json
import hashlib
from pathlib import Path

class AuditEventType(Enum):
    """Types of auditable events"""
    # Authentication
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    AUTH_INVALID_TENANT = "auth_invalid_tenant"
    
    # Security
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    XSS_ATTEMPT = "xss_attempt"
    PATH_TRAVERSAL_ATTEMPT = "path_traversal_attempt"
    INVALID_UUID = "invalid_uuid"
    DUPLICATE_HEADERS = "duplicate_headers"
    
    # API Operations
    API_REQUEST = "api_request"
    API_ERROR = "api_error"
    
    # Data Access
    CROSS_TENANT_ACCESS_ATTEMPT = "cross_tenant_access_attempt"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    
    # Admin Actions
    ADMIN_IMPERSONATION = "admin_impersonation"
    ADMIN_ACTION = "admin_action"


class AuditSeverity(Enum):
    """Severity levels for audit events"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditLogService:
    """
    Centralized audit logging service.
    
    Features:
    - Multi-backend support (DB, file, stdout)
    - Structured logging (JSON format)
    - PII masking (sensitive data protection)
    - Attack pattern detection
    - Compliance reporting
    """
    
    def __init__(self, supabase_client=None, log_dir: str = "logs"):
        self.supabase = supabase_client
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Attack detection counters
        self.attack_patterns = {
            "sql_injection": 0,
            "xss": 0,
            "path_traversal": 0,
            "brute_force": 0
        }
    
    def log_event(
        self,
        event_type: AuditEventType,
        severity: AuditSeverity,
        message: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        status_code: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        skip_detection: bool = False  # Sprint 6 fix: prevent recursion
    ):
        """
        Log an audit event to all configured backends.
        
        Args:
            event_type: Type of event (use AuditEventType enum)
            severity: Severity level (use AuditSeverity enum)
            message: Human-readable description
            tenant_id: Tenant ID (if applicable)
            user_id: User ID (if applicable)
            ip_address: Client IP address
            endpoint: API endpoint path
            method: HTTP method
            status_code: HTTP response status
            metadata: Additional context (dict)
            skip_detection: Skip attack pattern detection (prevents recursion)
        """
        timestamp = datetime.utcnow()
        
        # Build audit record
        audit_record = {
            "timestamp": timestamp.isoformat(),
            "event_type": event_type.value,
            "severity": severity.value,
            "message": message,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "ip_address": self._mask_ip(ip_address) if ip_address else None,
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "metadata": metadata or {}
        }
        
        # Remove None values
        audit_record = {k: v for k, v in audit_record.items() if v is not None}
        
        # Write to backends
        self._write_to_file(audit_record)
        self._write_to_db(audit_record)
        self._write_to_stdout(audit_record)
        
        # Check for attack patterns (skip if called from _trigger_alert to prevent recursion)
        if not skip_detection:
            self._detect_attack_pattern(audit_record)
    
    def _mask_ip(self, ip: str) -> str:
        """Mask IP address for PII compliance (keep first 2 octets)"""
        parts = ip.split(".")
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.xxx.xxx"
        return hashlib.md5(ip.encode()).hexdigest()[:16]  # Hash for IPv6
    
    def _write_to_file(self, record: Dict):
        """Write audit log to daily file"""
        try:
            date_str = datetime.utcnow().strftime("%Y%m%d")
            log_file = self.log_dir / f"audit_log_{date_str}.jsonl"
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"[AUDIT] Failed to write to file: {e}")
    
    def _write_to_db(self, record: Dict):
        """Write audit log to Supabase utm_audit_log table"""
        if not self.supabase:
            return
        
        try:
            # Map to DB schema
            db_record = {
                "timestamp": record["timestamp"],
                "event_type": record["event_type"],
                "severity": record["severity"],
                "message": record["message"],
                "tenant_id": record.get("tenant_id"),
                "user_id": record.get("user_id"),
                "ip_address": record.get("ip_address"),
                "endpoint": record.get("endpoint"),
                "method": record.get("method"),
                "status_code": record.get("status_code"),
                "metadata": record.get("metadata", {})
            }
            
            # TODO: Make this async to avoid blocking requests
            # For now, skip DB writes to prevent timeouts
            # self.supabase.table("utm_audit_log").insert(db_record).execute()
            pass  # Temporarily disabled - file and stdout logging still active
            
        except Exception as e:
            # Don't fail request if audit logging fails
            print(f"[AUDIT] Failed to write to DB: {e}")
    
    def _write_to_stdout(self, record: Dict):
        """Write audit log to console (for development)"""
        severity_icons = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "critical": "🚨"
        }
        
        icon = severity_icons.get(record["severity"], "📝")
        event_type = record["event_type"]
        message = record["message"]
        
        # Only print warnings and above in production
        if record["severity"] in ["warning", "error", "critical"]:
            print(f"[AUDIT] {icon} {event_type.upper()}: {message}")
    
    def _detect_attack_pattern(self, record: Dict):
        """Detect coordinated attack patterns and trigger alerts"""
        event_type = record["event_type"]
        
        # Increment attack counters
        if event_type == "sql_injection_attempt":
            self.attack_patterns["sql_injection"] += 1
        elif event_type == "xss_attempt":
            self.attack_patterns["xss"] += 1
        elif event_type == "path_traversal_attempt":
            self.attack_patterns["path_traversal"] += 1
        elif event_type == "auth_failure":
            self.attack_patterns["brute_force"] += 1
        
        # Check thresholds (5 attacks in current session)
        for attack_type, count in self.attack_patterns.items():
            if count >= 5:
                self._trigger_alert(attack_type, count, record)
    
    def _trigger_alert(self, attack_type: str, count: int, record: Dict):
        """Trigger security alert (log critical event)"""
        alert_message = f"🚨 SECURITY ALERT: {count} {attack_type} attempts detected from IP {record.get('ip_address')}"
        
        print(f"\n{'='*80}")
        print(alert_message)
        print(f"Latest attempt: {record.get('message')}")
        print(f"Endpoint: {record.get('endpoint')}")
        print(f"Tenant: {record.get('tenant_id', 'Unknown')}")
        print(f"{'='*80}\n")
        
        # Log critical alert (skip_detection=True to prevent recursion)
        self.log_event(
            event_type=AuditEventType.API_ERROR,
            severity=AuditSeverity.CRITICAL,
            message=alert_message,
            ip_address=record.get("ip_address"),
            tenant_id=record.get("tenant_id"),
            metadata={
                "attack_type": attack_type,
                "attempt_count": count,
                "original_event": record
            },
            skip_detection=True  # Sprint 6 fix: prevent infinite recursion
        )
    
    def log_auth_attempt(
        self,
        success: bool,
        tenant_id: Optional[str],
        user_id: Optional[str],
        ip_address: str,
        reason: Optional[str] = None
    ):
        """Convenience method for logging authentication attempts"""
        if success:
            self.log_event(
                event_type=AuditEventType.AUTH_SUCCESS,
                severity=AuditSeverity.INFO,
                message=f"Successful authentication for tenant {tenant_id}",
                tenant_id=tenant_id,
                user_id=user_id,
                ip_address=ip_address
            )
        else:
            self.log_event(
                event_type=AuditEventType.AUTH_FAILURE,
                severity=AuditSeverity.WARNING,
                message=f"Failed authentication: {reason or 'Unknown'}",
                tenant_id=tenant_id,
                user_id=user_id,
                ip_address=ip_address,
                metadata={"reason": reason}
            )
    
    def log_security_violation(
        self,
        violation_type: str,
        attempted_value: str,
        ip_address: str,
        endpoint: str,
        tenant_id: Optional[str] = None
    ):
        """Convenience method for logging security violations"""
        event_map = {
            "sql_injection": AuditEventType.SQL_INJECTION_ATTEMPT,
            "xss": AuditEventType.XSS_ATTEMPT,
            "path_traversal": AuditEventType.PATH_TRAVERSAL_ATTEMPT,
            "invalid_uuid": AuditEventType.INVALID_UUID
        }
        
        event_type = event_map.get(violation_type, AuditEventType.API_ERROR)
        
        # Truncate attempted value to prevent log flooding
        attempted_value_safe = attempted_value[:100] if attempted_value else "N/A"
        
        self.log_event(
            event_type=event_type,
            severity=AuditSeverity.ERROR,
            message=f"{violation_type.upper()} attempt detected: {attempted_value_safe}",
            tenant_id=tenant_id,
            ip_address=ip_address,
            endpoint=endpoint,
            metadata={
                "violation_type": violation_type,
                "attempted_value": attempted_value_safe
            }
        )
    
    def log_api_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration_ms: float,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ):
        """Log API request (only errors and slow requests)"""
        # Only log errors or slow requests (>5 seconds)
        if status_code >= 400 or duration_ms > 5000:
            severity = AuditSeverity.ERROR if status_code >= 400 else AuditSeverity.WARNING
            
            self.log_event(
                event_type=AuditEventType.API_REQUEST if status_code < 500 else AuditEventType.API_ERROR,
                severity=severity,
                message=f"{method} {endpoint} returned {status_code} in {duration_ms:.0f}ms",
                tenant_id=tenant_id,
                user_id=user_id,
                ip_address=ip_address,
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                metadata={"duration_ms": duration_ms}
            )
    
    def get_recent_attacks(self, hours: int = 24, limit: int = 100) -> list:
        """Retrieve recent attack attempts from audit log"""
        if not self.supabase:
            return []
        
        try:
            from datetime import timedelta
            cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
            
            response = self.supabase.table("utm_audit_log") \
                .select("*") \
                .gte("timestamp", cutoff) \
                .in_("event_type", [
                    "sql_injection_attempt",
                    "xss_attempt",
                    "path_traversal_attempt",
                    "auth_failure"
                ]) \
                .order("timestamp", desc=True) \
                .limit(limit) \
                .execute()
            
            return response.data if response.data else []
        except Exception as e:
            print(f"[AUDIT] Failed to retrieve recent attacks: {e}")
            return []


# Global audit service instance (will be initialized in main.py with Supabase client)
_audit_service: Optional[AuditLogService] = None


def init_audit_service(supabase_client):
    """Initialize global audit service with Supabase client"""
    global _audit_service
    _audit_service = AuditLogService(supabase_client)
    print("✅ Audit log service initialized")


def get_audit_service() -> AuditLogService:
    """Get global audit service instance"""
    if _audit_service is None:
        # Return basic service without DB support if not initialized
        return AuditLogService()
    return _audit_service

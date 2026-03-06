"""
QualityRuleEngine - Sprint 11: Data Quality Framework

Purpose: Define and evaluate data quality rules against tables and columns.
Supports multiple rule types: nullability, ranges, formats, uniqueness, referential integrity.

This service enables:
- Configurable quality rules per table/column
- Automatic rule evaluation
- Violation detection and logging
- Quality scoring (0-100%)
- Historical quality tracking

Author: UTM Platform Team
Created: February 11, 2026
Sprint: 11 (Data Quality Framework)
"""

from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import re
from supabase import create_client, Client
import os


class RuleType(Enum):
    """Types of data quality rules."""
    NULLABILITY = "nullability"  # Column must/must not be null
    RANGE = "range"  # Numeric values within range
    FORMAT = "format"  # String matches regex pattern
    LENGTH = "length"  # String length constraints
    UNIQUENESS = "uniqueness"  # Values must be unique
    REFERENCE = "reference"  # Foreign key validity
    ENUM = "enum"  # Value must be in allowed list
    CUSTOM = "custom"  # Custom SQL expression


class Severity(Enum):
    """Severity levels for rule violations."""
    CRITICAL = "critical"  # Data corruption, must fix immediately
    HIGH = "high"  # Major data quality issue
    MEDIUM = "medium"  # Moderate issue, should fix soon
    LOW = "low"  # Minor issue, cosmetic
    INFO = "info"  # Informational only


@dataclass
class QualityRule:
    """Represents a single data quality rule."""
    rule_id: str
    rule_type: RuleType
    table_name: str
    column_name: Optional[str] = None
    condition: Dict[str, Any] = None
    severity: Severity = Severity.MEDIUM
    description: str = ""
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_type": self.rule_type.value,
            "table_name": self.table_name,
            "column_name": self.column_name,
            "condition": self.condition,
            "severity": self.severity.value,
            "description": self.description,
            "enabled": self.enabled
        }


@dataclass
class RuleViolation:
    """Represents a rule violation found during evaluation."""
    rule_id: str
    table_name: str
    column_name: Optional[str]
    violation_count: int
    sample_values: List[Any]
    severity: Severity
    message: str
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        def _serialize_val(v):
            if isinstance(v, datetime):
                return v.isoformat()
            if isinstance(v, list):
                return [_serialize_val(i) for i in v]
            if isinstance(v, dict):
                return {k: _serialize_val(val) for k, val in v.items()}
            return v
            
        return {
            "rule_id": self.rule_id,
            "table_name": self.table_name,
            "column_name": self.column_name,
            "violation_count": self.violation_count,
            "sample_values": _serialize_val(self.sample_values[:10]),  # Limit samples
            "severity": self.severity.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class QualityReport:
    """Complete quality evaluation report for a table."""
    table_name: str
    total_rows: int
    rules_evaluated: int
    rules_passed: int
    rules_failed: int
    quality_score: float  # 0-100
    violations: List[RuleViolation]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "table_name": self.table_name,
            "total_rows": self.total_rows,
            "rules_evaluated": self.rules_evaluated,
            "rules_passed": self.rules_passed,
            "rules_failed": self.rules_failed,
            "quality_score": self.quality_score,
            "violations": [v.to_dict() for v in self.violations],
            "timestamp": self.timestamp.isoformat()
        }


class QualityRuleEngine:
    """
    Service for defining and evaluating data quality rules.
    
    This service provides comprehensive data quality validation:
    - Define rules per table/column
    - Evaluate rules against actual data
    - Track violations and quality scores
    - Historical quality tracking
    - Flexible rule configuration
    
    Rule Types:
    - NULLABILITY: Ensure column is/isn't null
    - RANGE: Numeric values within min/max
    - FORMAT: String matches regex pattern
    - LENGTH: String length constraints
    - UNIQUENESS: No duplicate values
    - REFERENCE: Foreign key validity
    - ENUM: Value in allowed list
    - CUSTOM: Custom SQL expression
    
    Usage:
        engine = QualityRuleEngine(tenant_id, project_id)
        
        # Define rule
        rule = QualityRule(
            rule_id="customers_email_not_null",
            rule_type=RuleType.NULLABILITY,
            table_name="customers",
            column_name="email",
            condition={"allow_null": False},
            severity=Severity.HIGH,
            description="Email must not be null"
        )
        
        await engine.add_rule(rule)
        
        # Evaluate rules
        report = await engine.evaluate_table("customers")
        
        print(f"Quality Score: {report.quality_score}%")
        print(f"Violations: {report.rules_failed}")
    """
    
    def __init__(self, tenant_id: str, project_id: str):
        """
        Initialize QualityRuleEngine.
        
        Args:
            tenant_id: UUID of the tenant
            project_id: UUID of the project
        """
        self.tenant_id = tenant_id
        self.project_id = project_id
        
        # Initialize Supabase client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
        # Rule evaluators registry
        self._evaluators: Dict[RuleType, Callable] = {
            RuleType.NULLABILITY: self._evaluate_nullability,
            RuleType.RANGE: self._evaluate_range,
            RuleType.FORMAT: self._evaluate_format,
            RuleType.LENGTH: self._evaluate_length,
            RuleType.UNIQUENESS: self._evaluate_uniqueness,
            RuleType.ENUM: self._evaluate_enum,
            RuleType.CUSTOM: self._evaluate_custom
        }
    
    async def add_rule(self, rule: QualityRule) -> str:
        """
        Add a new quality rule.
        
        Args:
            rule: QualityRule object to add
            
        Returns:
            Rule ID
        """
        insert_data = {
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "rule_id": rule.rule_id,
            "rule_type": rule.rule_type.value,
            "table_name": rule.table_name,
            "column_name": rule.column_name,
            "condition": rule.condition,
            "severity": rule.severity.value,
            "description": rule.description,
            "enabled": rule.enabled
        }
        
        response = self.supabase.table("utm_quality_rules").insert(insert_data).execute()
        
        return rule.rule_id
    
    async def get_rules(
        self,
        table_name: Optional[str] = None,
        enabled_only: bool = True
    ) -> List[QualityRule]:
        """
        Get quality rules, optionally filtered by table.
        
        Args:
            table_name: Optional table name to filter by
            enabled_only: If True, return only enabled rules
            
        Returns:
            List of QualityRule objects
        """
        query = self.supabase.table("utm_quality_rules").select("*").eq(
            "tenant_id", self.tenant_id
        ).eq(
            "project_id", self.project_id
        )
        
        if table_name:
            query = query.eq("table_name", table_name)
        
        if enabled_only:
            query = query.eq("enabled", True)
        
        response = query.execute()
        
        rules = []
        for row in response.data or []:
            rule = QualityRule(
                rule_id=row["rule_id"],
                rule_type=RuleType(row["rule_type"]),
                table_name=row["table_name"],
                column_name=row.get("column_name"),
                condition=row.get("condition", {}),
                severity=Severity(row["severity"]),
                description=row.get("description", ""),
                enabled=row.get("enabled", True)
            )
            rules.append(rule)
        
        return rules
    
    async def evaluate_table(
        self,
        table_name: str,
        catalog: str = "main",
        schema: str = "bronze"
    ) -> QualityReport:
        """
        Evaluate all rules for a table.
        
        Args:
            table_name: Table to evaluate
            catalog: Catalog name (default 'main')
            schema: Schema name (default 'bronze')
            
        Returns:
            QualityReport with results
        """
        # Get rules for this table
        rules = await self.get_rules(table_name=table_name, enabled_only=True)
        
        if not rules:
            # No rules defined, perfect score
            return QualityReport(
                table_name=table_name,
                total_rows=0,
                rules_evaluated=0,
                rules_passed=0,
                rules_failed=0,
                quality_score=100.0,
                violations=[],
                timestamp=datetime.now()
            )
        
        # Get total row count
        full_table_name = f"{catalog}.{schema}.{table_name}"
        total_rows = await self._get_row_count(full_table_name)
        
        # Evaluate each rule
        violations = []
        rules_passed = 0
        rules_failed = 0
        
        for rule in rules:
            try:
                violation = await self._evaluate_rule(rule, full_table_name, total_rows)
                
                if violation:
                    violations.append(violation)
                    rules_failed += 1
                else:
                    rules_passed += 1
            
            except Exception as e:
                # Log error but continue with other rules
                print(f"Error evaluating rule {rule.rule_id}: {e}")
                violations.append(RuleViolation(
                    rule_id=rule.rule_id,
                    table_name=table_name,
                    column_name=rule.column_name,
                    violation_count=0,
                    sample_values=[],
                    severity=Severity.INFO,
                    message=f"Rule evaluation failed: {str(e)}",
                    timestamp=datetime.now()
                ))
                rules_failed += 1
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(rules_passed, rules_failed, violations)
        
        # Create report
        report = QualityReport(
            table_name=table_name,
            total_rows=total_rows,
            rules_evaluated=len(rules),
            rules_passed=rules_passed,
            rules_failed=rules_failed,
            quality_score=quality_score,
            violations=violations,
            timestamp=datetime.now()
        )
        
        # Save report to database
        await self._save_report(report)
        
        return report
    
    async def _evaluate_rule(
        self,
        rule: QualityRule,
        full_table_name: str,
        total_rows: int
    ) -> Optional[RuleViolation]:
        """
        Evaluate a single rule.
        
        Args:
            rule: Rule to evaluate
            full_table_name: Fully qualified table name
            total_rows: Total rows in table
            
        Returns:
            RuleViolation if rule failed, None if passed
        """
        evaluator = self._evaluators.get(rule.rule_type)
        
        if not evaluator:
            raise ValueError(f"No evaluator for rule type {rule.rule_type}")
        
        return await evaluator(rule, full_table_name, total_rows)
    
    async def _evaluate_nullability(
        self,
        rule: QualityRule,
        full_table_name: str,
        total_rows: int
    ) -> Optional[RuleViolation]:
        """Evaluate nullability rule."""
        allow_null = rule.condition.get("allow_null", True)
        column = rule.column_name
        
        if allow_null:
            # No violation - allowing nulls
            return None
        
        # Check for null values
        query = f"""
        SELECT COUNT(*) as null_count
        FROM {full_table_name}
        WHERE {column} IS NULL
        """
        
        result = await self._execute_query(query)
        null_count = result[0]["null_count"] if result else 0
        
        if null_count > 0:
            return RuleViolation(
                rule_id=rule.rule_id,
                table_name=rule.table_name,
                column_name=column,
                violation_count=null_count,
                sample_values=[None],
                severity=rule.severity,
                message=f"Column '{column}' has {null_count} null values (not allowed)",
                timestamp=datetime.now()
            )
        
        return None
    
    async def _evaluate_range(
        self,
        rule: QualityRule,
        full_table_name: str,
        total_rows: int
    ) -> Optional[RuleViolation]:
        """Evaluate range rule."""
        column = rule.column_name
        min_value = rule.condition.get("min")
        max_value = rule.condition.get("max")
        
        conditions = []
        if min_value is not None:
            conditions.append(f"{column} < {min_value}")
        if max_value is not None:
            conditions.append(f"{column} > {max_value}")
        
        if not conditions:
            return None
        
        where_clause = " OR ".join(conditions)
        
        query = f"""
        SELECT {column}, COUNT(*) as violation_count
        FROM {full_table_name}
        WHERE {where_clause}
        GROUP BY {column}
        LIMIT 10
        """
        
        result = await self._execute_query(query)
        
        if result:
            total_violations = sum(row["violation_count"] for row in result)
            sample_values = [row[column] for row in result]
            
            return RuleViolation(
                rule_id=rule.rule_id,
                table_name=rule.table_name,
                column_name=column,
                violation_count=total_violations,
                sample_values=sample_values,
                severity=rule.severity,
                message=f"Column '{column}' has {total_violations} values outside range [{min_value}, {max_value}]",
                timestamp=datetime.now()
            )
        
        return None
    
    async def _evaluate_format(
        self,
        rule: QualityRule,
        full_table_name: str,
        total_rows: int
    ) -> Optional[RuleViolation]:
        """Evaluate format rule (regex pattern)."""
        column = rule.column_name
        pattern = rule.condition.get("pattern")
        
        if not pattern:
            return None
        
        # Use SQL REGEXP for pattern matching (platform-specific)
        query = f"""
        SELECT {column}
        FROM {full_table_name}
        WHERE {column} IS NOT NULL
          AND {column} NOT REGEXP '{pattern}'
        LIMIT 10
        """
        
        result = await self._execute_query(query)
        
        if result:
            sample_values = [row[column] for row in result]
            
            # Get total count
            count_query = f"""
            SELECT COUNT(*) as violation_count
            FROM {full_table_name}
            WHERE {column} IS NOT NULL
              AND {column} NOT REGEXP '{pattern}'
            """
            
            count_result = await self._execute_query(count_query)
            violation_count = count_result[0]["violation_count"] if count_result else len(result)
            
            return RuleViolation(
                rule_id=rule.rule_id,
                table_name=rule.table_name,
                column_name=column,
                violation_count=violation_count,
                sample_values=sample_values,
                severity=rule.severity,
                message=f"Column '{column}' has {violation_count} values not matching pattern '{pattern}'",
                timestamp=datetime.now()
            )
        
        return None
    
    async def _evaluate_length(
        self,
        rule: QualityRule,
        full_table_name: str,
        total_rows: int
    ) -> Optional[RuleViolation]:
        """Evaluate length rule."""
        column = rule.column_name
        min_length = rule.condition.get("min_length")
        max_length = rule.condition.get("max_length")
        
        conditions = []
        if min_length is not None:
            conditions.append(f"LENGTH({column}) < {min_length}")
        if max_length is not None:
            conditions.append(f"LENGTH({column}) > {max_length}")
        
        if not conditions:
            return None
        
        where_clause = " OR ".join(conditions)
        
        query = f"""
        SELECT {column}, LENGTH({column}) as length
        FROM {full_table_name}
        WHERE {column} IS NOT NULL AND ({where_clause})
        LIMIT 10
        """
        
        result = await self._execute_query(query)
        
        if result:
            sample_values = [f"{row[column]} (len={row['length']})" for row in result]
            
            count_query = f"""
            SELECT COUNT(*) as violation_count
            FROM {full_table_name}
            WHERE {column} IS NOT NULL AND ({where_clause})
            """
            
            count_result = await self._execute_query(count_query)
            violation_count = count_result[0]["violation_count"] if count_result else len(result)
            
            return RuleViolation(
                rule_id=rule.rule_id,
                table_name=rule.table_name,
                column_name=column,
                violation_count=violation_count,
                sample_values=sample_values,
                severity=rule.severity,
                message=f"Column '{column}' has {violation_count} values with invalid length",
                timestamp=datetime.now()
            )
        
        return None
    
    async def _evaluate_uniqueness(
        self,
        rule: QualityRule,
        full_table_name: str,
        total_rows: int
    ) -> Optional[RuleViolation]:
        """Evaluate uniqueness rule."""
        column = rule.column_name
        
        query = f"""
        SELECT {column}, COUNT(*) as duplicate_count
        FROM {full_table_name}
        WHERE {column} IS NOT NULL
        GROUP BY {column}
        HAVING COUNT(*) > 1
        LIMIT 10
        """
        
        result = await self._execute_query(query)
        
        if result:
            total_duplicates = sum(row["duplicate_count"] - 1 for row in result)
            sample_values = [f"{row[column]} (appears {row['duplicate_count']} times)" for row in result]
            
            return RuleViolation(
                rule_id=rule.rule_id,
                table_name=rule.table_name,
                column_name=column,
                violation_count=total_duplicates,
                sample_values=sample_values,
                severity=rule.severity,
                message=f"Column '{column}' has {total_duplicates} duplicate values",
                timestamp=datetime.now()
            )
        
        return None
    
    async def _evaluate_enum(
        self,
        rule: QualityRule,
        full_table_name: str,
        total_rows: int
    ) -> Optional[RuleViolation]:
        """Evaluate enum rule (allowed values)."""
        column = rule.column_name
        allowed_values = rule.condition.get("allowed_values", [])
        
        if not allowed_values:
            return None
        
        # Create IN clause
        value_list = ", ".join([f"'{v}'" for v in allowed_values])
        
        query = f"""
        SELECT {column}
        FROM {full_table_name}
        WHERE {column} IS NOT NULL
          AND {column} NOT IN ({value_list})
        LIMIT 10
        """
        
        result = await self._execute_query(query)
        
        if result:
            sample_values = [row[column] for row in result]
            
            count_query = f"""
            SELECT COUNT(*) as violation_count
            FROM {full_table_name}
            WHERE {column} IS NOT NULL
              AND {column} NOT IN ({value_list})
            """
            
            count_result = await self._execute_query(count_query)
            violation_count = count_result[0]["violation_count"] if count_result else len(result)
            
            return RuleViolation(
                rule_id=rule.rule_id,
                table_name=rule.table_name,
                column_name=column,
                violation_count=violation_count,
                sample_values=sample_values,
                severity=rule.severity,
                message=f"Column '{column}' has {violation_count} values not in allowed list",
                timestamp=datetime.now()
            )
        
        return None
    
    async def _evaluate_custom(
        self,
        rule: QualityRule,
        full_table_name: str,
        total_rows: int
    ) -> Optional[RuleViolation]:
        """Evaluate custom SQL rule."""
        custom_sql = rule.condition.get("sql")
        
        if not custom_sql:
            return None
        
        # Execute custom SQL
        result = await self._execute_query(custom_sql)
        
        if result:
            # Assume custom SQL returns violation_count
            violation_count = result[0].get("violation_count", len(result))
            
            return RuleViolation(
                rule_id=rule.rule_id,
                table_name=rule.table_name,
                column_name=rule.column_name,
                violation_count=violation_count,
                sample_values=[],
                severity=rule.severity,
                message=f"Custom rule violation: {violation_count} issues found",
                timestamp=datetime.now()
            )
        
        return None
    
    def _calculate_quality_score(
        self,
        rules_passed: int,
        rules_failed: int,
        violations: List[RuleViolation]
    ) -> float:
        """
        Calculate overall quality score (0-100).
        
        Formula considers:
        - Percentage of rules passed
        - Severity of violations
        - Number of violations
        """
        total_rules = rules_passed + rules_failed
        
        if total_rules == 0:
            return 100.0
        
        # Base score from pass rate
        base_score = (rules_passed / total_rules) * 100
        
        # Penalty based on severity
        severity_penalty = 0
        for violation in violations:
            if violation.severity == Severity.CRITICAL:
                severity_penalty += 20
            elif violation.severity == Severity.HIGH:
                severity_penalty += 10
            elif violation.severity == Severity.MEDIUM:
                severity_penalty += 5
            elif violation.severity == Severity.LOW:
                severity_penalty += 2
        
        # Apply penalty (capped at base score)
        final_score = max(0, base_score - severity_penalty)
        
        return round(final_score, 2)
    
    async def _get_row_count(self, full_table_name: str) -> int:
        """Get total row count for a table."""
        query = f"SELECT COUNT(*) as total_count FROM {full_table_name}"
        
        try:
            result = await self._execute_query(query)
            return result[0]["total_count"] if result else 0
        except Exception:
            return 0
    
    async def _execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a SQL query (placeholder - needs actual execution)."""
        # NOTE: In production, this would execute against actual data warehouse
        # For now, return empty result
        # TODO: Integrate with actual query execution service
        return []
    
    async def _save_report(self, report: QualityReport):
        """Save quality report to database."""
        insert_data = {
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "table_name": report.table_name,
            "total_rows": report.total_rows,
            "rules_evaluated": report.rules_evaluated,
            "rules_passed": report.rules_passed,
            "rules_failed": report.rules_failed,
            "quality_score": report.quality_score,
            "violations": [v.to_dict() for v in report.violations],
            "timestamp": report.timestamp.isoformat() if isinstance(report.timestamp, datetime) else report.timestamp
        }
        
        self.supabase.table("utm_quality_reports").insert(insert_data).execute()

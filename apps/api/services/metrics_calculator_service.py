"""
MetricsCalculator - Sprint 11: Data Quality Framework

Purpose: Calculate data quality metrics for tables and columns.
Supports multiple metric dimensions: completeness, accuracy, consistency, timeliness.

This service enables:
- Automated quality metric calculation
- Multi-dimensional quality assessment
- Historical metric tracking
- Aggregated quality scoring
- Trend analysis

Author: UTM Platform Team
Created: February 11, 2026
Sprint: 11 (Data Quality Framework)
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from supabase import create_client, Client
import os


class MetricType(Enum):
    """Types of data quality metrics."""
    COMPLETENESS = "completeness"  # % of non-null values
    ACCURACY = "accuracy"  # % of values meeting quality rules
    CONSISTENCY = "consistency"  # % of values consistent across tables
    TIMELINESS = "timeliness"  # Data freshness
    VALIDITY = "validity"  # % of values in valid format
    UNIQUENESS = "uniqueness"  # % of unique values (for key columns)


@dataclass
class QualityMetric:
    """Represents a single quality metric calculation."""
    metric_type: MetricType
    table_name: str
    column_name: Optional[str]
    value: float  # 0-100%
    measurement_count: int
    timestamp: datetime
    details: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_type": self.metric_type.value,
            "table_name": self.table_name,
            "column_name": self.column_name,
            "value": self.value,
            "measurement_count": self.measurement_count,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details or {}
        }


@dataclass
class MetricsReport:
    """Complete metrics report for a table."""
    table_name: str
    overall_score: float  # Weighted average of all metrics
    completeness_score: float
    accuracy_score: float
    consistency_score: float
    timeliness_score: float
    validity_score: float
    uniqueness_score: float
    metrics: List[QualityMetric]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "table_name": self.table_name,
            "overall_score": self.overall_score,
            "completeness_score": self.completeness_score,
            "accuracy_score": self.accuracy_score,
            "consistency_score": self.consistency_score,
            "timeliness_score": self.timeliness_score,
            "validity_score": self.validity_score,
            "uniqueness_score": self.uniqueness_score,
            "metrics": [m.to_dict() for m in self.metrics],
            "timestamp": self.timestamp.isoformat()
        }


class MetricsCalculator:
    """
    Service for calculating data quality metrics.
    
    This service provides comprehensive quality metrics across multiple dimensions:
    - Completeness: % of populated values
    - Accuracy: % of values meeting quality rules
    - Consistency: Cross-table validation
    - Timeliness: Data freshness
    - Validity: Format/pattern conformance
    - Uniqueness: Duplicate detection
    
    Metrics are calculated at table and column level, aggregated into overall scores.
    
    Usage:
        calculator = MetricsCalculator(tenant_id, project_id)
        
        # Calculate metrics for table
        report = await calculator.calculate_metrics("customers")
        
        print(f"Overall Score: {report.overall_score}%")
        print(f"Completeness: {report.completeness_score}%")
        print(f"Accuracy: {report.accuracy_score}%")
        
        # Get historical trends
        trends = await calculator.get_metric_trends(
            "customers", 
            metric_type=MetricType.COMPLETENESS,
            days=30
        )
    """
    
    def __init__(self, tenant_id: str, project_id: str):
        """
        Initialize MetricsCalculator.
        
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
        
        # Metric weights for overall score calculation
        self.metric_weights = {
            MetricType.COMPLETENESS: 0.25,
            MetricType.ACCURACY: 0.25,
            MetricType.CONSISTENCY: 0.15,
            MetricType.TIMELINESS: 0.15,
            MetricType.VALIDITY: 0.10,
            MetricType.UNIQUENESS: 0.10
        }
    
    async def calculate_metrics(
        self,
        table_name: str,
        catalog: str = "main",
        schema: str = "bronze"
    ) -> MetricsReport:
        """
        Calculate all quality metrics for a table.
        
        Args:
            table_name: Table to calculate metrics for
            catalog: Catalog name (default 'main')
            schema: Schema name (default 'bronze')
            
        Returns:
            MetricsReport with all calculated metrics
        """
        full_table_name = f"{catalog}.{schema}.{table_name}"
        
        # Get table metadata
        columns = await self._get_table_columns(full_table_name)
        total_rows = await self._get_row_count(full_table_name)
        
        metrics = []
        
        # Calculate completeness for each column
        completeness_scores = []
        for column in columns:
            metric = await self._calculate_completeness(full_table_name, column, total_rows)
            metrics.append(metric)
            completeness_scores.append(metric.value)
        
        # Calculate accuracy (based on quality rules)
        accuracy_metric = await self._calculate_accuracy(table_name, full_table_name, total_rows)
        metrics.append(accuracy_metric)
        
        # Calculate consistency (cross-table validation)
        consistency_metric = await self._calculate_consistency(table_name, full_table_name)
        metrics.append(consistency_metric)
        
        # Calculate timeliness (data freshness)
        timeliness_metric = await self._calculate_timeliness(table_name, full_table_name)
        metrics.append(timeliness_metric)
        
        # Calculate validity for string columns
        validity_scores = []
        for column in columns:
            if await self._is_string_column(full_table_name, column):
                metric = await self._calculate_validity(full_table_name, column, total_rows)
                metrics.append(metric)
                validity_scores.append(metric.value)
        
        # Calculate uniqueness for key columns
        uniqueness_scores = []
        key_columns = await self._get_key_columns(full_table_name)
        for column in key_columns:
            metric = await self._calculate_uniqueness(full_table_name, column, total_rows)
            metrics.append(metric)
            uniqueness_scores.append(metric.value)
        
        # Calculate aggregate scores
        completeness_score = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 100.0
        accuracy_score = accuracy_metric.value
        consistency_score = consistency_metric.value
        timeliness_score = timeliness_metric.value
        validity_score = sum(validity_scores) / len(validity_scores) if validity_scores else 100.0
        uniqueness_score = sum(uniqueness_scores) / len(uniqueness_scores) if uniqueness_scores else 100.0
        
        # Calculate weighted overall score
        overall_score = (
            completeness_score * self.metric_weights[MetricType.COMPLETENESS] +
            accuracy_score * self.metric_weights[MetricType.ACCURACY] +
            consistency_score * self.metric_weights[MetricType.CONSISTENCY] +
            timeliness_score * self.metric_weights[MetricType.TIMELINESS] +
            validity_score * self.metric_weights[MetricType.VALIDITY] +
            uniqueness_score * self.metric_weights[MetricType.UNIQUENESS]
        )
        
        # Create report
        report = MetricsReport(
            table_name=table_name,
            overall_score=round(overall_score, 2),
            completeness_score=round(completeness_score, 2),
            accuracy_score=round(accuracy_score, 2),
            consistency_score=round(consistency_score, 2),
            timeliness_score=round(timeliness_score, 2),
            validity_score=round(validity_score, 2),
            uniqueness_score=round(uniqueness_score, 2),
            metrics=metrics,
            timestamp=datetime.now()
        )
        
        # Save report
        await self._save_metrics_report(report)
        
        return report
    
    async def _calculate_completeness(
        self,
        full_table_name: str,
        column: str,
        total_rows: int
    ) -> QualityMetric:
        """
        Calculate completeness metric (% of non-null values).
        
        Formula: (total_rows - null_count) / total_rows * 100
        """
        if total_rows == 0:
            return QualityMetric(
                metric_type=MetricType.COMPLETENESS,
                table_name=full_table_name.split('.')[-1],
                column_name=column,
                value=100.0,
                measurement_count=0,
                timestamp=datetime.now()
            )
        
        query = f"""
        SELECT COUNT(*) as null_count
        FROM {full_table_name}
        WHERE {column} IS NULL
        """
        
        result = await self._execute_query(query)
        null_count = result[0]["null_count"] if result else 0
        
        non_null_count = total_rows - null_count
        completeness = (non_null_count / total_rows) * 100
        
        return QualityMetric(
            metric_type=MetricType.COMPLETENESS,
            table_name=full_table_name.split('.')[-1],
            column_name=column,
            value=round(completeness, 2),
            measurement_count=total_rows,
            timestamp=datetime.now(),
            details={
                "null_count": null_count,
                "non_null_count": non_null_count,
                "total_rows": total_rows
            }
        )
    
    async def _calculate_accuracy(
        self,
        table_name: str,
        full_table_name: str,
        total_rows: int
    ) -> QualityMetric:
        """
        Calculate accuracy metric (% of values meeting quality rules).
        
        Formula: (total_rows - total_violations) / total_rows * 100
        """
        # Get quality report for this table
        from quality_rule_engine_service import QualityRuleEngine
        
        engine = QualityRuleEngine(self.tenant_id, self.project_id)
        quality_report = await engine.evaluate_table(table_name)
        
        # Accuracy is inverse of violations
        accuracy = quality_report.quality_score
        
        return QualityMetric(
            metric_type=MetricType.ACCURACY,
            table_name=table_name,
            column_name=None,
            value=round(accuracy, 2),
            measurement_count=total_rows,
            timestamp=datetime.now(),
            details={
                "rules_evaluated": quality_report.rules_evaluated,
                "rules_passed": quality_report.rules_passed,
                "rules_failed": quality_report.rules_failed,
                "violations": len(quality_report.violations)
            }
        )
    
    async def _calculate_consistency(
        self,
        table_name: str,
        full_table_name: str
    ) -> QualityMetric:
        """
        Calculate consistency metric (cross-table validation).
        
        Checks:
        - Foreign key integrity
        - Cross-table value consistency
        - Referential integrity
        """
        # Get foreign key relationships
        fk_relationships = await self._get_foreign_keys(full_table_name)
        
        if not fk_relationships:
            # No foreign keys, perfect consistency
            return QualityMetric(
                metric_type=MetricType.CONSISTENCY,
                table_name=table_name,
                column_name=None,
                value=100.0,
                measurement_count=0,
                timestamp=datetime.now(),
                details={"foreign_keys": 0}
            )
        
        total_checks = len(fk_relationships)
        passed_checks = 0
        
        for fk in fk_relationships:
            # Check foreign key integrity
            query = f"""
            SELECT COUNT(*) as orphan_count
            FROM {full_table_name} t
            LEFT JOIN {fk['referenced_table']} r ON t.{fk['column']} = r.{fk['referenced_column']}
            WHERE t.{fk['column']} IS NOT NULL AND r.{fk['referenced_column']} IS NULL
            """
            
            result = await self._execute_query(query)
            orphan_count = result[0]["orphan_count"] if result else 0
            
            if orphan_count == 0:
                passed_checks += 1
        
        consistency = (passed_checks / total_checks) * 100
        
        return QualityMetric(
            metric_type=MetricType.CONSISTENCY,
            table_name=table_name,
            column_name=None,
            value=round(consistency, 2),
            measurement_count=total_checks,
            timestamp=datetime.now(),
            details={
                "foreign_keys_checked": total_checks,
                "foreign_keys_valid": passed_checks
            }
        )
    
    async def _calculate_timeliness(
        self,
        table_name: str,
        full_table_name: str
    ) -> QualityMetric:
        """
        Calculate timeliness metric (data freshness).
        
        Formula: Based on how recent the data is (timestamp columns)
        - < 1 hour old: 100%
        - 1-24 hours old: 90%
        - 1-7 days old: 70%
        - 7-30 days old: 50%
        - > 30 days old: 30%
        """
        # Find timestamp columns
        timestamp_columns = await self._get_timestamp_columns(full_table_name)
        
        if not timestamp_columns:
            # No timestamp column, assume current
            return QualityMetric(
                metric_type=MetricType.TIMELINESS,
                table_name=table_name,
                column_name=None,
                value=100.0,
                measurement_count=0,
                timestamp=datetime.now(),
                details={"no_timestamp_column": True}
            )
        
        # Use first timestamp column (usually created_at or updated_at)
        ts_column = timestamp_columns[0]
        
        query = f"""
        SELECT MAX({ts_column}) as latest_timestamp
        FROM {full_table_name}
        """
        
        result = await self._execute_query(query)
        
        if not result or not result[0].get("latest_timestamp"):
            return QualityMetric(
                metric_type=MetricType.TIMELINESS,
                table_name=table_name,
                column_name=ts_column,
                value=100.0,
                measurement_count=0,
                timestamp=datetime.now()
            )
        
        latest_ts = result[0]["latest_timestamp"]
        age = datetime.now() - latest_ts
        
        # Calculate timeliness score
        if age < timedelta(hours=1):
            timeliness = 100.0
        elif age < timedelta(days=1):
            timeliness = 90.0
        elif age < timedelta(days=7):
            timeliness = 70.0
        elif age < timedelta(days=30):
            timeliness = 50.0
        else:
            timeliness = 30.0
        
        return QualityMetric(
            metric_type=MetricType.TIMELINESS,
            table_name=table_name,
            column_name=ts_column,
            value=timeliness,
            measurement_count=1,
            timestamp=datetime.now(),
            details={
                "latest_timestamp": latest_ts.isoformat(),
                "age_hours": age.total_seconds() / 3600
            }
        )
    
    async def _calculate_validity(
        self,
        full_table_name: str,
        column: str,
        total_rows: int
    ) -> QualityMetric:
        """
        Calculate validity metric (% of values in valid format).
        
        Checks for:
        - Printable characters
        - No control characters
        - Proper encoding
        """
        if total_rows == 0:
            return QualityMetric(
                metric_type=MetricType.VALIDITY,
                table_name=full_table_name.split('.')[-1],
                column_name=column,
                value=100.0,
                measurement_count=0,
                timestamp=datetime.now()
            )
        
        # Count invalid values (contains control characters)
        query = f"""
        SELECT COUNT(*) as invalid_count
        FROM {full_table_name}
        WHERE {column} IS NOT NULL
          AND ({column} REGEXP '[[:cntrl:]]' OR LENGTH({column}) = 0)
        """
        
        result = await self._execute_query(query)
        invalid_count = result[0]["invalid_count"] if result else 0
        
        valid_count = total_rows - invalid_count
        validity = (valid_count / total_rows) * 100
        
        return QualityMetric(
            metric_type=MetricType.VALIDITY,
            table_name=full_table_name.split('.')[-1],
            column_name=column,
            value=round(validity, 2),
            measurement_count=total_rows,
            timestamp=datetime.now(),
            details={
                "invalid_count": invalid_count,
                "valid_count": valid_count
            }
        )
    
    async def _calculate_uniqueness(
        self,
        full_table_name: str,
        column: str,
        total_rows: int
    ) -> QualityMetric:
        """
        Calculate uniqueness metric (% of unique values).
        
        Formula: distinct_count / total_rows * 100
        """
        if total_rows == 0:
            return QualityMetric(
                metric_type=MetricType.UNIQUENESS,
                table_name=full_table_name.split('.')[-1],
                column_name=column,
                value=100.0,
                measurement_count=0,
                timestamp=datetime.now()
            )
        
        query = f"""
        SELECT COUNT(DISTINCT {column}) as distinct_count
        FROM {full_table_name}
        WHERE {column} IS NOT NULL
        """
        
        result = await self._execute_query(query)
        distinct_count = result[0]["distinct_count"] if result else 0
        
        uniqueness = (distinct_count / total_rows) * 100
        
        return QualityMetric(
            metric_type=MetricType.UNIQUENESS,
            table_name=full_table_name.split('.')[-1],
            column_name=column,
            value=round(uniqueness, 2),
            measurement_count=total_rows,
            timestamp=datetime.now(),
            details={
                "distinct_count": distinct_count,
                "total_count": total_rows,
                "duplicate_count": total_rows - distinct_count
            }
        )
    
    async def get_metric_trends(
        self,
        table_name: str,
        metric_type: MetricType,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get historical trend for a specific metric.
        
        Args:
            table_name: Table to get trends for
            metric_type: Type of metric
            days: Number of days of history
            
        Returns:
            List of metric values over time
        """
        since_date = datetime.now() - timedelta(days=days)
        
        query = self.supabase.table("utm_quality_metrics").select("*").eq(
            "tenant_id", self.tenant_id
        ).eq(
            "project_id", self.project_id
        ).eq(
            "table_name", table_name
        ).eq(
            "metric_type", metric_type.value
        ).gte(
            "timestamp", since_date.isoformat()
        ).order("timestamp", desc=False)
        
        response = query.execute()
        
        return response.data or []
    
    async def _get_table_columns(self, full_table_name: str) -> List[str]:
        """Get list of columns for a table."""
        # TODO: Implement actual column retrieval
        return []
    
    async def _get_row_count(self, full_table_name: str) -> int:
        """Get total row count for a table."""
        query = f"SELECT COUNT(*) as total_count FROM {full_table_name}"
        
        try:
            result = await self._execute_query(query)
            return result[0]["total_count"] if result else 0
        except Exception:
            return 0
    
    async def _is_string_column(self, full_table_name: str, column: str) -> bool:
        """Check if column is string type."""
        # TODO: Implement actual type checking
        return True
    
    async def _get_key_columns(self, full_table_name: str) -> List[str]:
        """Get primary/unique key columns."""
        # TODO: Implement actual key column detection
        return []
    
    async def _get_foreign_keys(self, full_table_name: str) -> List[Dict[str, str]]:
        """Get foreign key relationships."""
        # TODO: Implement actual FK detection
        return []
    
    async def _get_timestamp_columns(self, full_table_name: str) -> List[str]:
        """Get timestamp/date columns."""
        # TODO: Implement actual timestamp column detection
        return []
    
    async def _execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a SQL query (placeholder)."""
        # TODO: Integrate with actual query execution service
        return []
    
    async def _save_metrics_report(self, report: MetricsReport):
        """Save metrics report to database."""
        insert_data = {
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "table_name": report.table_name,
            "overall_score": report.overall_score,
            "completeness_score": report.completeness_score,
            "accuracy_score": report.accuracy_score,
            "consistency_score": report.consistency_score,
            "timeliness_score": report.timeliness_score,
            "validity_score": report.validity_score,
            "uniqueness_score": report.uniqueness_score,
            "metrics": [m.to_dict() for m in report.metrics],
            "timestamp": report.timestamp
        }
        
        self.supabase.table("utm_quality_metrics").insert(insert_data).execute()

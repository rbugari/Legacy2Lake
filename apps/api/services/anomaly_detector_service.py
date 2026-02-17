"""
AnomalyDetector - Sprint 11: Data Quality Framework

Purpose: Detect anomalies and outliers in data using statistical methods.
Supports multiple detection techniques: Z-score, IQR, moving average, pattern-based.

This service enables:
- Statistical outlier detection
- Pattern-based anomaly detection
- Threshold-based alerting
- Trend analysis
- Automated anomaly scoring

Author: UTM Platform Team
Created: February 11, 2026
Sprint: 11 (Data Quality Framework)
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from supabase import create_client, Client
import os
import statistics


class AnomalyType(Enum):
    """Types of anomalies that can be detected."""
    STATISTICAL_OUTLIER = "statistical_outlier"  # Z-score or IQR based
    VOLUME_SPIKE = "volume_spike"  # Sudden increase in row count
    VOLUME_DROP = "volume_drop"  # Sudden decrease in row count
    NULL_SPIKE = "null_spike"  # Sudden increase in null values
    DUPLICATE_SPIKE = "duplicate_spike"  # Sudden increase in duplicates
    PATTERN_BREAK = "pattern_break"  # Break in expected pattern
    THRESHOLD_VIOLATION = "threshold_violation"  # Value exceeds threshold
    DATA_DRIFT = "data_drift"  # Distribution change over time


class Severity(Enum):
    """Severity levels for anomalies."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class Anomaly:
    """Represents a detected anomaly."""
    anomaly_type: AnomalyType
    table_name: str
    column_name: Optional[str]
    detected_value: Any
    expected_range: Tuple[float, float]
    deviation_score: float  # How far from normal (0-100)
    severity: Severity
    description: str
    timestamp: datetime
    details: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "anomaly_type": self.anomaly_type.value,
            "table_name": self.table_name,
            "column_name": self.column_name,
            "detected_value": self.detected_value,
            "expected_range": list(self.expected_range),
            "deviation_score": self.deviation_score,
            "severity": self.severity.value,
            "description": self.description,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details or {}
        }


@dataclass
class AnomalyReport:
    """Complete anomaly detection report."""
    table_name: str
    anomalies_detected: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    anomalies: List[Anomaly]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "table_name": self.table_name,
            "anomalies_detected": self.anomalies_detected,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "anomalies": [a.to_dict() for a in self.anomalies],
            "timestamp": self.timestamp.isoformat()
        }


class AnomalyDetector:
    """
    Service for detecting anomalies and outliers in data.
    
    This service provides comprehensive anomaly detection:
    - Statistical Outliers: Z-score and IQR methods
    - Volume Anomalies: Sudden changes in row counts
    - Quality Anomalies: Spikes in nulls or duplicates
    - Pattern Anomalies: Breaks in expected patterns
    - Threshold Violations: Values exceeding limits
    - Data Drift: Distribution changes over time
    
    Detection Methods:
    - Z-Score: Values > 3 standard deviations from mean
    - IQR: Values outside [Q1 - 1.5*IQR, Q3 + 1.5*IQR]
    - Moving Average: Values deviating from MA by threshold
    - Pattern Matching: Expected vs actual patterns
    
    Usage:
        detector = AnomalyDetector(tenant_id, project_id)
        
        # Detect anomalies in table
        report = await detector.detect_anomalies("orders")
        
        print(f"Anomalies Detected: {report.anomalies_detected}")
        print(f"Critical: {report.critical_count}")
        
        # Detect outliers in specific column
        outliers = await detector.detect_statistical_outliers(
            "orders",
            "total_amount",
            method="z_score"
        )
    """
    
    def __init__(self, tenant_id: str, project_id: str):
        """
        Initialize AnomalyDetector.
        
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
        
        # Detection thresholds
        self.z_score_threshold = 3.0  # Standard deviations
        self.iqr_multiplier = 1.5
        self.volume_change_threshold = 0.3  # 30% change
        self.null_spike_threshold = 0.2  # 20% increase in nulls
    
    async def detect_anomalies(
        self,
        table_name: str,
        catalog: str = "main",
        schema: str = "bronze"
    ) -> AnomalyReport:
        """
        Detect all types of anomalies for a table.
        
        Args:
            table_name: Table to detect anomalies in
            catalog: Catalog name (default 'main')
            schema: Schema name (default 'bronze')
            
        Returns:
            AnomalyReport with all detected anomalies
        """
        full_table_name = f"{catalog}.{schema}.{table_name}"
        anomalies = []
        
        # Detect volume anomalies
        volume_anomalies = await self._detect_volume_anomalies(table_name, full_table_name)
        anomalies.extend(volume_anomalies)
        
        # Detect null spikes
        null_anomalies = await self._detect_null_spikes(table_name, full_table_name)
        anomalies.extend(null_anomalies)
        
        # Detect duplicate spikes
        duplicate_anomalies = await self._detect_duplicate_spikes(table_name, full_table_name)
        anomalies.extend(duplicate_anomalies)
        
        # Detect statistical outliers in numeric columns
        numeric_columns = await self._get_numeric_columns(full_table_name)
        for column in numeric_columns:
            outliers = await self.detect_statistical_outliers(
                table_name,
                column,
                catalog=catalog,
                schema=schema,
                method="z_score"
            )
            anomalies.extend(outliers)
        
        # Count by severity
        critical_count = sum(1 for a in anomalies if a.severity == Severity.CRITICAL)
        high_count = sum(1 for a in anomalies if a.severity == Severity.HIGH)
        medium_count = sum(1 for a in anomalies if a.severity == Severity.MEDIUM)
        low_count = sum(1 for a in anomalies if a.severity == Severity.LOW)
        
        report = AnomalyReport(
            table_name=table_name,
            anomalies_detected=len(anomalies),
            critical_count=critical_count,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count,
            anomalies=anomalies,
            timestamp=datetime.now()
        )
        
        # Save report
        await self._save_anomaly_report(report)
        
        return report
    
    async def detect_statistical_outliers(
        self,
        table_name: str,
        column_name: str,
        catalog: str = "main",
        schema: str = "bronze",
        method: str = "z_score"
    ) -> List[Anomaly]:
        """
        Detect statistical outliers in a numeric column.
        
        Args:
            table_name: Table name
            column_name: Column to check for outliers
            catalog: Catalog name
            schema: Schema name
            method: Detection method ('z_score' or 'iqr')
            
        Returns:
            List of Anomaly objects for detected outliers
        """
        full_table_name = f"{catalog}.{schema}.{table_name}"
        
        # Get column statistics
        stats = await self._get_column_statistics(full_table_name, column_name)
        
        if not stats:
            return []
        
        anomalies = []
        
        if method == "z_score":
            anomalies = await self._detect_z_score_outliers(
                table_name,
                full_table_name,
                column_name,
                stats
            )
        elif method == "iqr":
            anomalies = await self._detect_iqr_outliers(
                table_name,
                full_table_name,
                column_name,
                stats
            )
        
        return anomalies
    
    async def _detect_z_score_outliers(
        self,
        table_name: str,
        full_table_name: str,
        column_name: str,
        stats: Dict[str, float]
    ) -> List[Anomaly]:
        """Detect outliers using Z-score method."""
        mean = stats["mean"]
        stddev = stats["stddev"]
        
        if stddev == 0:
            return []
        
        # Find values with |z-score| > threshold
        lower_bound = mean - (self.z_score_threshold * stddev)
        upper_bound = mean + (self.z_score_threshold * stddev)
        
        query = f"""
        SELECT {column_name}, 
               ABS(({column_name} - {mean}) / {stddev}) as z_score
        FROM {full_table_name}
        WHERE {column_name} IS NOT NULL
          AND ({column_name} < {lower_bound} OR {column_name} > {upper_bound})
        LIMIT 100
        """
        
        result = await self._execute_query(query)
        
        anomalies = []
        for row in result or []:
            z_score = row["z_score"]
            value = row[column_name]
            
            # Calculate deviation score (0-100)
            deviation_score = min(100, (z_score / self.z_score_threshold) * 100)
            
            # Determine severity based on z-score
            if z_score > 5:
                severity = Severity.CRITICAL
            elif z_score > 4:
                severity = Severity.HIGH
            elif z_score > 3:
                severity = Severity.MEDIUM
            else:
                severity = Severity.LOW
            
            anomaly = Anomaly(
                anomaly_type=AnomalyType.STATISTICAL_OUTLIER,
                table_name=table_name,
                column_name=column_name,
                detected_value=value,
                expected_range=(lower_bound, upper_bound),
                deviation_score=round(deviation_score, 2),
                severity=severity,
                description=f"Value {value} is {z_score:.2f} standard deviations from mean",
                timestamp=datetime.now(),
                details={
                    "method": "z_score",
                    "z_score": z_score,
                    "mean": mean,
                    "stddev": stddev
                }
            )
            
            anomalies.append(anomaly)
        
        return anomalies
    
    async def _detect_iqr_outliers(
        self,
        table_name: str,
        full_table_name: str,
        column_name: str,
        stats: Dict[str, float]
    ) -> List[Anomaly]:
        """Detect outliers using IQR method."""
        q1 = stats["q1"]
        q3 = stats["q3"]
        iqr = q3 - q1
        
        if iqr == 0:
            return []
        
        # Calculate bounds
        lower_bound = q1 - (self.iqr_multiplier * iqr)
        upper_bound = q3 + (self.iqr_multiplier * iqr)
        
        query = f"""
        SELECT {column_name}
        FROM {full_table_name}
        WHERE {column_name} IS NOT NULL
          AND ({column_name} < {lower_bound} OR {column_name} > {upper_bound})
        LIMIT 100
        """
        
        result = await self._execute_query(query)
        
        anomalies = []
        for row in result or []:
            value = row[column_name]
            
            # Calculate deviation from bounds
            if value < lower_bound:
                deviation = (lower_bound - value) / iqr
            else:
                deviation = (value - upper_bound) / iqr
            
            deviation_score = min(100, deviation * 50)
            
            # Determine severity
            if deviation > 5:
                severity = Severity.CRITICAL
            elif deviation > 3:
                severity = Severity.HIGH
            elif deviation > 2:
                severity = Severity.MEDIUM
            else:
                severity = Severity.LOW
            
            anomaly = Anomaly(
                anomaly_type=AnomalyType.STATISTICAL_OUTLIER,
                table_name=table_name,
                column_name=column_name,
                detected_value=value,
                expected_range=(lower_bound, upper_bound),
                deviation_score=round(deviation_score, 2),
                severity=severity,
                description=f"Value {value} is outside IQR bounds [{lower_bound:.2f}, {upper_bound:.2f}]",
                timestamp=datetime.now(),
                details={
                    "method": "iqr",
                    "q1": q1,
                    "q3": q3,
                    "iqr": iqr,
                    "deviation_iqr": deviation
                }
            )
            
            anomalies.append(anomaly)
        
        return anomalies
    
    async def _detect_volume_anomalies(
        self,
        table_name: str,
        full_table_name: str
    ) -> List[Anomaly]:
        """Detect sudden changes in row count."""
        # Get current row count
        current_count = await self._get_row_count(full_table_name)
        
        # Get historical row counts
        historical_counts = await self._get_historical_row_counts(table_name, days=7)
        
        if len(historical_counts) < 2:
            return []
        
        # Calculate expected range (mean ± threshold)
        mean_count = statistics.mean(historical_counts)
        expected_min = mean_count * (1 - self.volume_change_threshold)
        expected_max = mean_count * (1 + self.volume_change_threshold)
        
        anomalies = []
        
        if current_count < expected_min:
            # Volume drop
            deviation = ((mean_count - current_count) / mean_count) * 100
            
            anomaly = Anomaly(
                anomaly_type=AnomalyType.VOLUME_DROP,
                table_name=table_name,
                column_name=None,
                detected_value=current_count,
                expected_range=(expected_min, expected_max),
                deviation_score=round(deviation, 2),
                severity=Severity.HIGH if deviation > 50 else Severity.MEDIUM,
                description=f"Row count dropped by {deviation:.1f}% (expected ~{mean_count:.0f}, got {current_count})",
                timestamp=datetime.now(),
                details={
                    "current_count": current_count,
                    "mean_count": mean_count,
                    "historical_counts": historical_counts
                }
            )
            
            anomalies.append(anomaly)
        
        elif current_count > expected_max:
            # Volume spike
            deviation = ((current_count - mean_count) / mean_count) * 100
            
            anomaly = Anomaly(
                anomaly_type=AnomalyType.VOLUME_SPIKE,
                table_name=table_name,
                column_name=None,
                detected_value=current_count,
                expected_range=(expected_min, expected_max),
                deviation_score=round(deviation, 2),
                severity=Severity.MEDIUM if deviation > 50 else Severity.LOW,
                description=f"Row count spiked by {deviation:.1f}% (expected ~{mean_count:.0f}, got {current_count})",
                timestamp=datetime.now(),
                details={
                    "current_count": current_count,
                    "mean_count": mean_count,
                    "historical_counts": historical_counts
                }
            )
            
            anomalies.append(anomaly)
        
        return anomalies
    
    async def _detect_null_spikes(
        self,
        table_name: str,
        full_table_name: str
    ) -> List[Anomaly]:
        """Detect sudden increases in null values."""
        columns = await self._get_table_columns(full_table_name)
        anomalies = []
        
        for column in columns:
            # Get current null percentage
            current_null_pct = await self._get_null_percentage(full_table_name, column)
            
            # Get historical null percentages
            historical_nulls = await self._get_historical_null_percentages(table_name, column, days=7)
            
            if not historical_nulls:
                continue
            
            mean_null_pct = statistics.mean(historical_nulls)
            
            # Check for spike
            if current_null_pct > mean_null_pct + self.null_spike_threshold:
                deviation = ((current_null_pct - mean_null_pct) / (mean_null_pct + 0.01)) * 100
                
                anomaly = Anomaly(
                    anomaly_type=AnomalyType.NULL_SPIKE,
                    table_name=table_name,
                    column_name=column,
                    detected_value=current_null_pct,
                    expected_range=(0, mean_null_pct + self.null_spike_threshold),
                    deviation_score=round(min(100, deviation), 2),
                    severity=Severity.HIGH if current_null_pct > 0.5 else Severity.MEDIUM,
                    description=f"Null percentage in '{column}' increased to {current_null_pct*100:.1f}% (expected ~{mean_null_pct*100:.1f}%)",
                    timestamp=datetime.now(),
                    details={
                        "current_null_pct": current_null_pct,
                        "mean_null_pct": mean_null_pct,
                        "historical_nulls": historical_nulls
                    }
                )
                
                anomalies.append(anomaly)
        
        return anomalies
    
    async def _detect_duplicate_spikes(
        self,
        table_name: str,
        full_table_name: str
    ) -> List[Anomaly]:
        """Detect sudden increases in duplicate values."""
        # Get key columns
        key_columns = await self._get_key_columns(full_table_name)
        
        if not key_columns:
            return []
        
        anomalies = []
        
        for column in key_columns:
            # Get current duplicate percentage
            current_dup_pct = await self._get_duplicate_percentage(full_table_name, column)
            
            # Get historical duplicate percentages
            historical_dups = await self._get_historical_duplicate_percentages(table_name, column, days=7)
            
            if not historical_dups:
                continue
            
            mean_dup_pct = statistics.mean(historical_dups)
            
            # Check for spike (key columns should have low duplicates)
            if current_dup_pct > mean_dup_pct + 0.1:  # 10% increase
                deviation = ((current_dup_pct - mean_dup_pct) / (mean_dup_pct + 0.01)) * 100
                
                anomaly = Anomaly(
                    anomaly_type=AnomalyType.DUPLICATE_SPIKE,
                    table_name=table_name,
                    column_name=column,
                    detected_value=current_dup_pct,
                    expected_range=(0, mean_dup_pct + 0.1),
                    deviation_score=round(min(100, deviation), 2),
                    severity=Severity.HIGH,
                    description=f"Duplicate percentage in key column '{column}' increased to {current_dup_pct*100:.1f}%",
                    timestamp=datetime.now(),
                    details={
                        "current_dup_pct": current_dup_pct,
                        "mean_dup_pct": mean_dup_pct,
                        "historical_dups": historical_dups
                    }
                )
                
                anomalies.append(anomaly)
        
        return anomalies
    
    async def _get_column_statistics(
        self,
        full_table_name: str,
        column_name: str
    ) -> Optional[Dict[str, float]]:
        """Get statistical summary for a numeric column."""
        query = f"""
        SELECT 
            AVG({column_name}) as mean,
            STDDEV({column_name}) as stddev,
            MIN({column_name}) as min,
            MAX({column_name}) as max,
            PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY {column_name}) as q1,
            PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY {column_name}) as median,
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY {column_name}) as q3
        FROM {full_table_name}
        WHERE {column_name} IS NOT NULL
        """
        
        result = await self._execute_query(query)
        
        if result:
            return result[0]
        
        return None
    
    async def _get_row_count(self, full_table_name: str) -> int:
        """Get current row count."""
        query = f"SELECT COUNT(*) as count FROM {full_table_name}"
        result = await self._execute_query(query)
        return result[0]["count"] if result else 0
    
    async def _get_null_percentage(self, full_table_name: str, column: str) -> float:
        """Get percentage of null values in column."""
        query = f"""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN {column} IS NULL THEN 1 ELSE 0 END) as null_count
        FROM {full_table_name}
        """
        
        result = await self._execute_query(query)
        
        if result and result[0]["total"] > 0:
            return result[0]["null_count"] / result[0]["total"]
        
        return 0.0
    
    async def _get_duplicate_percentage(self, full_table_name: str, column: str) -> float:
        """Get percentage of duplicate values in column."""
        query = f"""
        SELECT 
            COUNT(*) as total,
            COUNT(DISTINCT {column}) as distinct_count
        FROM {full_table_name}
        WHERE {column} IS NOT NULL
        """
        
        result = await self._execute_query(query)
        
        if result and result[0]["total"] > 0:
            duplicates = result[0]["total"] - result[0]["distinct_count"]
            return duplicates / result[0]["total"]
        
        return 0.0
    
    async def _get_historical_row_counts(self, table_name: str, days: int) -> List[int]:
        """Get historical row counts from metrics."""
        # TODO: Query utm_quality_metrics for historical data
        return []
    
    async def _get_historical_null_percentages(self, table_name: str, column: str, days: int) -> List[float]:
        """Get historical null percentages."""
        # TODO: Query utm_quality_metrics
        return []
    
    async def _get_historical_duplicate_percentages(self, table_name: str, column: str, days: int) -> List[float]:
        """Get historical duplicate percentages."""
        # TODO: Query utm_quality_metrics
        return []
    
    async def _get_table_columns(self, full_table_name: str) -> List[str]:
        """Get list of columns."""
        # TODO: Implement
        return []
    
    async def _get_numeric_columns(self, full_table_name: str) -> List[str]:
        """Get numeric columns."""
        # TODO: Implement
        return []
    
    async def _get_key_columns(self, full_table_name: str) -> List[str]:
        """Get key columns."""
        # TODO: Implement
        return []
    
    async def _execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute SQL query (placeholder)."""
        # TODO: Integrate with actual query execution
        return []
    
    async def _save_anomaly_report(self, report: AnomalyReport):
        """Save anomaly report to database."""
        insert_data = {
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "table_name": report.table_name,
            "anomalies_detected": report.anomalies_detected,
            "critical_count": report.critical_count,
            "high_count": report.high_count,
            "medium_count": report.medium_count,
            "low_count": report.low_count,
            "anomalies": [a.to_dict() for a in report.anomalies],
            "timestamp": report.timestamp
        }
        
        self.supabase.table("utm_anomaly_reports").insert(insert_data).execute()

"""
Forensic Analyzer Service - v4.0 Deep Forensic Triage

Performs field-level (column) analysis for data profiling.
Detects PII, calculates quality scores, infers types, and provides recommendations.

Features:
- Statistical profiling (min/max/mean/percentiles)
- PII detection (email, phone, SSN, credit card, etc.)
- Data quality scoring (0-100)
- Type inference with confidence
- Pattern detection
- Recommendations for constraints and transformations

Author: Legacy2Lake Engineering
Date: February 14, 2026
Version: v4.0.0
"""

try:
    from apps.api.utils.logger import logger
    from apps.api.services.persistence_service import SupabasePersistence
except ImportError:
    try:
        from utils.logger import logger
        from services.persistence_service import SupabasePersistence
    except ImportError:
        from ..utils.logger import logger
        from .persistence_service import SupabasePersistence

from typing import Dict, Any, Optional, List
import re
from datetime import datetime
import statistics


class ColumnProfile:
    """Represents a complete column profile"""
    
    def __init__(self):
        self.profile_id: Optional[str] = None
        self.project_id: str = ""
        self.tenant_id: str = ""
        self.object_id: Optional[str] = None
        self.object_name: str = ""
        self.column_name: str = ""
        self.column_index: int = 0
        
        # Type information
        self.inferred_type: str = "STRING"
        self.declared_type: Optional[str] = None
        self.type_confidence: float = 0.0
        
        # Nullability and cardinality
        self.nullability_score: float = 0.0
        self.total_rows: int = 0
        self.null_count: int = 0
        self.distinct_count: int = 0
        self.cardinality: int = 0
        self.distinct_ratio: float = 0.0
        
        # Semantic tags
        self.semantic_tags: List[str] = []
        self.pii_detected: bool = False
        self.pii_confidence: float = 0.0
        
        # Quality
        self.quality_score: int = 0
        self.quality_issues: List[str] = []
        
        # Statistical profile
        self.statistical_profile: Dict[str, Any] = {}
        
        # Detected patterns
        self.detected_patterns: List[str] = []
        self.pattern_coverage: float = 0.0
        
        # Sample values
        self.sample_values: Dict[str, Any] = {}
        
        # Recommendations
        self.recommendations: Dict[str, Any] = {}
        
        # Metadata
        self.analyzed_at: str = datetime.now().isoformat()
        self.analysis_duration_ms: int = 0
        self.analyzer_version: str = "4.0.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database insertion"""
        return {
            "profile_id": self.profile_id,
            "project_id": self.project_id,
            "tenant_id": self.tenant_id,
            "object_id": self.object_id,
            "object_name": self.object_name,
            "column_name": self.column_name,
            "column_index": self.column_index,
            "inferred_type": self.inferred_type,
            "declared_type": self.declared_type,
            "type_confidence": self.type_confidence,
            "nullability_score": self.nullability_score,
            "total_rows": self.total_rows,
            "null_count": self.null_count,
            "distinct_count": self.distinct_count,
            "cardinality": self.cardinality,
            "distinct_ratio": self.distinct_ratio,
            "semantic_tags": self.semantic_tags,
            "pii_detected": self.pii_detected,
            "pii_confidence": self.pii_confidence,
            "quality_score": self.quality_score,
            "quality_issues": self.quality_issues,
            "statistical_profile": self.statistical_profile,
            "detected_patterns": self.detected_patterns,
            "pattern_coverage": self.pattern_coverage,
            "sample_values": self.sample_values,
            "recommendations": self.recommendations,
            "analyzed_at": self.analyzed_at,
            "analysis_duration_ms": self.analysis_duration_ms,
            "analyzer_version": self.analyzer_version
        }


class ForensicAnalyzer:
    """
    Performs deep field-level forensic analysis on data columns.
    
    v4.0 Feature: Deep Forensic Triage
    """
    
    # PII detection patterns
    PATTERNS = {
        "EMAIL": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "PHONE_US": r'\b(\+1[-.\s]?)?(\()?[0-9]{3}(\))?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
        "SSN": r'\b\d{3}-\d{2}-\d{4}\b',
        "CREDIT_CARD": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        "ZIP_CODE": r'\b\d{5}(-\d{4})?\b',
        "DATE_YYYYMMDD": r'\b\d{4}-\d{2}-\d{2}\b',
        "DATE_MMDDYYYY": r'\b\d{2}/\d{2}/\d{4}\b',
        "IP_ADDRESS": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
        "URL": r'https?://[^\s]+',
        "GUID": r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b'
    }
    
    # PII tags (for semantic tagging)
    PII_TAGS = ["EMAIL", "PHONE", "SSN", "CREDIT_CARD"]
    
    def __init__(self, tenant_id: Optional[str] = None, client_id: Optional[str] = None):
        """
        Initialize Forensic Analyzer
        
        Args:
            tenant_id: Tenant ID for multi-tenant isolation
            client_id: Client ID for additional isolation
        """
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.db = SupabasePersistence(tenant_id=tenant_id, client_id=client_id)
    
    async def analyze_column(
        self,
        project_id: str,
        object_name: str,
        column_name: str,
        values: List[Any],
        column_index: int = 0,
        declared_type: Optional[str] = None,
        object_id: Optional[str] = None
    ) -> ColumnProfile:
        """
        Analyze a single column and generate complete profile
        
        Args:
            project_id: Project ID
            object_name: Source object/table name
            column_name: Column name
            values: List of sample values from the column
            column_index: Position in table (0-based)
            declared_type: Data type from source schema (if available)
            object_id: Reference to utm_objects table
            
        Returns:
            ColumnProfile object with complete analysis
        """
        start_time = datetime.now()
        
        logger.info(
            f"[ForensicAnalyzer] Analyzing column: {object_name}.{column_name} ({len(values)} samples)",
            "ForensicAnalyzer"
        )
        
        profile = ColumnProfile()
        profile.project_id = project_id
        profile.tenant_id = self.tenant_id or ""
        profile.object_id = object_id
        profile.object_name = object_name
        profile.column_name = column_name
        profile.column_index = column_index
        profile.declared_type = declared_type
        
        # Filter out None values for analysis
        non_null_values = [v for v in values if v is not None]
        
        # Basic statistics
        profile.total_rows = len(values)
        profile.null_count = len(values) - len(non_null_values)
        profile.nullability_score = profile.null_count / profile.total_rows if profile.total_rows > 0 else 0.0
        
        # Cardinality
        unique_values = set(str(v) for v in non_null_values)
        profile.distinct_count = len(unique_values)
        profile.cardinality = profile.distinct_count
        profile.distinct_ratio = profile.distinct_count / profile.total_rows if profile.total_rows > 0 else 0.0
        
        # Type inference
        profile.inferred_type, profile.type_confidence = self._infer_type(non_null_values)
        
        # Pattern detection and PII detection
        profile.detected_patterns = self._detect_patterns(non_null_values)
        profile.semantic_tags = self._semantic_tagging(column_name, non_null_values, profile.detected_patterns)
        profile.pii_detected = any(tag in self.PII_TAGS for tag in profile.semantic_tags)
        profile.pii_confidence = self._calculate_pii_confidence(profile.semantic_tags, non_null_values)
        
        # Statistical profiling
        profile.statistical_profile = self._calculate_statistics(non_null_values, profile.inferred_type)
        
        # Sample values
        profile.sample_values = self._collect_samples(values, non_null_values, unique_values)
        
        # Quality scoring
        profile.quality_score, profile.quality_issues = self._calculate_quality_score(profile)
        
        # Recommendations
        profile.recommendations = self._generate_recommendations(profile)
        
        # Analysis duration
        end_time = datetime.now()
        profile.analysis_duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        logger.info(
            f"[ForensicAnalyzer] Analysis complete: {column_name} | "
            f"Type: {profile.inferred_type} | "
            f"Quality: {profile.quality_score} | "
            f"PII: {profile.pii_detected} | "
            f"Duration: {profile.analysis_duration_ms}ms",
            "ForensicAnalyzer"
        )
        
        return profile
    
    async def save_profile(self, profile: ColumnProfile) -> str:
        """
        Save column profile to database
        
        Args:
            profile: ColumnProfile to save
            
        Returns:
            Profile ID (UUID)
        """
        try:
            data = profile.to_dict()
            
            # Remove profile_id if None (let DB generate it)
            if not data.get("profile_id"):
                data.pop("profile_id", None)
            
            response = (
                self.db.client
                .table("utm_column_profiles")
                .upsert(data, on_conflict="project_id,object_name,column_name")
                .execute()
            )
            
            profile_id = response.data[0]["profile_id"]
            
            logger.info(
                f"[ForensicAnalyzer] Profile saved: {profile.column_name} -> {profile_id}",
                "ForensicAnalyzer"
            )
            
            return profile_id
            
        except Exception as e:
            logger.error(
                f"[ForensicAnalyzer] Error saving profile: {e}",
                "ForensicAnalyzer"
            )
            raise
    
    async def get_profile(
        self,
        project_id: str,
        object_name: str,
        column_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get existing column profile from database
        
        Args:
            project_id: Project ID
            object_name: Object name
            column_name: Column name
            
        Returns:
            Profile dictionary or None
        """
        try:
            query = (
                self.db.client
                .table("utm_column_profiles")
                .select("*")
                .eq("project_id", project_id)
                .eq("object_name", object_name)
                .eq("column_name", column_name)
            )
            
            if self.tenant_id:
                query = query.eq("tenant_id", self.tenant_id)
            
            response = query.single().execute()
            
            return response.data if response.data else None
            
        except Exception as e:
            logger.warning(
                f"[ForensicAnalyzer] Profile not found: {object_name}.{column_name}",
                "ForensicAnalyzer"
            )
            return None
    
    # Private helper methods
    
    def _infer_type(self, values: List[Any]) -> tuple[str, float]:
        """
        Infer data type from values
        
        Returns:
            (type_name, confidence) tuple
        """
        if not values:
            return ("STRING", 0.0)
        
        # Count type matches
        type_counts = {
            "INTEGER": 0,
            "DECIMAL": 0,
            "BOOLEAN": 0,
            "DATE": 0,
            "TIMESTAMP": 0,
            "STRING": 0
        }
        
        for value in values[:1000]:  # Sample first 1000 values
            str_value = str(value).strip()
            
            # Try integer
            try:
                int(str_value)
                type_counts["INTEGER"] += 1
                continue
            except:
                pass
            
            # Try decimal
            try:
                float(str_value)
                type_counts["DECIMAL"] += 1
                continue
            except:
                pass
            
            # Try boolean
            if str_value.lower() in ["true", "false", "yes", "no", "1", "0"]:
                type_counts["BOOLEAN"] += 1
                continue
            
            # Try date patterns
            if re.match(self.PATTERNS["DATE_YYYYMMDD"], str_value) or \
               re.match(self.PATTERNS["DATE_MMDDYYYY"], str_value):
                type_counts["DATE"] += 1
                continue
            
            # Default to string
            type_counts["STRING"] += 1
        
        # Find dominant type
        max_type = max(type_counts, key=type_counts.get)
        total = sum(type_counts.values())
        confidence = type_counts[max_type] / total if total > 0 else 0.0
        
        return (max_type, confidence)
    
    def _detect_patterns(self, values: List[Any]) -> List[str]:
        """Detect data patterns in values"""
        detected = []
        sample_size = min(len(values), 100)
        
        if sample_size == 0:
            return detected
        
        for pattern_name, pattern_regex in self.PATTERNS.items():
            matches = sum(1 for v in values[:sample_size] if re.search(pattern_regex, str(v)))
            
            # If >50% of samples match, consider pattern detected
            if matches / sample_size > 0.5:
                detected.append(pattern_name)
        
        return detected
    
    def _semantic_tagging(
        self,
        column_name: str,
        values: List[Any],
        patterns: List[str]
    ) -> List[str]:
        """Generate semantic tags based on column name and patterns"""
        tags = []
        
        # From patterns
        tags.extend(patterns)
        
        # From column name heuristics
        col_lower = column_name.lower()
        
        if any(word in col_lower for word in ["email", "e-mail", "mail"]):
            tags.append("EMAIL")
        if any(word in col_lower for word in ["phone", "tel", "mobile", "cell"]):
            tags.append("PHONE")
        if "ssn" in col_lower or "social_security" in col_lower:
            tags.append("SSN")
        if "credit" in col_lower or "card" in col_lower:
            tags.append("CREDIT_CARD")
        if any(word in col_lower for word in ["address", "street", "city", "state"]):
            tags.append("ADDRESS")
        if any(word in col_lower for word in ["name", "first_name", "last_name"]):
            tags.append("NAME")
        
        return list(set(tags))  # Remove duplicates
    
    def _calculate_pii_confidence(self, tags: List[str], values: List[Any]) -> float:
        """Calculate confidence that column contains PII"""
        pii_tag_count = sum(1 for tag in tags if tag in self.PII_TAGS)
        
        if pii_tag_count == 0:
            return 0.0
        elif pii_tag_count >= 2:
            return 1.0
        else:
            return 0.7
    
    def _calculate_statistics(self, values: List[Any], inferred_type: str) -> Dict[str, Any]:
        """Calculate statistical profile based on type"""
        stats = {}
        
        if not values:
            return stats
        
        if inferred_type in ["INTEGER", "DECIMAL"]:
            # Numeric statistics
            try:
                numeric_values = [float(v) for v in values if v is not None]
                
                if numeric_values:
                    stats["min"] = min(numeric_values)
                    stats["max"] = max(numeric_values)
                    stats["mean"] = statistics.mean(numeric_values)
                    stats["median"] = statistics.median(numeric_values)
                    
                    if len(numeric_values) > 1:
                        stats["stddev"] = statistics.stdev(numeric_values)
                    
                    # Percentiles
                    sorted_values = sorted(numeric_values)
                    stats["percentiles"] = {
                        "p25": sorted_values[len(sorted_values) // 4],
                        "p50": sorted_values[len(sorted_values) // 2],
                        "p75": sorted_values[3 * len(sorted_values) // 4],
                        "p95": sorted_values[95 * len(sorted_values) // 100] if len(sorted_values) >= 100 else sorted_values[-1]
                    }
            except Exception as e:
                logger.warning(f"[ForensicAnalyzer] Numeric stats failed: {e}", "ForensicAnalyzer")
        
        elif inferred_type == "STRING":
            # String statistics
            str_values = [str(v) for v in values if v is not None]
            
            if str_values:
                lengths = [len(s) for s in str_values]
                stats["min_length"] = min(lengths)
                stats["max_length"] = max(lengths)
                stats["avg_length"] = statistics.mean(lengths)
        
        return stats
    
    def _collect_samples(
        self,
        all_values: List[Any],
        non_null_values: List[Any],
        unique_values: set
    ) -> Dict[str, Any]:
        """Collect sample values for preview"""
        samples = {}
        
        # Clean samples (first 10 non-null)
        samples["clean_samples"] = [str(v) for v in non_null_values[:10]]
        
        # Top values (most common)
        from collections import Counter
        value_counts = Counter(str(v) for v in non_null_values)
        samples["top_values"] = [
            {"value": value, "count": count}
            for value, count in value_counts.most_common(5)
        ]
        
        # Distinct samples
        samples["distinct_samples"] = [str(v) for v in list(unique_values)[:10]]
        
        return samples
    
    def _calculate_quality_score(self, profile: ColumnProfile) -> tuple[int, List[str]]:
        """
        Calculate quality score (0-100) and identify issues
        
        Returns:
            (score, issues) tuple
        """
        score = 100
        issues = []
        
        # Deduct for high nullability
        if profile.nullability_score > 0.5:
            score -= 30
            issues.append("HIGH_NULLABILITY")
        elif profile.nullability_score > 0.2:
            score -= 15
            issues.append("MODERATE_NULLABILITY")
        
        # Deduct for low cardinality (possible data quality issue)
        if profile.distinct_ratio < 0.1 and profile.total_rows > 100:
            score -= 20
            issues.append("LOW_CARDINALITY")
        
        # Deduct for low type confidence
        if profile.type_confidence < 0.7:
            score -= 15
            issues.append("INCONSISTENT_TYPE")
        
        # Bonus for PII detection (good metadata)
        if profile.pii_detected and profile.pii_confidence > 0.8:
            # Don't add score, but mark as important
            issues.append("PII_DETECTED")
        
        score = max(0, min(100, score))  # Clamp to 0-100
        
        return (score, issues)
    
    def _generate_recommendations(self, profile: ColumnProfile) -> Dict[str, Any]:
        """Generate recommendations for column"""
        recommendations = {}
        
        # Type recommendation
        recommendations["suggested_type"] = profile.inferred_type
        
        # Nullability constraint
        if profile.nullability_score < 0.01:
            recommendations["add_not_null"] = True
        else:
            recommendations["add_not_null"] = False
        
        # Unique constraint
        if profile.distinct_ratio > 0.99 and profile.total_rows > 10:
            recommendations["add_unique_constraint"] = True
        else:
            recommendations["add_unique_constraint"] = False
        
        # PII masking
        if profile.pii_detected:
            recommendations["pii_action"] = "MASK"
            recommendations["pii_method"] = "SHA256" if "SSN" in profile.semantic_tags else "PARTIAL_MASK"
        
        return recommendations

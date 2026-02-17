"""
CompatibilityChecker - Sprint 10: Schema Evolution

Purpose: Verify backward compatibility between schema versions, detect breaking
changes, and suggest column mappings for renamed columns using heuristic matching.

This service enables:
- Backward compatibility validation
- Breaking vs non-breaking change classification
- Column rename detection (similarity matching)
- Compatibility scoring (0-100%)
- Migration safety recommendations

Author: UTM Platform Team
Created: February 11, 2026
Sprint: 10 (Schema Evolution)
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from difflib import SequenceMatcher
from apps.api.services.schema_version_service import SchemaChange, SchemaSnapshot, SchemaColumn


@dataclass
class CompatibilityResult:
    """Result of compatibility check between two schema versions."""
    compatible: bool
    compatibility_score: float  # 0-100
    breaking_changes: List[SchemaChange]
    non_breaking_changes: List[SchemaChange]
    suggested_column_mappings: Dict[str, str]  # old_name -> new_name
    warnings: List[str]
    safety_score: float  # 0-100, higher is safer
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "compatible": self.compatible,
            "compatibility_score": self.compatibility_score,
            "breaking_changes": [c.to_dict() for c in self.breaking_changes],
            "non_breaking_changes": [c.to_dict() for c in self.non_breaking_changes],
            "suggested_column_mappings": self.suggested_column_mappings,
            "warnings": self.warnings,
            "safety_score": self.safety_score
        }


class CompatibilityChecker:
    """
    Service for checking backward compatibility between schema versions.
    
    This service analyzes schema changes and determines if they are backward
    compatible. It also provides intelligent suggestions for handling schema
    evolution, including column rename detection.
    
    Compatibility Rules:
    - ✅ COMPATIBLE: Adding nullable columns
    - ✅ COMPATIBLE: Making columns more permissive (nullable)
    - ✅ COMPATIBLE: Adding indexes/constraints that don't affect data
    - ❌ INCOMPATIBLE: Removing columns
    - ❌ INCOMPATIBLE: Changing column types
    - ❌ INCOMPATIBLE: Making columns NOT NULL
    - ❌ INCOMPATIBLE: Changing primary keys
    
    Usage:
        checker = CompatibilityChecker()
        
        # Check compatibility between versions
        result = checker.check_compatibility(old_snapshot, new_snapshot)
        
        if result.compatible:
            print(f"Compatibility score: {result.compatibility_score}%")
        else:
            print(f"Breaking changes detected: {len(result.breaking_changes)}")
    """
    
    def __init__(self, similarity_threshold: float = 0.7):
        """
        Initialize CompatibilityChecker.
        
        Args:
            similarity_threshold: Threshold for column name similarity (0-1)
                                Used for detecting renamed columns
        """
        self.similarity_threshold = similarity_threshold
    
    def check_compatibility(
        self,
        old_snapshot: SchemaSnapshot,
        new_snapshot: SchemaSnapshot,
        detect_renames: bool = True
    ) -> CompatibilityResult:
        """
        Check backward compatibility between two schema snapshots.
        
        Args:
            old_snapshot: Previous schema version
            new_snapshot: Current schema version
            detect_renames: If True, attempt to detect renamed columns
            
        Returns:
            CompatibilityResult with detailed analysis
        """
        # Detect changes
        from apps.api.services.schema_version_service import SchemaVersionService
        version_service = SchemaVersionService("temp", "temp")
        changes = version_service._detect_changes(old_snapshot, new_snapshot)
        
        # Classify changes
        breaking = [c for c in changes if c.is_breaking]
        non_breaking = [c for c in changes if not c.is_breaking]
        
        # Detect potential column renames
        suggested_mappings = {}
        if detect_renames:
            suggested_mappings = self._detect_column_renames(
                old_snapshot, new_snapshot, changes
            )
        
        # Calculate compatibility score
        compatibility_score = self._calculate_compatibility_score(
            len(breaking), len(non_breaking), len(suggested_mappings)
        )
        
        # Calculate safety score
        safety_score = self._calculate_safety_score(changes)
        
        # Generate warnings
        warnings = self._generate_warnings(changes, suggested_mappings)
        
        # Determine overall compatibility
        compatible = len(breaking) == 0
        
        return CompatibilityResult(
            compatible=compatible,
            compatibility_score=compatibility_score,
            breaking_changes=breaking,
            non_breaking_changes=non_breaking,
            suggested_column_mappings=suggested_mappings,
            warnings=warnings,
            safety_score=safety_score
        )
    
    def _detect_column_renames(
        self,
        old_snapshot: SchemaSnapshot,
        new_snapshot: SchemaSnapshot,
        changes: List[SchemaChange]
    ) -> Dict[str, str]:
        """
        Detect potential column renames using similarity matching.
        
        This uses heuristic matching to identify columns that may have been
        renamed rather than removed/added. Considers:
        - Name similarity (Levenshtein distance)
        - Type matching
        - Position in schema
        
        Args:
            old_snapshot: Previous schema
            new_snapshot: Current schema
            changes: List of detected changes
            
        Returns:
            Dictionary mapping old column names to suggested new names
        """
        # Extract removed and added columns
        removed_cols = {
            c.column_name: c.old_value
            for c in changes if c.change_type == "removed"
        }
        added_cols = {
            c.column_name: c.new_value
            for c in changes if c.change_type == "added"
        }
        
        if not removed_cols or not added_cols:
            return {}
        
        mappings = {}
        
        for old_name, old_col_data in removed_cols.items():
            best_match = None
            best_score = 0.0
            
            for new_name, new_col_data in added_cols.items():
                # Skip if already mapped
                if new_name in mappings.values():
                    continue
                
                # Calculate similarity score
                name_similarity = self._calculate_name_similarity(old_name, new_name)
                
                # Bonus points if types match
                type_match_bonus = 0.2 if old_col_data.get("data_type") == new_col_data.get("data_type") else 0
                
                # Total score
                score = name_similarity + type_match_bonus
                
                if score > best_score and score >= self.similarity_threshold:
                    best_score = score
                    best_match = new_name
            
            if best_match:
                mappings[old_name] = best_match
        
        return mappings
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity between two column names.
        
        Uses SequenceMatcher (Ratcliff/Obershelp algorithm) to compute
        similarity ratio between two strings.
        
        Args:
            name1: First column name
            name2: Second column name
            
        Returns:
            Similarity score (0-1), where 1 is identical
        """
        # Normalize names (lowercase, remove underscores/spaces)
        norm1 = name1.lower().replace("_", "").replace(" ", "")
        norm2 = name2.lower().replace("_", "").replace(" ", "")
        
        # Calculate sequence similarity
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    def _calculate_compatibility_score(
        self,
        breaking_count: int,
        non_breaking_count: int,
        rename_count: int
    ) -> float:
        """
        Calculate overall compatibility score (0-100).
        
        Formula:
        - Start at 100
        - Subtract 20 points per breaking change
        - Subtract 5 points per non-breaking change
        - Add 10 points per detected rename (reduces impact)
        - Minimum score: 0
        
        Args:
            breaking_count: Number of breaking changes
            non_breaking_count: Number of non-breaking changes
            rename_count: Number of detected renames
            
        Returns:
            Compatibility score (0-100)
        """
        score = 100.0
        score -= breaking_count * 20    # Major penalty for breaking changes
        score -= non_breaking_count * 5  # Minor penalty for non-breaking changes
        score += rename_count * 10       # Bonus for detected renames
        
        return max(0.0, min(100.0, score))
    
    def _calculate_safety_score(self, changes: List[SchemaChange]) -> float:
        """
        Calculate migration safety score (0-100).
        
        Higher score = safer migration
        Lower score = requires more caution
        
        Factors:
        - Type changes: -15 points each
        - Column removals: -25 points each
        - PK changes: -40 points each
        - Nullable additions: -2 points each
        - Column additions: -5 points each
        
        Args:
            changes: List of schema changes
            
        Returns:
            Safety score (0-100)
        """
        score = 100.0
        
        for change in changes:
            if change.change_type == "removed":
                score -= 25
            elif change.change_type == "added":
                if not change.new_value.get("nullable", True):
                    score -= 10  # Non-nullable addition is risky
                else:
                    score -= 2   # Nullable addition is safe
            elif change.change_type == "modified":
                if "type" in str(change.old_value):
                    score -= 15  # Type change is moderately risky
                if "primary_key" in str(change.old_value):
                    score -= 40  # PK change is very risky
                if "nullable" in str(change.old_value):
                    if not change.new_value.get("nullable", True):
                        score -= 20  # Making NOT NULL is risky
                    else:
                        score -= 5   # Making nullable is less risky
        
        return max(0.0, min(100.0, score))
    
    def _generate_warnings(
        self,
        changes: List[SchemaChange],
        suggested_mappings: Dict[str, str]
    ) -> List[str]:
        """
        Generate human-readable warnings for schema changes.
        
        Args:
            changes: List of schema changes
            suggested_mappings: Suggested column renames
            
        Returns:
            List of warning messages
        """
        warnings = []
        
        # Breaking change warnings
        for change in changes:
            if not change.is_breaking:
                continue
            
            if change.change_type == "removed":
                if change.column_name in suggested_mappings:
                    new_name = suggested_mappings[change.column_name]
                    warnings.append(
                        f"⚠️ Column '{change.column_name}' appears to be renamed to '{new_name}'. "
                        f"Consider using column mapping to preserve compatibility."
                    )
                else:
                    warnings.append(
                        f"❌ BREAKING: Column '{change.column_name}' removed. "
                        f"Existing queries will fail."
                    )
            
            elif change.change_type == "modified":
                if "type" in str(change.old_value):
                    old_type = change.old_value.get("type")
                    new_type = change.new_value.get("type")
                    warnings.append(
                        f"❌ BREAKING: Column '{change.column_name}' type changed "
                        f"from {old_type} to {new_type}. Data migration required."
                    )
                
                if "nullable" in str(change.old_value):
                    if not change.new_value.get("nullable", True):
                        warnings.append(
                            f"❌ BREAKING: Column '{change.column_name}' now NOT NULL. "
                            f"Existing NULL values will cause errors."
                        )
        
        # Non-breaking change warnings
        non_breaking = [c for c in changes if not c.is_breaking]
        if non_breaking:
            warnings.append(
                f"ℹ️ {len(non_breaking)} non-breaking change(s) detected. "
                f"Backward compatible, but test thoroughly."
            )
        
        return warnings
    
    def validate_column_mapping(
        self,
        old_snapshot: SchemaSnapshot,
        new_snapshot: SchemaSnapshot,
        mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Validate a proposed column mapping.
        
        Checks:
        - Old columns exist in old schema
        - New columns exist in new schema
        - Types are compatible
        - No duplicate mappings
        
        Args:
            old_snapshot: Previous schema
            new_snapshot: Current schema
            mapping: Proposed column mapping (old_name -> new_name)
            
        Returns:
            Validation result with errors
        """
        errors = []
        warnings = []
        
        old_cols = {col.name: col for col in old_snapshot.columns}
        new_cols = {col.name: col for col in new_snapshot.columns}
        
        # Check for invalid old column names
        for old_name in mapping.keys():
            if old_name not in old_cols:
                errors.append(f"Old column '{old_name}' not found in old schema")
        
        # Check for invalid new column names
        for new_name in mapping.values():
            if new_name not in new_cols:
                errors.append(f"New column '{new_name}' not found in new schema")
        
        # Check for duplicate target mappings
        new_names = list(mapping.values())
        duplicates = [name for name in new_names if new_names.count(name) > 1]
        if duplicates:
            errors.append(f"Duplicate target columns: {', '.join(set(duplicates))}")
        
        # Check type compatibility
        for old_name, new_name in mapping.items():
            if old_name in old_cols and new_name in new_cols:
                old_type = old_cols[old_name].data_type
                new_type = new_cols[new_name].data_type
                
                if old_type != new_type:
                    warnings.append(
                        f"Type mismatch: '{old_name}' ({old_type}) -> '{new_name}' ({new_type}). "
                        f"Data conversion may be required."
                    )
        
        valid = len(errors) == 0
        
        return {
            "valid": valid,
            "errors": errors,
            "warnings": warnings,
            "mapping_count": len(mapping)
        }
    
    def suggest_migration_strategy(
        self,
        compatibility_result: CompatibilityResult
    ) -> Dict[str, Any]:
        """
        Suggest migration strategy based on compatibility analysis.
        
        Args:
            compatibility_result: Result from check_compatibility()
            
        Returns:
            Dictionary with recommended strategy and steps
        """
        if compatibility_result.compatibility_score >= 90:
            strategy = "SIMPLE_DEPLOY"
            steps = [
                "1. Run migration script",
                "2. Deploy new code",
                "3. Monitor for errors"
            ]
            risk_level = "LOW"
        
        elif compatibility_result.compatibility_score >= 70:
            strategy = "STAGED_DEPLOY"
            steps = [
                "1. Create backup",
                "2. Run migration in staging",
                "3. Validate data integrity",
                "4. Deploy to production during low-traffic window",
                "5. Monitor closely for 24 hours"
            ]
            risk_level = "MEDIUM"
        
        elif compatibility_result.compatibility_score >= 40:
            strategy = "BLUE_GREEN_DEPLOY"
            steps = [
                "1. Create complete backup",
                "2. Set up parallel environment (blue/green)",
                "3. Run migration on green environment",
                "4. Run extensive validation tests",
                "5. Gradually route traffic to green",
                "6. Keep blue environment for 48h rollback window",
                "7. Decommission blue after validation"
            ]
            risk_level = "HIGH"
        
        else:
            strategy = "MANUAL_MIGRATION"
            steps = [
                "1. Full database backup",
                "2. Document all breaking changes",
                "3. Create data migration scripts",
                "4. Schedule maintenance window",
                "5. Run migration with DBA supervision",
                "6. Validate all data transformations",
                "7. Test all dependent systems",
                "8. Keep rollback plan ready",
                "9. Extended monitoring (72h)"
            ]
            risk_level = "CRITICAL"
        
        return {
            "strategy": strategy,
            "risk_level": risk_level,
            "recommended_steps": steps,
            "requires_dba_approval": risk_level in ["HIGH", "CRITICAL"],
            "requires_maintenance_window": risk_level == "CRITICAL",
            "estimated_downtime_minutes": self._estimate_downtime(compatibility_result)
        }
    
    def _estimate_downtime(self, compatibility_result: CompatibilityResult) -> int:
        """
        Estimate downtime required for migration (in minutes).
        
        Args:
            compatibility_result: Compatibility analysis result
            
        Returns:
            Estimated downtime in minutes
        """
        base_downtime = 5  # Minimum downtime for any migration
        
        # Add time per change
        downtime = base_downtime
        downtime += len(compatibility_result.breaking_changes) * 10
        downtime += len(compatibility_result.non_breaking_changes) * 2
        
        # Type changes require additional time
        type_changes = [
            c for c in compatibility_result.breaking_changes
            if "type" in str(c.old_value)
        ]
        downtime += len(type_changes) * 15
        
        return downtime

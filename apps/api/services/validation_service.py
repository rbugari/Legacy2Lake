"""
Real-Time Validation Service - Sprint 8
========================================

Purpose:
    Validates generated code DURING generation (not after).
    Provides immediate feedback to Agent C for syntax errors,
    missing imports, and technology-specific compliance.

Features:
    - Python syntax validation (ast module)
    - SQL syntax validation (sqlparse + dialect-specific)
    - Technology-specific checks (PySpark, Snowflake, DBT, etc.)
    - Test case generation from code
    - Performance suggestions

Usage:
    validator = ValidationService()
    result = await validator.validate_code(code, tech_id='pyspark', layer='bronze')
    
    if not result.is_valid:
        # Return errors to Agent C for regeneration
        feedback = result.get_llm_feedback()

Integration:
    - Called by Agent C during transpile_task()
    - Results stored in utm_code_validations table
    - Frontend shows realtime validation status

Author: Legacy2Lake Engineering
Date: 2026-02-11 (Sprint 8)
Version: v1.0
"""

import ast
import re
import sqlparse
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

try:
    from apps.api.utils.logger import logger
except ImportError:
    from utils.logger import logger


# ================================================================
# ENUMS & DATA CLASSES
# ================================================================

class ValidationLevel(Enum):
    """Validation severity levels"""
    ERROR = "ERROR"          # Blocking issue (syntax error, missing imports)
    WARNING = "WARNING"      # Non-blocking issue (missing logging, no docs)
    INFO = "INFO"            # Informational (style suggestion, optimization)


class TechnologyType(Enum):
    """Supported technology types"""
    PYSPARK = "pyspark"
    SNOWFLAKE = "snowflake"
    FABRIC = "fabric"
    DBT = "dbt"
    AWS_GLUE = "aws"
    GCP_BIGQUERY = "gcp"
    GENERIC = "generic"
    SALESFORCE = "salesforce"


@dataclass
class ValidationIssue:
    """Individual validation issue"""
    level: ValidationLevel
    check_name: str
    message: str
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None


@dataclass
class ValidationResult:
    """Complete validation result"""
    is_valid: bool
    tech_id: str
    layer: str
    issues: List[ValidationIssue] = field(default_factory=list)
    warnings_count: int = 0
    errors_count: int = 0
    info_count: int = 0
    validated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def get_llm_feedback(self) -> str:
        """
        Format validation issues as feedback for LLM regeneration.
        
        Returns:
            Human-readable feedback string for Agent C
        """
        if self.is_valid:
            return "✅ Code validation passed. No issues detected."
        
        feedback_lines = ["❌ Code validation failed. Please fix the following issues:\n"]
        
        # Group by level
        errors = [issue for issue in self.issues if issue.level == ValidationLevel.ERROR]
        warnings = [issue for issue in self.issues if issue.level == ValidationLevel.WARNING]
        
        if errors:
            feedback_lines.append("**ERRORS (must fix):**")
            for i, issue in enumerate(errors, 1):
                location = f" (line {issue.line_number})" if issue.line_number else ""
                feedback_lines.append(f"{i}. {issue.check_name}{location}: {issue.message}")
                if issue.suggestion:
                    feedback_lines.append(f"   → Suggestion: {issue.suggestion}")
            feedback_lines.append("")
        
        if warnings:
            feedback_lines.append("**WARNINGS (recommended fixes):**")
            for i, issue in enumerate(warnings, 1):
                feedback_lines.append(f"{i}. {issue.check_name}: {issue.message}")
            feedback_lines.append("")
        
        feedback_lines.append("Please regenerate the code addressing the ERRORS above.")
        
        return "\n".join(feedback_lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            'is_valid': self.is_valid,
            'tech_id': self.tech_id,
            'layer': self.layer,
            'errors_count': self.errors_count,
            'warnings_count': self.warnings_count,
            'info_count': self.info_count,
            'validated_at': self.validated_at,
            'issues': [
                {
                    'level': issue.level.value,
                    'check_name': issue.check_name,
                    'message': issue.message,
                    'line_number': issue.line_number,
                    'suggestion': issue.suggestion
                }
                for issue in self.issues
            ]
        }


# ================================================================
# VALIDATION SERVICE
# ================================================================

class ValidationService:
    """
    Main validation service for real-time code validation.
    Supports Python (PySpark, Fabric, AWS) and SQL (Snowflake, DBT).
    """
    
    # Technology-specific required patterns
    TECH_REQUIREMENTS = {
        TechnologyType.PYSPARK: {
            'required_imports': ['pyspark.sql', 'SparkSession'],
            'required_patterns': ['SparkSession.builder', '.read.', '.write.'],
            'recommended_patterns': ['try:', 'except', 'logger', 'add_ingestion_metadata'],
            'forbidden_patterns': ['pandas.DataFrame']  # Should use Spark DataFrames
        },
        TechnologyType.SNOWFLAKE: {
            'required_patterns': ['COPY INTO', 'CREATE OR REPLACE', 'MERGE INTO'],
            'recommended_patterns': ['COMMENT', 'BEGIN', 'COMMIT'],
            'forbidden_patterns': []
        },
        TechnologyType.DBT: {
            'required_patterns': ['{{', '}}', 'config(', 'ref('],
            'recommended_patterns': ['source(', 'test'],
            'forbidden_patterns': []
        },
        TechnologyType.FABRIC: {
            'required_imports': ['pyspark.sql', 'notebookutils'],
            'required_patterns': ['spark.read.', 'spark.write.'],
            'recommended_patterns': ['notebookutils.'],
            'forbidden_patterns': []
        },
        TechnologyType.AWS_GLUE: {
            'required_imports': ['awsglue', 'GlueContext'],
            'required_patterns': ['GlueContext(', 'Job.init', 'Job.commit'],
            'recommended_patterns': ['DynamicFrame'],
            'forbidden_patterns': []
        }
    }
    
    def __init__(self):
        self.version = "v1.0"

    def _pattern_exists(self, code: str, pattern: str, tech_type: TechnologyType) -> bool:
        """Allow modern target-specific equivalents for coarse required patterns."""
        if pattern in code:
            return True

        if tech_type == TechnologyType.PYSPARK and pattern == '.write.':
            return bool(re.search(r'\.write(?:Stream)?\b|saveAsTable\s*\(|insertInto\s*\(|save\s*\(|merge\s*\(', code))

        return False
    
    
    async def validate_code(
        self,
        code: str,
        tech_id: str,
        layer: str = "bronze",
        context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Main validation entry point.
        
        Args:
            code: Generated code to validate
            tech_id: Technology ID (pyspark, snowflake, dbt, etc.)
            layer: Medallion layer (bronze, silver, gold)
            context: Optional context (source_table, target_table, etc.)
        
        Returns:
            ValidationResult with all issues found
        """
        logger.info(f"[Validator] Validating {tech_id} {layer} code ({len(code)} chars)", "Validator")
        
        issues: List[ValidationIssue] = []
        
        # Step 1: Basic checks (empty, too short)
        basic_issues = self._basic_checks(code)
        issues.extend(basic_issues)
        
        # If code is fundamentally broken, stop here
        if any(issue.level == ValidationLevel.ERROR for issue in basic_issues):
            return self._build_result(tech_id, layer, issues)
        
        # Step 2: Language-specific validation
        tech_type = self._get_tech_type(tech_id)
        
        if tech_type in [TechnologyType.PYSPARK, TechnologyType.FABRIC, TechnologyType.AWS_GLUE]:
            # Python-based technologies
            syntax_issues = self._validate_python_syntax(code)
            issues.extend(syntax_issues)
            
            tech_issues = self._validate_python_tech(code, tech_type, layer)
            issues.extend(tech_issues)
        
        elif tech_type in [TechnologyType.SNOWFLAKE, TechnologyType.DBT]:
            # SQL-based technologies
            syntax_issues = self._validate_sql_syntax(code, tech_type)
            issues.extend(syntax_issues)
            
            tech_issues = self._validate_sql_tech(code, tech_type, layer)
            issues.extend(tech_issues)
        
        elif tech_type == TechnologyType.GENERIC:
            # Generic/pseudocode
            generic_issues = self._validate_generic(code, layer)
            issues.extend(generic_issues)
        
        # Step 3: Layer-specific checks
        layer_issues = self._validate_layer_requirements(code, layer, tech_type)
        issues.extend(layer_issues)

        # Step 4: Direct-mode zero-hardcode checks
        if str(layer).lower() == "direct":
            direct_issues = self._validate_direct_zero_hardcode(code, tech_type)
            issues.extend(direct_issues)
        
        # Step 5: Integrity checks (placeholders)
        integrity_issues = self._validate_placeholders(code)
        issues.extend(integrity_issues)
        
        # Build final result
        result = self._build_result(tech_id, layer, issues)
        
        logger.info(
            f"[Validator] Validation complete: {'PASS' if result.is_valid else 'FAIL'} "
            f"({result.errors_count} errors, {result.warnings_count} warnings)",
            "Validator"
        )
        
        return result
    
    
    def _basic_checks(self, code: str) -> List[ValidationIssue]:
        """Basic checks on code quality"""
        issues = []
        
        # Check 1: Non-empty
        if not code or len(code.strip()) == 0:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                check_name="empty_code",
                message="Generated code is empty",
                suggestion="Regenerate code with valid content"
            ))
            return issues  # Stop if empty
        
        # Check 2: Minimum length
        if len(code.strip()) < 50:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                check_name="too_short",
                message=f"Generated code is too short ({len(code)} chars)",
                suggestion="Code should be at least 50 characters"
            ))
        
        # Check 3: Has comments (recommended)
        if '#' not in code and '--' not in code and '/*' not in code:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                check_name="no_comments",
                message="No comments found in code",
                suggestion="Add comments to explain logic"
            ))
        
        return issues
    
    
    def _validate_python_syntax(self, code: str) -> List[ValidationIssue]:
        """Validate Python syntax using AST"""
        issues = []
        
        try:
            ast.parse(code)
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                check_name="python_syntax",
                message="✅ Python syntax is valid"
            ))
        except SyntaxError as e:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                check_name="python_syntax",
                message=f"Syntax error: {e.msg}",
                line_number=e.lineno,
                column_number=e.offset,
                suggestion="Fix syntax error before proceeding"
            ))
        except Exception as e:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                check_name="python_syntax",
                message=f"Failed to parse Python code: {str(e)}",
                suggestion="Ensure code is valid Python"
            ))
        
        return issues
    
    
    def _validate_python_tech(
        self,
        code: str,
        tech_type: TechnologyType,
        layer: str
    ) -> List[ValidationIssue]:
        """Technology-specific Python validation"""
        issues = []
        
        if tech_type not in self.TECH_REQUIREMENTS:
            return issues
        
        requirements = self.TECH_REQUIREMENTS[tech_type]
        
        # Layer-aware relaxation: silver/gold code can receive Spark session from runtime entrypoint.
        relaxed_runtime_spark = tech_type == TechnologyType.PYSPARK and str(layer).lower() != "direct"

        # Check required imports
        if 'required_imports' in requirements:
            for required_import in requirements['required_imports']:
                if relaxed_runtime_spark and required_import == 'SparkSession':
                    continue
                if required_import not in code:
                    issues.append(ValidationIssue(
                        level=ValidationLevel.ERROR,
                        check_name="missing_import",
                        message=f"Missing required import: {required_import}",
                        suggestion=f"Add 'from {required_import}' or 'import {required_import}'"
                    ))
        
        # Check required patterns
        if 'required_patterns' in requirements:
            for pattern in requirements['required_patterns']:
                if relaxed_runtime_spark and pattern == 'SparkSession.builder':
                    continue
                if not self._pattern_exists(code, pattern, tech_type):
                    issues.append(ValidationIssue(
                        level=ValidationLevel.ERROR,
                        check_name="missing_pattern",
                        message=f"Missing required pattern: {pattern}",
                        suggestion=f"Code must use {pattern}"
                    ))
        
        # Check recommended patterns
        if 'recommended_patterns' in requirements:
            for pattern in requirements['recommended_patterns']:
                if pattern not in code:
                    issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        check_name="missing_recommended",
                        message=f"Missing recommended pattern: {pattern}",
                        suggestion=f"Consider adding {pattern} for best practices"
                    ))
        
        # Check forbidden patterns
        if 'forbidden_patterns' in requirements:
            for pattern in requirements['forbidden_patterns']:
                if pattern in code:
                    issues.append(ValidationIssue(
                        level=ValidationLevel.ERROR,
                        check_name="forbidden_pattern",
                        message=f"Forbidden pattern detected: {pattern}",
                        suggestion=f"Remove {pattern} - not compatible with {tech_type.value}"
                    ))
        
        return issues
    
    
    def _validate_sql_syntax(self, code: str, tech_type: TechnologyType) -> List[ValidationIssue]:
        """Validate SQL syntax using sqlparse"""
        issues = []
        
        try:
            # Parse SQL
            parsed = sqlparse.parse(code)
            
            if not parsed or len(parsed) == 0:
                issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    check_name="sql_syntax",
                    message="Failed to parse SQL code",
                    suggestion="Check SQL syntax"
                ))
            else:
                issues.append(ValidationIssue(
                    level=ValidationLevel.INFO,
                    check_name="sql_syntax",
                    message=f"✅ SQL syntax appears valid ({len(parsed)} statements)"
                ))
        
        except Exception as e:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                check_name="sql_syntax",
                message=f"SQL parsing error: {str(e)}",
                suggestion="Ensure code is valid SQL"
            ))
        
        return issues
    
    
    def _validate_sql_tech(
        self,
        code: str,
        tech_type: TechnologyType,
        layer: str
    ) -> List[ValidationIssue]:
        """Technology-specific SQL validation"""
        issues = []
        
        if tech_type not in self.TECH_REQUIREMENTS:
            return issues
        
        requirements = self.TECH_REQUIREMENTS[tech_type]
        
        # Check required patterns
        if 'required_patterns' in requirements:
            for pattern in requirements['required_patterns']:
                if pattern not in code:
                    issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        check_name="missing_sql_pattern",
                        message=f"Missing recommended SQL pattern: {pattern}",
                        suggestion=f"Consider using {pattern} for {tech_type.value}"
                    ))
        
        return issues
    
    
    def _validate_generic(self, code: str, layer: str) -> List[ValidationIssue]:
        """Validate generic/pseudocode"""
        issues = []
        
        # Generic code should have structure keywords
        structure_keywords = ['STEP', 'Step', '1.', '2.', 'Extract', 'Transform', 'Load']
        
        if not any(kw in code for kw in structure_keywords):
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                check_name="generic_structure",
                message="Generic code lacks clear step structure",
                suggestion="Use STEP 1, STEP 2, etc. or Extract/Transform/Load patterns"
            ))
        
        # Should mention layer
        if layer.lower() not in code.lower():
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                check_name="layer_mention",
                message=f"Layer '{layer}' not mentioned in code",
                suggestion=f"Consider adding '{layer}' reference for clarity"
            ))
        
        return issues
    
    
    def _validate_layer_requirements(
        self,
        code: str,
        layer: str,
        tech_type: TechnologyType
    ) -> List[ValidationIssue]:
        """Validate medallion layer-specific requirements"""
        issues = []
        
        if layer == "bronze":
            # Bronze should have ingestion metadata
            metadata_patterns = ['_ingestion_', 'ingestion_timestamp', 'add_ingestion_metadata']
            
            if not any(pattern in code for pattern in metadata_patterns):
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    check_name="bronze_metadata",
                    message="Bronze layer missing ingestion metadata columns",
                    suggestion="Add _ingestion_timestamp, _ingestion_date, _source_file columns"
                ))
        
        elif layer == "silver":
            # Silver should have data quality checks
            quality_patterns = ['WHERE', 'FILTER', 'dropna', 'isNotNull', 'CASE WHEN']
            
            if not any(pattern in code for pattern in quality_patterns):
                issues.append(ValidationIssue(
                    level=ValidationLevel.INFO,
                    check_name="silver_quality",
                    message="Silver layer may benefit from data quality filters",
                    suggestion="Consider adding WHERE clauses or filter() for data quality"
                ))
        
        elif layer == "gold":
            # Gold should have business logic
            business_patterns = ['JOIN', 'GROUP BY', 'SUM', 'COUNT', 'AVG', 'fact_', 'dim_']
            
            if not any(pattern in code for pattern in business_patterns):
                issues.append(ValidationIssue(
                    level=ValidationLevel.INFO,
                    check_name="gold_business_logic",
                    message="Gold layer may need aggregations or joins",
                    suggestion="Add GROUP BY, JOIN, or business calculations"
                ))
        
        return issues
    
    
    def _validate_direct_zero_hardcode(
        self,
        code: str,
        tech_type: TechnologyType,
    ) -> List[ValidationIssue]:
        """Enforce strict no-hardcode policy in direct transpilation mode."""
        issues: List[ValidationIssue] = []

        if tech_type not in [TechnologyType.PYSPARK, TechnologyType.FABRIC, TechnologyType.AWS_GLUE]:
            return issues

        line_checks = [
            (r'^\s*(CATALOG|SCHEMA_[A-Z0-9_]+|BRONZE_PATH|SILVER_PATH|GOLD_PATH)\s*=\s*["\"][^"\"]+["\"]', "hardcoded_constant"),
            (r'^\s*[A-Za-z_][A-Za-z0-9_]*(?:catalog|schema|table|table_name|path|object_name|source_name|target_name)\s*=\s*["\"][^"\"]+["\"]', "hardcoded_helper_assignment"),
            (r'\b(hive_metastore\.|main\.|bronze_raw\.|silver_curated\.|gold_business\.)', "hardcoded_table_reference"),
            (r'["\"](?:/mnt/|abfss://|s3://|gs://)[^"\"]*["\"]', "hardcoded_storage_path"),
            (r'\bsaveAsTable\(\s*["\"][^"\"]+["\"]\s*\)', "hardcoded_saveastable"),
            (r'\b(?:config|cfg)\.get\(\s*["\"][^"\"]*(?:catalog|schema|table|path|object|source|target)[^"\"]*["\"]\s*,\s*["\"][^"\"]+["\"]\s*\)', "hardcoded_config_default"),
        ]

        bad_lines: List[str] = []
        for raw_line in code.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            # Allow dynamic config-based resolution in direct mode, but not invented literal defaults.
            if (
                ("config.get(" in line or "cfg.get(" in line)
                and not re.search(r'\b(?:config|cfg)\.get\(\s*["\"][^"\"]*(?:catalog|schema|table|path|object|source|target)[^"\"]*["\"]\s*,\s*["\"][^"\"]+["\"]\s*\)', line)
            ):
                continue

            for pattern, _ in line_checks:
                if re.search(pattern, line):
                    bad_lines.append(line)
                    break

        if bad_lines:
            preview = "; ".join(bad_lines[:3])
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                check_name="direct_no_hardcode",
                message=f"Hardcoded values detected in direct mode: {preview}",
                suggestion="Replace literals with config.get(...) and metadata-driven values.",
            ))

        return issues

    def _validate_placeholders(self, code: str) -> List[ValidationIssue]:
        """Detect unresolved placeholders like {variable} or {{variable}} in code"""
        issues = []
        
        # In PySpark and Python, f"{variable}" is perfectly valid syntax.
        # We only want to catch specific template placeholders that the LLM forgot to resolve.
        # Typical unresolved placeholders hallucinated by LLM based on system prompt:
        known_unresolved = [
            'silver_path', 'gold_path', 'bronze_path',
            'silver_schema', 'gold_schema', 'bronze_schema',
            'layer_schema', 'layer_path', 'layer_prefix',
            'target_table', 'schema', 'table_name'
        ]
        
        # Regex to find all {something} blocks
        patterns = [
            r'\{([a-z_][a-z0-9_]+)\}',          # {variable}
            r'\{\{([a-z_][a-z0-9_]+)\}\}'       # {{variable}}
        ]
        
        found_placeholders = []
        for pattern in patterns:
            for match in re.finditer(pattern, code):
                var_name = match.group(1)
                full_match = match.group(0)
                line = code[:match.start()].splitlines()[-1] if code[:match.start()].splitlines() else ""
                line += code[match.start():].splitlines()[0] if code[match.start():].splitlines() else ""

                # Allow Python f-strings such as f"{silver_schema}.{silver_prefix}table"
                # because those are runtime interpolations, not unresolved template placeholders.
                if re.search(r'\bf["\']', line):
                    continue
                
                # If it's literally one of our known migration template variables, it's a hallucinated placeholder.
                # Otherwise, it might be a valid python f-string variable like f"{df.count()}" or f"{my_var}"
                # We can also check if the placeholder looks like an unresolved path
                if var_name in known_unresolved or "path" in var_name or "schema" in var_name:
                    # Let's ensure it's not a valid f-string by checking if we really wanted to emit it.
                    # Since these are exact names from our system prompt, it's highly likely to be a hallucinated placeholder.
                    found_placeholders.append(full_match)
        
        if found_placeholders:
            unique_placeholders = list(set(found_placeholders))
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                check_name="unresolved_placeholders",
                message=f"Unresolved placeholders detected in code: {', '.join(unique_placeholders)}",
                suggestion="The code contains literal placeholders that should have been resolved. Ensure you are replacing these with actual values from the project context, not outputting them literally."
            ))
            
        return issues
    
    
    def _get_tech_type(self, tech_id: str) -> TechnologyType:
        """Map tech_id string to TechnologyType enum"""
        tech_map = {
            'pyspark': TechnologyType.PYSPARK,
            'snowflake': TechnologyType.SNOWFLAKE,
            'fabric': TechnologyType.FABRIC,
            'dbt': TechnologyType.DBT,
            'aws': TechnologyType.AWS_GLUE,
            'gcp': TechnologyType.GCP_BIGQUERY,
            'generic': TechnologyType.GENERIC,
            'salesforce': TechnologyType.SALESFORCE
        }
        
        return tech_map.get(tech_id.lower(), TechnologyType.GENERIC)
    
    
    def _build_result(
        self,
        tech_id: str,
        layer: str,
        issues: List[ValidationIssue]
    ) -> ValidationResult:
        """Build final ValidationResult from issues"""
        errors_count = sum(1 for issue in issues if issue.level == ValidationLevel.ERROR)
        warnings_count = sum(1 for issue in issues if issue.level == ValidationLevel.WARNING)
        info_count = sum(1 for issue in issues if issue.level == ValidationLevel.INFO)
        
        is_valid = (errors_count == 0)
        
        return ValidationResult(
            is_valid=is_valid,
            tech_id=tech_id,
            layer=layer,
            issues=issues,
            errors_count=errors_count,
            warnings_count=warnings_count,
            info_count=info_count
        )

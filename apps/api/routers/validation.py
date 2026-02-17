"""
Validation API Endpoints - Sprint 8
====================================

Purpose:
    REST API endpoints for real-time code validation and test generation.
    Allows manual validation of code snippets and retrieval of validation history.

Endpoints:
    POST /api/v1/validation/python - Validate Python code
    POST /api/v1/validation/sql - Validate SQL code
    POST /api/v1/validation/generate-tests - Generate test cases
    GET /api/v1/validation/history/{project_id} - Validation history
    GET /api/v1/validation/stats/{project_id} - Validation statistics

Integration:
    - Used by Agent C for real-time validation
    - Used by frontend for manual code validation
    - Results stored in utm_code_validations table

Author: Legacy2Lake Engineering
Date: 2026-02-11 (Sprint 8)
Version: v1.0
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    from apps.api.services.validation_service import ValidationService, ValidationLevel
    from apps.api.services.test_generator_service import TestGeneratorService
    from apps.api.services.persistence_service import SupabasePersistence
    from apps.api.utils.logger import logger
except ImportError:
    from services.validation_service import ValidationService, ValidationLevel
    from services.test_generator_service import TestGeneratorService
    from services.persistence_service import SupabasePersistence
    from utils.logger import logger


# ================================================================
# ROUTER INITIALIZATION
# ================================================================

router = APIRouter(
    prefix="/api/v1/validation",
    tags=["validation"]
)


# ================================================================
# REQUEST/RESPONSE MODELS
# ================================================================

class ValidateCodeRequest(BaseModel):
    """Request model for code validation"""
    code: str = Field(..., description="Code to validate")
    tech_id: str = Field(..., description="Technology ID (pyspark, snowflake, dbt, etc.)")
    layer: str = Field(default="bronze", description="Medallion layer (bronze, silver, gold)")
    strict_mode: bool = Field(default=True, description="If True, warnings count as errors")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional context (source_table, target_table, etc.)")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "from pyspark.sql import SparkSession\n\nspark = SparkSession.builder.appName('test').getOrCreate()",
                "tech_id": "pyspark",
                "layer": "bronze",
                "strict_mode": False,
                "context": {"source_table": "customers", "target_table": "bronze_customers"}
            }
        }


class ValidationIssueResponse(BaseModel):
    """Individual validation issue"""
    level: str
    check_name: str
    message: str
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    suggestion: Optional[str] = None


class ValidateCodeResponse(BaseModel):
    """Response model for code validation"""
    is_valid: bool
    tech_id: str
    layer: str
    errors_count: int
    warnings_count: int
    info_count: int
    validated_at: str
    issues: List[ValidationIssueResponse]
    llm_feedback: Optional[str] = None


class GenerateTestsRequest(BaseModel):
    """Request model for test case generation"""
    code: str = Field(..., description="Code to generate tests for")
    tech_id: str = Field(..., description="Technology ID (pyspark, snowflake, etc.)")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadata (source_table, target_table, etc.)")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "def transform_customers(df):\n    return df.filter(df.age > 18)",
                "tech_id": "pyspark",
                "metadata": {"source_table": "customers", "target_table": "bronze_customers"}
            }
        }


class GenerateTestsResponse(BaseModel):
    """Response model for test case generation"""
    test_code: str
    test_cases_count: int
    tech_id: str
    generated_at: str


class ValidationHistoryItem(BaseModel):
    """Validation history item"""
    validation_id: str
    project_id: str
    task_id: Optional[str]
    tech_id: str
    layer: str
    is_valid: bool
    errors_count: int
    warnings_count: int
    validated_at: str


class ValidationStatsResponse(BaseModel):
    """Validation statistics for a project"""
    project_id: str
    total_validations: int
    passed: int
    failed: int
    pass_rate: float
    avg_errors_per_validation: float
    most_common_errors: List[Dict[str, Any]]


# ================================================================
# API ENDPOINTS
# ================================================================

@router.post("/python", response_model=ValidateCodeResponse)
async def validate_python_code(request: ValidateCodeRequest):
    """
    Validate Python code (PySpark, Fabric, AWS Glue, etc.)
    
    Returns validation results with issues, suggestions, and LLM feedback.
    """
    logger.info(f"[API] Validating Python code: tech={request.tech_id}, layer={request.layer}", "ValidationAPI")
    
    try:
        validator = ValidationService()
        
        result = await validator.validate_code(
            code=request.code,
            tech_id=request.tech_id,
            layer=request.layer,
            context=request.context or {}
        )
        
        # Apply strict mode
        if request.strict_mode and result.warnings_count > 0:
            result.is_valid = False
        
        # Convert to response model
        response = ValidateCodeResponse(
            is_valid=result.is_valid,
            tech_id=result.tech_id,
            layer=result.layer,
            errors_count=result.errors_count,
            warnings_count=result.warnings_count,
            info_count=result.info_count,
            validated_at=result.validated_at,
            issues=[
                ValidationIssueResponse(
                    level=issue.level.value,
                    check_name=issue.check_name,
                    message=issue.message,
                    line_number=issue.line_number,
                    column_number=issue.column_number,
                    suggestion=issue.suggestion
                )
                for issue in result.issues
            ],
            llm_feedback=result.get_llm_feedback() if not result.is_valid else None
        )
        
        logger.info(
            f"[API] Validation complete: valid={response.is_valid}, errors={response.errors_count}, warnings={response.warnings_count}",
            "ValidationAPI"
        )
        
        return response
    
    except Exception as e:
        logger.error(f"[API] Validation failed: {e}", "ValidationAPI")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.post("/sql", response_model=ValidateCodeResponse)
async def validate_sql_code(request: ValidateCodeRequest):
    """
    Validate SQL code (Snowflake, DBT, etc.)
    
    Returns validation results with issues and suggestions.
    """
    logger.info(f"[API] Validating SQL code: tech={request.tech_id}, layer={request.layer}", "ValidationAPI")
    
    try:
        validator = ValidationService()
        
        result = await validator.validate_code(
            code=request.code,
            tech_id=request.tech_id,
            layer=request.layer,
            context=request.context or {}
        )
        
        # Apply strict mode
        if request.strict_mode and result.warnings_count > 0:
            result.is_valid = False
        
        # Convert to response model
        response = ValidateCodeResponse(
            is_valid=result.is_valid,
            tech_id=result.tech_id,
            layer=result.layer,
            errors_count=result.errors_count,
            warnings_count=result.warnings_count,
            info_count=result.info_count,
            validated_at=result.validated_at,
            issues=[
                ValidationIssueResponse(
                    level=issue.level.value,
                    check_name=issue.check_name,
                    message=issue.message,
                    line_number=issue.line_number,
                    column_number=issue.column_number,
                    suggestion=issue.suggestion
                )
                for issue in result.issues
            ],
            llm_feedback=result.get_llm_feedback() if not result.is_valid else None
        )
        
        logger.info(
            f"[API] Validation complete: valid={response.is_valid}, errors={response.errors_count}, warnings={response.warnings_count}",
            "ValidationAPI"
        )
        
        return response
    
    except Exception as e:
        logger.error(f"[API] Validation failed: {e}", "ValidationAPI")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.post("/generate-tests", response_model=GenerateTestsResponse)
async def generate_test_cases(request: GenerateTestsRequest):
    """
    Generate pytest test cases from code
    
    Returns pytest-compatible test code with fixtures and test cases.
    """
    logger.info(f"[API] Generating test cases: tech={request.tech_id}", "ValidationAPI")
    
    try:
        test_generator = TestGeneratorService()
        
        test_code = await test_generator.generate_tests(
            code=request.code,
            tech_id=request.tech_id,
            metadata=request.metadata or {}
        )
        
        # Count test cases in generated code
        test_cases_count = test_code.count("def test_")
        
        response = GenerateTestsResponse(
            test_code=test_code,
            test_cases_count=test_cases_count,
            tech_id=request.tech_id,
            generated_at=datetime.utcnow().isoformat()
        )
        
        logger.info(f"[API] Test generation complete: {test_cases_count} test cases generated", "ValidationAPI")
        
        return response
    
    except Exception as e:
        logger.error(f"[API] Test generation failed: {e}", "ValidationAPI")
        raise HTTPException(status_code=500, detail=f"Test generation failed: {str(e)}")


@router.get("/history/{project_id}", response_model=List[ValidationHistoryItem])
async def get_validation_history(
    project_id: str,
    limit: int = 50,
    offset: int = 0
):
    """
    Get validation history for a project
    
    Returns paginated list of validation results.
    """
    logger.info(f"[API] Fetching validation history: project_id={project_id}, limit={limit}, offset={offset}", "ValidationAPI")
    
    try:
        # TODO: Query utm_code_validations table
        # For now, return empty list (table will be created in migration)
        
        logger.warning(f"[API] utm_code_validations table not yet created, returning empty history", "ValidationAPI")
        
        return []
    
    except Exception as e:
        logger.error(f"[API] Failed to fetch validation history: {e}", "ValidationAPI")
        raise HTTPException(status_code=500, detail=f"Failed to fetch validation history: {str(e)}")


@router.get("/stats/{project_id}", response_model=ValidationStatsResponse)
async def get_validation_stats(project_id: str):
    """
    Get validation statistics for a project
    
    Returns aggregated validation metrics (pass rate, common errors, etc.)
    """
    logger.info(f"[API] Fetching validation stats: project_id={project_id}", "ValidationAPI")
    
    try:
        # TODO: Query utm_code_validations table and aggregate
        # For now, return mock stats
        
        logger.warning(f"[API] utm_code_validations table not yet created, returning mock stats", "ValidationAPI")
        
        return ValidationStatsResponse(
            project_id=project_id,
            total_validations=0,
            passed=0,
            failed=0,
            pass_rate=0.0,
            avg_errors_per_validation=0.0,
            most_common_errors=[]
        )
    
    except Exception as e:
        logger.error(f"[API] Failed to fetch validation stats: {e}", "ValidationAPI")
        raise HTTPException(status_code=500, detail=f"Failed to fetch validation stats: {str(e)}")

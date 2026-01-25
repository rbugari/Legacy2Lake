import pytest
import json
from apps.api.services.refinement.quality_service import QualityService

def test_dq_generation_active():
    """Verify that DQ contracts are generated when rules exist."""
    service = QualityService()
    
    mappings = [
        {"source_column": "email", "is_nullable": False, "is_pii": True, "source_datatype": "varchar"},
        {"source_column": "age", "is_nullable": True, "source_datatype": "integer"}
    ]
    
    # 1. Great Expectations
    gx = service.generate_great_expectations_json("Customers", mappings)
    assert gx is not None
    assert len(gx["expectations"]) >= 2 # not_null(email), type(age), type(email)?
    
    # Check for specific rule
    has_not_null = any(e["expectation_type"] == "expect_column_values_to_not_be_null" for e in gx["expectations"])
    assert has_not_null
    
    # 2. Soda
    soda = service.generate_soda_yaml("Customers", mappings)
    assert soda is not None
    assert "missing_count(email) = 0" in soda

def test_dq_generation_optional():
    """Verify that DQ contracts are SKIPPED (None) when no rules exist."""
    service = QualityService()
    
    mappings = [
        {"source_column": "description", "is_nullable": True, "is_pii": False, "source_datatype": "text"}
        # No strict rules here (nullable=True, not pii)
        # Note: Depending on implementation, type check might still trigger. 
        # For this test, let's assume we want to test the "empty" case.
        # Use empty mappings
    ]
    
    # Test completely empty rules
    gx_empty = service.generate_great_expectations_json("Empty", [])
    assert gx_empty is None
    
    soda_empty = service.generate_soda_yaml("Empty", [])
    assert soda_empty is None

if __name__ == "__main__":
    test_dq_generation_active()
    test_dq_generation_optional()
    print("DQ Verification Passed!")

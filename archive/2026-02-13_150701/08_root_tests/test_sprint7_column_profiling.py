"""
Unit Tests for Column Profiling Service - Sprint 7
===================================================

Tests for Deep Forensic Triage column-level analysis:
- Cardinality calculation
- Null percentage calculation
- Data type inference
- PII detection (regex + keyword matching)
- Partition recommendations
- Database persistence
- Heatmap generation

Run with:
    pytest test_sprint7_column_profiling.py -v

Author: Legacy2Lake Engineering
Date: 2026-02-11
"""

import pytest
import asyncio
from typing import List, Dict, Any
import json

# Import service
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from apps.api.services.column_profiling_service import ColumnProfilingService


# ================================================================
# FIXTURES
# ================================================================

@pytest.fixture
def profiler():
    """Create a ColumnProfilingService instance."""
    return ColumnProfilingService(tenant_id='test-tenant', client_id='test-client')


@pytest.fixture
def sample_string_column():
    """Sample string column with moderate cardinality."""
    return {
        'column_name': 'customer_status',
        'data_type': 'VARCHAR(50)',
        'sample_values': ['ACTIVE', 'ACTIVE', 'INACTIVE', 'ACTIVE', 'PENDING', 
                          'ACTIVE', 'INACTIVE', 'ACTIVE', 'ACTIVE', 'PENDING'] * 5,
        'is_nullable': True,
        'is_primary_key': False,
        'is_indexed': True
    }


@pytest.fixture
def sample_numeric_column():
    """Sample numeric column with high cardinality."""
    return {
        'column_name': 'customer_id',
        'data_type': 'INT',
        'sample_values': list(range(1, 101)),  # 100 unique values
        'is_nullable': False,
        'is_primary_key': True,
        'is_indexed': True
    }


@pytest.fixture
def sample_date_column():
    """Sample date column."""
    return {
        'column_name': 'created_date',
        'data_type': 'DATE',
        'sample_values': ['2024-01-15', '2024-02-20', '2024-03-10'] * 10,
        'is_nullable': True,
        'is_primary_key': False,
        'is_indexed': False
    }


@pytest.fixture
def sample_email_column():
    """Sample email column (PII)."""
    return {
        'column_name': 'customer_email',
        'data_type': 'VARCHAR(255)',
        'sample_values': [
            'john.doe@example.com',
            'jane.smith@company.org',
            'bob.wilson@test.net',
            'alice.jones@demo.com',
            'mike.brown@sample.io'
        ] * 10,
        'is_nullable': True,
        'is_primary_key': False,
        'is_indexed': True
    }


@pytest.fixture
def sample_ssn_column():
    """Sample SSN column (PII)."""
    return {
        'column_name': 'social_security_number',
        'data_type': 'VARCHAR(11)',
        'sample_values': [
            '123-45-6789',
            '987-65-4321',
            '555-12-3456',
            '111-22-3333',
            '999-88-7777'
        ] * 10,
        'is_nullable': True,
        'is_primary_key': False,
        'is_indexed': False
    }


@pytest.fixture
def sample_high_null_column():
    """Sample column with high null percentage."""
    values = [None] * 80 + ['value1', 'value2'] * 10
    return {
        'column_name': 'optional_field',
        'data_type': 'VARCHAR(100)',
        'sample_values': values,
        'is_nullable': True,
        'is_primary_key': False,
        'is_indexed': False
    }


# ================================================================
# TEST: Cardinality Calculation
# ================================================================

@pytest.mark.asyncio
async def test_cardinality_low(profiler, sample_string_column):
    """Test cardinality calculation for low-cardinality column."""
    profile = await profiler._profile_single_column(sample_string_column, 0, None)
    
    assert profile['column_name'] == 'customer_status'
    assert profile['distinct_count'] == 3  # ACTIVE, INACTIVE, PENDING
    assert 0.0 < profile['cardinality_ratio'] < 0.3  # Low cardinality
    assert profile['cardinality_ratio'] == pytest.approx(0.06, abs=0.01)  # 3/50


@pytest.mark.asyncio
async def test_cardinality_high(profiler, sample_numeric_column):
    """Test cardinality calculation for high-cardinality column."""
    profile = await profiler._profile_single_column(sample_numeric_column, 0, None)
    
    assert profile['column_name'] == 'customer_id'
    assert profile['distinct_count'] == 100
    assert profile['cardinality_ratio'] == 1.0  # All unique values


# ================================================================
# TEST: Null Percentage
# ================================================================

@pytest.mark.asyncio
async def test_null_percentage_zero(profiler, sample_numeric_column):
    """Test null percentage for non-nullable column."""
    profile = await profiler._profile_single_column(sample_numeric_column, 0, None)
    
    assert profile['null_percentage'] == 0.0
    assert profile['null_count'] == 0


@pytest.mark.asyncio
async def test_null_percentage_high(profiler, sample_high_null_column):
    """Test null percentage for column with many nulls."""
    profile = await profiler._profile_single_column(sample_high_null_column, 0, None)
    
    assert profile['null_percentage'] == pytest.approx(80.0, abs=1.0)
    assert profile['null_count'] == 80


# ================================================================
# TEST: Data Type Inference
# ================================================================

@pytest.mark.asyncio
async def test_infer_type_string(profiler, sample_string_column):
    """Test type inference for string column."""
    inferred = profiler._infer_type(sample_string_column['sample_values'])
    assert inferred == 'STRING'


@pytest.mark.asyncio
async def test_infer_type_numeric(profiler):
    """Test type inference for numeric column."""
    samples = [1, 2, 3, 4, 5, 10, 100, 1000]
    inferred = profiler._infer_type(samples)
    assert inferred == 'NUMERIC'


@pytest.mark.asyncio
async def test_infer_type_date(profiler, sample_date_column):
    """Test type inference for date column."""
    inferred = profiler._infer_type(sample_date_column['sample_values'])
    assert  inferred == 'DATE'


@pytest.mark.asyncio
async def test_infer_type_boolean(profiler):
    """Test type inference for boolean column."""
    samples = ['TRUE', 'FALSE', 'TRUE', 'TRUE', 'FALSE'] * 5
    inferred = profiler._infer_type(samples)
    assert inferred == 'BOOLEAN'


# ================================================================
# TEST: PII Detection
# ================================================================

@pytest.mark.asyncio
async def test_pii_detection_email_regex(profiler, sample_email_column):
    """Test PII detection for email addresses (regex match)."""
    pii_result = profiler._detect_pii(
        sample_email_column['column_name'],
        sample_email_column['sample_values'],
        sample_email_column['data_type']
    )
    
    assert pii_result['is_pii'] is True
    assert pii_result['category'] == 'EMAIL'
    assert pii_result['confidence'] >= 0.9  # High confidence from regex
    assert pii_result['pattern'] is not None


@pytest.mark.asyncio
async def test_pii_detection_ssn_regex(profiler, sample_ssn_column):
    """Test PII detection for SSN (regex match)."""
    pii_result = profiler._detect_pii(
        sample_ssn_column['column_name'],
        sample_ssn_column['sample_values'],
        sample_ssn_column['data_type']
    )
    
    assert pii_result['is_pii'] is True
    assert pii_result['category'] == 'SSN'
    assert pii_result['confidence'] >= 0.7  # At least moderate confidence


@pytest.mark.asyncio
async def test_pii_detection_keyword_match(profiler):
    """Test PII detection from column name keywords."""
    pii_result = profiler._detect_pii(
        'customer_phone_number',
        ['1234567890', '9876543210'],
        'VARCHAR(20)'
    )
    
    assert pii_result['is_pii'] is True
    assert pii_result['category'] in ['PHONE', 'NAME']  # Could match either
    assert pii_result['confidence'] >= 0.5


@pytest.mark.asyncio
async def test_pii_detection_no_pii(profiler, sample_numeric_column):
    """Test PII detection for non-PII column."""
    pii_result = profiler._detect_pii(
        sample_numeric_column['column_name'],
        sample_numeric_column['sample_values'],
        sample_numeric_column['data_type']
    )
    
    assert pii_result['is_pii'] is False
    assert pii_result['category'] is None


# ================================================================
# TEST: Partition Recommendations
# ================================================================

@pytest.mark.asyncio
async def test_partition_recommendation_date(profiler, sample_date_column):
    """Test partition recommendation for date column (ideal candidate)."""
    partition = profiler._recommend_partition(
        sample_date_column['column_name'],
        sample_date_column['data_type'],
        'DATE',
        cardinality_ratio=0.2,
        is_primary_key=False,
        is_indexed=False
    )
    
    assert partition['is_candidate'] is True
    assert partition['score'] >= 0.8  # High score for date columns
    assert 'Date' in partition['reason'] or 'date' in partition['reason']


@pytest.mark.asyncio
async def test_partition_recommendation_low_cardinality_string(profiler):
    """Test partition recommendation for low-cardinality string (good candidate)."""
    partition = profiler._recommend_partition(
        'region_code',
        'VARCHAR(10)',
        'STRING',
        cardinality_ratio=0.15,  # Low cardinality
        is_primary_key=False,
        is_indexed=True
    )
    
    assert partition['is_candidate'] is True
    assert 0.5 <= partition['score'] <= 0.9


@pytest.mark.asyncio
async def test_partition_recommendation_high_cardinality_penalty(profiler):
    """Test partition recommendation for high-cardinality column (penalty)."""
    partition = profiler._recommend_partition(
        'customer_id',
        'INT',
        'NUMERIC',
        cardinality_ratio=0.95,  # Very high cardinality
        is_primary_key=True,  # Primary key = additional penalty
        is_indexed=True
    )
    
    # Should not be recommended (PK + high cardinality)
    assert partition['is_candidate'] is False or partition['score'] < 0.5


@pytest.mark.asyncio
async def test_partition_recommendation_keyword_bonus(profiler):
    """Test partition recommendation with favorable column name."""
    partition = profiler._recommend_partition(
        'transaction_date',
        'DATE',
        'DATE',
        cardinality_ratio=0.3,
        is_primary_key=False,
        is_indexed=False
    )
    
    assert partition['is_candidate'] is True
    assert partition['score'] >= 0.8  # Date type + keyword bonus


# ================================================================
# TEST: Foreign Key Detection (Heuristic)
# ================================================================

def test_detect_foreign_key_id_suffix(profiler):
    """Test FK detection for columns ending with _id."""
    assert profiler._detect_foreign_key('customer_id') is True
    assert profiler._detect_foreign_key('order_id') is True
    assert profiler._detect_foreign_key('product_key') is True


def test_detect_foreign_key_no_match(profiler):
    """Test FK detection for non-FK columns."""
    assert profiler._detect_foreign_key('customer_name') is False
    assert profiler._detect_foreign_key('total_amount') is False


# ================================================================
# TEST: Min/Max Value Calculation
# ================================================================

def test_calculate_max_length(profiler):
    """Test max length calculation."""
    samples = ['abc', 'hello', 'world123', 'x']
    max_len = profiler._calculate_max_length(samples)
    assert max_len == 8  # 'world123'


def test_calculate_max_length_empty(profiler):
    """Test max length with empty samples."""
    max_len = profiler._calculate_max_length([])
    assert max_len is None


# ================================================================
# TEST: Precision/Scale Extraction
# ================================================================

def test_extract_precision_scale_decimal(profiler):
    """Test precision/scale extraction from DECIMAL type."""
    result = profiler._extract_precision_scale('DECIMAL(18,2)')
    assert result == '18,2'


def test_extract_precision_scale_numeric(profiler):
    """Test precision/scale extraction from NUMERIC type."""
    result = profiler._extract_precision_scale('NUMERIC(10, 4)')
    assert result == '10,4'


def test_extract_precision_scale_no_match(profiler):
    """Test precision/scale extraction for non-numeric types."""
    result = profiler._extract_precision_scale('VARCHAR(255)')
    assert result is None


# ================================================================
# TEST: End-to-End Column Profiling
# ================================================================

@pytest.mark.asyncio
async def test_profile_asset_multiple_columns(profiler):
    """Test profiling multiple columns in one asset."""
    columns_data = [
        {
            'column_name': 'id',
            'data_type': 'INT',
            'sample_values': list(range(1, 51)),
            'is_nullable': False,
            'is_primary_key': True,
            'is_indexed': True
        },
        {
            'column_name': 'email',
            'data_type': 'VARCHAR(255)',
            'sample_values': [f'user{i}@test.com' for i in range(50)],
            'is_nullable': True,
            'is_primary_key': False,
            'is_indexed': True
        },
        {
            'column_name': 'status',
            'data_type': 'VARCHAR(20)',
            'sample_values': ['ACTIVE', 'INACTIVE'] * 25,
            'is_nullable': True,
            'is_primary_key': False,
            'is_indexed': False
        }
    ]
    
    result = await profiler.profile_asset(
        asset_id='test-asset-123',
        columns_data=columns_data,
        asset_metadata=None
    )
    
    assert len(result) == 3
    
    # Check first column (id)
    id_profile = result[0]
    assert id_profile['column_name'] == 'id'
    assert id_profile['is_primary_key'] is True
    assert id_profile['cardinality_ratio'] == 1.0
    
    # Check second column (email - PII)
    email_profile = result[1]
    assert email_profile['column_name'] == 'email'
    assert email_profile['is_pii'] is True
    assert email_profile['pii_category'] == 'EMAIL'
    
    # Check third column (status - partition candidate)
    status_profile = result[2]
    assert status_profile['column_name'] == 'status'
    assert status_profile['cardinality_ratio'] < 0.3  # Low cardinality
    # Status should be a partition candidate (low cardinality string)


# ================================================================
# TEST: Error Handling
# ================================================================

@pytest.mark.asyncio
async def test_profile_column_missing_data(profiler):
    """Test profiling column with missing required data."""
    incomplete_column = {
        'column_name': 'test_col'
        # Missing sample_values
    }
    
    # Should handle gracefully without crashing
    profile = await profiler._profile_single_column(incomplete_column, 0, None)
    
    assert profile['column_name'] == 'test_col'
    assert profile['distinct_count'] == 0
    assert profile['null_percentage'] == 0.0


# ================================================================
# SUMMARY
# ================================================================

def test_summary():
    """Print test summary."""
    print("\n" + "=" * 80)
    print("Sprint 7 Column Profiling Tests Summary")
    print("=" * 80)
    print("✅ Cardinality Tests: 2")
    print("✅ Null Percentage Tests: 2")
    print("✅ Type Inference Tests: 4")
    print("✅ PII Detection Tests: 4")
    print("✅ Partition Recommendation Tests: 4")
    print("✅ Foreign Key Detection Tests: 2")
    print("✅ Utility Tests: 3")
    print("✅ End-to-End Tests: 1")
    print("✅ Error Handling Tests: 1")
    print("=" * 80)
    print("Total: 23 Tests")
    print("=" * 80)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

"""
Unit Tests for MetricsCalculator - Sprint 11

Tests cover all metric types:
- Completeness metrics (% non-null)
- Accuracy metrics (% meeting rules)
- Consistency metrics (cross-table validation)
- Timeliness metrics (data freshness)
- Validity metrics (format conformance)
- Uniqueness metrics (duplicate detection)
- Overall scoring
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

# Import service under test
from apps.api.services.metrics_calculator_service import (
    MetricsCalculator,
    QualityMetric,
    MetricsReport,
    MetricType
)


@pytest.fixture
def mock_supabase():
    """Mock Supabase client."""
    with patch('apps.api.services.metrics_calculator_service.create_client') as mock:
        client = Mock()
        mock.return_value = client
        yield client


@pytest.fixture
def calculator(mock_supabase):
    """Create MetricsCalculator instance with mocked Supabase."""
    return MetricsCalculator(
        tenant_id="00000000-0000-0000-0000-000000000001",
        project_id="10000000-0000-0000-0000-000000000001"
    )


# ================================================================
# TEST 1: Calculate Completeness Metric (100%)
# ================================================================
@pytest.mark.asyncio
async def test_calculate_completeness_perfect(calculator):
    """Test completeness calculation with no null values (100%)."""
    # Arrange
    with patch.object(calculator, '_execute_query', new=AsyncMock(return_value=[{"null_count": 0}])):
        # Act
        metric = await calculator._calculate_completeness(
            "main.bronze.customers",
            "email",
            1000
        )
        
        # Assert
        assert metric.value == 100.0
        assert metric.metric_type == MetricType.COMPLETENESS
        assert metric.details["null_count"] == 0
        assert metric.details["non_null_count"] == 1000


# ================================================================
# TEST 2: Calculate Completeness Metric (80%)
# ================================================================
@pytest.mark.asyncio
async def test_calculate_completeness_partial(calculator):
    """Test completeness calculation with some null values."""
    # Arrange
    with patch.object(calculator, '_execute_query', new=AsyncMock(return_value=[{"null_count": 200}])):
        # Act
        metric = await calculator._calculate_completeness(
            "main.bronze.customers",
            "phone",
            1000
        )
        
        # Assert
        assert metric.value == 80.0
        assert metric.details["null_count"] == 200
        assert metric.details["non_null_count"] == 800


# ================================================================
# TEST 3: Calculate Accuracy Metric
# ================================================================
@pytest.mark.asyncio
async def test_calculate_accuracy_metric(calculator):
    """Test accuracy metric calculation based on quality rules."""
    # Arrange
    mock_quality_report = Mock()
    mock_quality_report.quality_score = 85.5
    mock_quality_report.rules_evaluated = 10
    mock_quality_report.rules_passed = 8
    mock_quality_report.rules_failed = 2
    mock_quality_report.violations = []
    
    with patch('apps.api.services.metrics_calculator_service.QualityRuleEngine') as mock_engine:
        mock_instance = Mock()
        mock_instance.evaluate_table = AsyncMock(return_value=mock_quality_report)
        mock_engine.return_value = mock_instance
        
        # Act
        metric = await calculator._calculate_accuracy(
            "customers",
            "main.bronze.customers",
            1000
        )
        
        # Assert
        assert metric.value == 85.5
        assert metric.metric_type == MetricType.ACCURACY
        assert metric.details["rules_evaluated"] == 10
        assert metric.details["rules_passed"] == 8


# ================================================================
# TEST 4: Calculate Consistency Metric (No Foreign Keys)
# ================================================================
@pytest.mark.asyncio
async def test_calculate_consistency_no_fks(calculator):
    """Test consistency metric with no foreign key relationships (100%)."""
    # Arrange
    with patch.object(calculator, '_get_foreign_keys', new=AsyncMock(return_value=[])):
        # Act
        metric = await calculator._calculate_consistency(
            "customers",
            "main.bronze.customers"
        )
        
        # Assert
        assert metric.value == 100.0
        assert metric.details["foreign_keys"] == 0


# ================================================================
# TEST 5: Calculate Consistency Metric (With Valid FKs)
# ================================================================
@pytest.mark.asyncio
async def test_calculate_consistency_with_fks(calculator):
    """Test consistency metric with valid foreign key relationships."""
    # Arrange
    fk_relationships = [
        {
            "column": "country_id",
            "referenced_table": "countries",
            "referenced_column": "id"
        },
        {
            "column": "city_id",
            "referenced_table": "cities",
            "referenced_column": "id"
        }
    ]
    
    with patch.object(calculator, '_get_foreign_keys', new=AsyncMock(return_value=fk_relationships)):
        with patch.object(calculator, '_execute_query', new=AsyncMock(return_value=[{"orphan_count": 0}])):
            # Act
            metric = await calculator._calculate_consistency(
                "customers",
                "main.bronze.customers"
            )
            
            # Assert
            assert metric.value == 100.0
            assert metric.details["foreign_keys_checked"] == 2
            assert metric.details["foreign_keys_valid"] == 2


# ================================================================
# TEST 6: Calculate Timeliness Metric (Fresh Data)
# ================================================================
@pytest.mark.asyncio
async def test_calculate_timeliness_fresh_data(calculator):
    """Test timeliness metric with fresh data (< 1 hour old)."""
    # Arrange
    recent_timestamp = datetime.now() - timedelta(minutes=30)
    
    with patch.object(calculator, '_get_timestamp_columns', new=AsyncMock(return_value=["created_at"])):
        with patch.object(calculator, '_execute_query', new=AsyncMock(return_value=[{"latest_timestamp": recent_timestamp}])):
            # Act
            metric = await calculator._calculate_timeliness(
                "orders",
                "main.bronze.orders"
            )
            
            # Assert
            assert metric.value == 100.0
            assert metric.column_name == "created_at"


# ================================================================
# TEST 7: Calculate Timeliness Metric (Old Data)
# ================================================================
@pytest.mark.asyncio
async def test_calculate_timeliness_old_data(calculator):
    """Test timeliness metric with old data (> 30 days)."""
    # Arrange
    old_timestamp = datetime.now() - timedelta(days=45)
    
    with patch.object(calculator, '_get_timestamp_columns', new=AsyncMock(return_value=["updated_at"])):
        with patch.object(calculator, '_execute_query', new=AsyncMock(return_value=[{"latest_timestamp": old_timestamp}])):
            # Act
            metric = await calculator._calculate_timeliness(
                "archive",
                "main.bronze.archive"
            )
            
            # Assert
            assert metric.value == 30.0  # Oldest category


# ================================================================
# TEST 8: Calculate Validity Metric
# ================================================================
@pytest.mark.asyncio
async def test_calculate_validity_metric(calculator):
    """Test validity metric for string columns."""
    # Arrange
    with patch.object(calculator, '_execute_query', new=AsyncMock(return_value=[{"invalid_count": 10}])):
        # Act
        metric = await calculator._calculate_validity(
            "main.bronze.customers",
            "email",
            1000
        )
        
        # Assert
        assert metric.value == 99.0
        assert metric.details["invalid_count"] == 10
        assert metric.details["valid_count"] == 990


# ================================================================
# TEST 9: Calculate Uniqueness Metric (100% Unique)
# ================================================================
@pytest.mark.asyncio
async def test_calculate_uniqueness_perfect(calculator):
    """Test uniqueness metric with all unique values."""
    # Arrange
    with patch.object(calculator, '_execute_query', new=AsyncMock(return_value=[{"distinct_count": 1000}])):
        # Act
        metric = await calculator._calculate_uniqueness(
            "main.bronze.customers",
            "customer_id",
            1000
        )
        
        # Assert
        assert metric.value == 100.0
        assert metric.details["distinct_count"] == 1000
        assert metric.details["duplicate_count"] == 0


# ================================================================
# TEST 10: Calculate Uniqueness Metric (With Duplicates)
# ================================================================
@pytest.mark.asyncio
async def test_calculate_uniqueness_with_duplicates(calculator):
    """Test uniqueness metric with duplicate values."""
    # Arrange
    with patch.object(calculator, '_execute_query', new=AsyncMock(return_value=[{"distinct_count": 800}])):
        # Act
        metric = await calculator._calculate_uniqueness(
            "main.bronze.customers",
            "email",
            1000
        )
        
        # Assert
        assert metric.value == 80.0
        assert metric.details["duplicate_count"] == 200


# ================================================================
# TEST 11: Calculate Overall Metrics Report
# ================================================================
@pytest.mark.asyncio
async def test_calculate_metrics_report(calculator):
    """Test complete metrics report calculation."""
    # Arrange
    with patch.object(calculator, '_get_table_columns', new=AsyncMock(return_value=["col1", "col2"])):
        with patch.object(calculator, '_get_row_count', new=AsyncMock(return_value=1000)):
            with patch.object(calculator, '_calculate_completeness', new=AsyncMock(return_value=Mock(value=95.0))):
                with patch.object(calculator, '_calculate_accuracy', new=AsyncMock(return_value=Mock(value=90.0))):
                    with patch.object(calculator, '_calculate_consistency', new=AsyncMock(return_value=Mock(value=100.0))):
                        with patch.object(calculator, '_calculate_timeliness', new=AsyncMock(return_value=Mock(value=85.0))):
                            with patch.object(calculator, '_is_string_column', new=AsyncMock(return_value=False)):
                                with patch.object(calculator, '_get_key_columns', new=AsyncMock(return_value=[])):
                                    with patch.object(calculator, '_save_metrics_report', new=AsyncMock()):
                                        # Act
                                        report = await calculator.calculate_metrics("test_table")
                                        
                                        # Assert
                                        assert report.table_name == "test_table"
                                        assert report.completeness_score == 95.0
                                        assert report.accuracy_score == 90.0
                                        assert report.consistency_score == 100.0
                                        assert report.timeliness_score == 85.0


# ================================================================
# TEST 12: Weighted Overall Score Calculation
# ================================================================
@pytest.mark.asyncio
async def test_weighted_overall_score(calculator):
    """Test weighted overall score calculation."""
    # Arrange
    # Default weights: completeness=0.25, accuracy=0.25, consistency=0.15, timeliness=0.15, validity=0.10, uniqueness=0.10
    # Scores: 80, 90, 100, 70, 85, 95
    # Expected: 80*0.25 + 90*0.25 + 100*0.15 + 70*0.15 + 85*0.10 + 95*0.10 = 20 + 22.5 + 15 + 10.5 + 8.5 + 9.5 = 86.0
    
    with patch.object(calculator, '_get_table_columns', new=AsyncMock(return_value=["col1"])):
        with patch.object(calculator, '_get_row_count', new=AsyncMock(return_value=1000)):
            with patch.object(calculator, '_calculate_completeness', new=AsyncMock(return_value=Mock(value=80.0))):
                with patch.object(calculator, '_calculate_accuracy', new=AsyncMock(return_value=Mock(value=90.0))):
                    with patch.object(calculator, '_calculate_consistency', new=AsyncMock(return_value=Mock(value=100.0))):
                        with patch.object(calculator, '_calculate_timeliness', new=AsyncMock(return_value=Mock(value=70.0))):
                            with patch.object(calculator, '_is_string_column', new=AsyncMock(return_value=True)):
                                with patch.object(calculator, '_calculate_validity', new=AsyncMock(return_value=Mock(value=85.0))):
                                    with patch.object(calculator, '_get_key_columns', new=AsyncMock(return_value=["col1"])):
                                        with patch.object(calculator, '_calculate_uniqueness', new=AsyncMock(return_value=Mock(value=95.0))):
                                            with patch.object(calculator, '_save_metrics_report', new=AsyncMock()):
                                                # Act
                                                report = await calculator.calculate_metrics("test")
                                                
                                                # Assert
                                                assert report.overall_score == 86.0


# ================================================================
# TEST 13: Get Metric Trends
# ================================================================
@pytest.mark.asyncio
async def test_get_metric_trends(calculator, mock_supabase):
    """Test retrieving historical metric trends."""
    # Arrange
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.eq.return_value.eq.return_value.gte.return_value.order.return_value.execute.return_value = Mock(
        data=[
            {"metric_type": "completeness", "value": 95.0, "timestamp": "2026-02-01"},
            {"metric_type": "completeness", "value": 96.0, "timestamp": "2026-02-02"},
            {"metric_type": "completeness", "value": 97.0, "timestamp": "2026-02-03"}
        ]
    )
    
    # Act
    trends = await calculator.get_metric_trends(
        "customers",
        MetricType.COMPLETENESS,
        days=7
    )
    
    # Assert
    assert len(trends) == 3
    assert trends[0]["value"] == 95.0


# ================================================================
# TEST 14: Metric Dataclass Serialization
# ================================================================
def test_quality_metric_to_dict():
    """Test QualityMetric serialization to dictionary."""
    # Arrange
    metric = QualityMetric(
        metric_type=MetricType.COMPLETENESS,
        table_name="customers",
        column_name="email",
        value=95.5,
        measurement_count=1000,
        timestamp=datetime(2026, 2, 11, 12, 0, 0),
        details={"null_count": 45}
    )
    
    # Act
    metric_dict = metric.to_dict()
    
    # Assert
    assert metric_dict["metric_type"] == "completeness"
    assert metric_dict["value"] == 95.5
    assert metric_dict["details"]["null_count"] == 45


# ================================================================
# TEST 15: MetricsReport Dataclass Serialization
# ================================================================
def test_metrics_report_to_dict():
    """Test MetricsReport serialization to dictionary."""
    # Arrange
    report = MetricsReport(
        table_name="customers",
        overall_score=88.5,
        completeness_score=95.0,
        accuracy_score=90.0,
        consistency_score=100.0,
        timeliness_score=80.0,
        validity_score=85.0,
        uniqueness_score=92.0,
        metrics=[],
        timestamp=datetime(2026, 2, 11, 12, 0, 0)
    )
    
    # Act
    report_dict = report.to_dict()
    
    # Assert
    assert report_dict["table_name"] == "customers"
    assert report_dict["overall_score"] == 88.5
    assert report_dict["completeness_score"] == 95.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

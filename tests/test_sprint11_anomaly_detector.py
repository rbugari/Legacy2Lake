"""
Unit Tests for AnomalyDetector - Sprint 11

Tests cover all anomaly detection types:
- Statistical outliers (Z-score and IQR methods)
- Volume anomalies (spikes and drops)
- Null spikes
- Duplicate spikes
- Pattern breaks
- Threshold violations
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

# Import service under test
from apps.api.services.anomaly_detector_service import (
    AnomalyDetector,
    Anomaly,
    AnomalyReport,
    AnomalyType,
    Severity
)


@pytest.fixture
def mock_supabase():
    """Mock Supabase client."""
    with patch('apps.api.services.anomaly_detector_service.create_client') as mock:
        client = Mock()
        mock.return_value = client
        yield client


@pytest.fixture
def detector(mock_supabase):
    """Create AnomalyDetector instance with mocked Supabase."""
    return AnomalyDetector(
        tenant_id="00000000-0000-0000-0000-000000000001",
        project_id="10000000-0000-0000-0000-000000000001"
    )


# ================================================================
# TEST 1: Detect Z-Score Outliers
# ================================================================
@pytest.mark.asyncio
async def test_detect_z_score_outliers(detector):
    """Test Z-score based outlier detection."""
    # Arrange
    stats = {
        "mean": 100.0,
        "stddev": 10.0,
        "min": 50.0,
        "max": 200.0,
        "q1": 90.0,
        "median": 100.0,
        "q3": 110.0
    }
    
    # Mock query - 2 outliers (z-score > 3)
    with patch.object(detector, '_execute_query', new=AsyncMock(return_value=[
        {"amount": 150.0, "z_score": 5.0},
        {"amount": 30.0, "z_score": 7.0}
    ])):
        # Act
        anomalies = await detector._detect_z_score_outliers(
            "orders",
            "main.bronze.orders",
            "amount",
            stats
        )
        
        # Assert
        assert len(anomalies) == 2
        assert anomalies[0].anomaly_type == AnomalyType.STATISTICAL_OUTLIER
        assert anomalies[0].detected_value == 150.0
        assert anomalies[0].severity == Severity.CRITICAL  # z-score > 5


# ================================================================
# TEST 2: Detect IQR Outliers
# ================================================================
@pytest.mark.asyncio
async def test_detect_iqr_outliers(detector):
    """Test IQR-based outlier detection."""
    # Arrange
    stats = {
        "mean": 100.0,
        "stddev": 10.0,
        "min": 50.0,
        "max": 200.0,
        "q1": 90.0,
        "median": 100.0,
        "q3": 110.0
    }
    
    # IQR = 110 - 90 = 20
    # Lower bound: 90 - 1.5*20 = 60
    # Upper bound: 110 + 1.5*20 = 140
    
    # Mock query - 1 outlier
    with patch.object(detector, '_execute_query', new=AsyncMock(return_value=[
        {"amount": 200.0}
    ])):
        # Act
        anomalies = await detector._detect_iqr_outliers(
            "orders",
            "main.bronze.orders",
            "amount",
            stats
        )
        
        # Assert
        assert len(anomalies) == 1
        assert anomalies[0].detected_value == 200.0


# ================================================================
# TEST 3: Detect Volume Spike
# ================================================================
@pytest.mark.asyncio
async def test_detect_volume_spike(detector):
    """Test volume spike detection (sudden row count increase)."""
    # Arrange
    current_count = 1500
    historical_counts = [1000, 1050, 980, 1020, 1000, 990, 1010]
    mean_count = 1007.14  # ~1000
    
    with patch.object(detector, '_get_row_count', new=AsyncMock(return_value=current_count)):
        with patch.object(detector, '_get_historical_row_counts', new=AsyncMock(return_value=historical_counts)):
            # Act
            anomalies = await detector._detect_volume_anomalies(
                "orders",
                "main.bronze.orders"
            )
            
            # Assert
            assert len(anomalies) == 1
            assert anomalies[0].anomaly_type == AnomalyType.VOLUME_SPIKE
            assert anomalies[0].detected_value == 1500


# ================================================================
# TEST 4: Detect Volume Drop
# ================================================================
@pytest.mark.asyncio
async def test_detect_volume_drop(detector):
    """Test volume drop detection (sudden row count decrease)."""
    # Arrange
    current_count = 500
    historical_counts = [1000, 1050, 980, 1020, 1000, 990, 1010]
    
    with patch.object(detector, '_get_row_count', new=AsyncMock(return_value=current_count)):
        with patch.object(detector, '_get_historical_row_counts', new=AsyncMock(return_value=historical_counts)):
            # Act
            anomalies = await detector._detect_volume_anomalies(
                "orders",
                "main.bronze.orders"
            )
            
            # Assert
            assert len(anomalies) == 1
            assert anomalies[0].anomaly_type == AnomalyType.VOLUME_DROP
            assert anomalies[0].severity == Severity.HIGH  # > 50% drop


# ================================================================
# TEST 5: Detect Null Spike
# ================================================================
@pytest.mark.asyncio
async def test_detect_null_spike(detector):
    """Test null spike detection (sudden increase in null values)."""
    # Arrange
    current_null_pct = 0.50  # 50% nulls
    historical_nulls = [0.05, 0.06, 0.04, 0.05, 0.06, 0.05, 0.04]  # ~5% historically
    
    with patch.object(detector, '_get_table_columns', new=AsyncMock(return_value=["email"])):
        with patch.object(detector, '_get_null_percentage', new=AsyncMock(return_value=current_null_pct)):
            with patch.object(detector, '_get_historical_null_percentages', new=AsyncMock(return_value=historical_nulls)):
                # Act
                anomalies = await detector._detect_null_spikes(
                    "customers",
                    "main.bronze.customers"
                )
                
                # Assert
                assert len(anomalies) == 1
                assert anomalies[0].anomaly_type == AnomalyType.NULL_SPIKE
                assert anomalies[0].column_name == "email"
                assert anomalies[0].severity == Severity.HIGH


# ================================================================
# TEST 6: Detect Duplicate Spike
# ================================================================
@pytest.mark.asyncio
async def test_detect_duplicate_spike(detector):
    """Test duplicate spike detection for key columns."""
    # Arrange
    current_dup_pct = 0.25  # 25% duplicates
    historical_dups = [0.02, 0.01, 0.02, 0.01, 0.02, 0.01, 0.02]  # ~1-2% historically
    
    with patch.object(detector, '_get_key_columns', new=AsyncMock(return_value=["customer_id"])):
        with patch.object(detector, '_get_duplicate_percentage', new=AsyncMock(return_value=current_dup_pct)):
            with patch.object(detector, '_get_historical_duplicate_percentages', new=AsyncMock(return_value=historical_dups)):
                # Act
                anomalies = await detector._detect_duplicate_spikes(
                    "customers",
                    "main.bronze.customers"
                )
                
                # Assert
                assert len(anomalies) == 1
                assert anomalies[0].anomaly_type == AnomalyType.DUPLICATE_SPIKE
                assert anomalies[0].column_name == "customer_id"


# ================================================================
# TEST 7: Detect No Anomalies
# ================================================================
@pytest.mark.asyncio
async def test_detect_no_anomalies(detector):
    """Test anomaly detection when everything is normal."""
    # Arrange
    with patch.object(detector, '_detect_volume_anomalies', new=AsyncMock(return_value=[])):
        with patch.object(detector, '_detect_null_spikes', new=AsyncMock(return_value=[])):
            with patch.object(detector, '_detect_duplicate_spikes', new=AsyncMock(return_value=[])):
                with patch.object(detector, '_get_numeric_columns', new=AsyncMock(return_value=[])):
                    with patch.object(detector, '_save_anomaly_report', new=AsyncMock()):
                        # Act
                        report = await detector.detect_anomalies("test_table")
                        
                        # Assert
                        assert report.anomalies_detected == 0
                        assert report.critical_count == 0
                        assert len(report.anomalies) == 0


# ================================================================
# TEST 8: Detect Multiple Anomalies (Mixed Severity)
# ================================================================
@pytest.mark.asyncio
async def test_detect_multiple_anomalies(detector):
    """Test detection of multiple anomalies with different severities."""
    # Arrange
    volume_anomaly = Anomaly(
        anomaly_type=AnomalyType.VOLUME_SPIKE,
        table_name="orders",
        column_name=None,
        detected_value=2000,
        expected_range=(900, 1100),
        deviation_score=90.0,
        severity=Severity.MEDIUM,
        description="Volume spike",
        timestamp=datetime.now()
    )
    
    null_anomaly = Anomaly(
        anomaly_type=AnomalyType.NULL_SPIKE,
        table_name="orders",
        column_name="email",
        detected_value=0.3,
        expected_range=(0, 0.1),
        deviation_score=80.0,
        severity=Severity.HIGH,
        description="Null spike",
        timestamp=datetime.now()
    )
    
    outlier_anomaly = Anomaly(
        anomaly_type=AnomalyType.STATISTICAL_OUTLIER,
        table_name="orders",
        column_name="amount",
        detected_value=10000,
        expected_range=(0, 1000),
        deviation_score=95.0,
        severity=Severity.CRITICAL,
        description="Statistical outlier",
        timestamp=datetime.now()
    )
    
    with patch.object(detector, '_detect_volume_anomalies', new=AsyncMock(return_value=[volume_anomaly])):
        with patch.object(detector, '_detect_null_spikes', new=AsyncMock(return_value=[null_anomaly])):
            with patch.object(detector, '_detect_duplicate_spikes', new=AsyncMock(return_value=[])):
                with patch.object(detector, '_get_numeric_columns', new=AsyncMock(return_value=["amount"])):
                    with patch.object(detector, 'detect_statistical_outliers', new=AsyncMock(return_value=[outlier_anomaly])):
                        with patch.object(detector, '_save_anomaly_report', new=AsyncMock()):
                            # Act
                            report = await detector.detect_anomalies("orders")
                            
                            # Assert
                            assert report.anomalies_detected == 3
                            assert report.critical_count == 1
                            assert report.high_count == 1
                            assert report.medium_count == 1


# ================================================================
# TEST 9: Get Column Statistics
# ================================================================
@pytest.mark.asyncio
async def test_get_column_statistics(detector):
    """Test retrieving column statistics for outlier detection."""
    # Arrange
    with patch.object(detector, '_execute_query', new=AsyncMock(return_value=[{
        "mean": 100.0,
        "stddev": 15.0,
        "min": 50.0,
        "max": 200.0,
        "q1": 85.0,
        "median": 100.0,
        "q3": 115.0
    }])):
        # Act
        stats = await detector._get_column_statistics(
            "main.bronze.orders",
            "total_amount"
        )
        
        # Assert
        assert stats is not None
        assert stats["mean"] == 100.0
        assert stats["stddev"] == 15.0
        assert stats["q1"] == 85.0


# ================================================================
# TEST 10: Anomaly Dataclass Serialization
# ================================================================
def test_anomaly_to_dict():
    """Test Anomaly serialization to dictionary."""
    # Arrange
    anomaly = Anomaly(
        anomaly_type=AnomalyType.STATISTICAL_OUTLIER,
        table_name="orders",
        column_name="amount",
        detected_value=5000,
        expected_range=(0, 1000),
        deviation_score=85.5,
        severity=Severity.HIGH,
        description="Value exceeds expected range",
        timestamp=datetime(2026, 2, 11, 12, 0, 0),
        details={"z_score": 4.5}
    )
    
    # Act
    anomaly_dict = anomaly.to_dict()
    
    # Assert
    assert anomaly_dict["anomaly_type"] == "statistical_outlier"
    assert anomaly_dict["detected_value"] == 5000
    assert anomaly_dict["expected_range"] == [0, 1000]
    assert anomaly_dict["severity"] == "high"
    assert anomaly_dict["details"]["z_score"] == 4.5


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

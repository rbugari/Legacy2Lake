"""
Unit Tests for QualityRuleEngine - Sprint 11

Tests cover all rule types:
- Nullability rules
- Range rules
- Format rules (regex patterns)
- Length rules
- Uniqueness rules
- Enum rules
- Custom SQL rules
- Rule evaluation and scoring
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

# Import service under test
from apps.api.services.quality_rule_engine_service import (
    QualityRuleEngine,
    QualityRule,
    RuleViolation,
    QualityReport,
    RuleType,
    Severity
)


@pytest.fixture
def mock_supabase():
    """Mock Supabase client."""
    with patch('apps.api.services.quality_rule_engine_service.create_client') as mock:
        client = Mock()
        mock.return_value = client
        yield client


@pytest.fixture
def engine(mock_supabase):
    """Create QualityRuleEngine instance with mocked Supabase."""
    return QualityRuleEngine(
        tenant_id="00000000-0000-0000-0000-000000000001",
        project_id="10000000-0000-0000-0000-000000000001"
    )


# ================================================================
# TEST 1: Add Quality Rule
# ================================================================
@pytest.mark.asyncio
async def test_add_quality_rule(engine, mock_supabase):
    """Test adding a new quality rule."""
    # Arrange
    rule = QualityRule(
        rule_id="customers_email_not_null",
        rule_type=RuleType.NULLABILITY,
        table_name="customers",
        column_name="email",
        condition={"allow_null": False},
        severity=Severity.HIGH,
        description="Email must not be null"
    )
    
    mock_supabase.table.return_value.insert.return_value.execute.return_value = Mock(
        data=[{"rule_id": rule.rule_id}]
    )
    
    # Act
    result = await engine.add_rule(rule)
    
    # Assert
    assert result == "customers_email_not_null"
    mock_supabase.table.assert_called_with("utm_quality_rules")


# ================================================================
# TEST 2: Get Rules for Table
# ================================================================
@pytest.mark.asyncio
async def test_get_rules_for_table(engine, mock_supabase):
    """Test retrieving rules for a specific table."""
    # Arrange
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = Mock(
        data=[
            {
                "rule_id": "email_not_null",
                "rule_type": "nullability",
                "table_name": "customers",
                "column_name": "email",
                "condition": {"allow_null": False},
                "severity": "high",
                "description": "Email required",
                "enabled": True
            }
        ]
    )
    
    # Act
    rules = await engine.get_rules(table_name="customers", enabled_only=True)
    
    # Assert
    assert len(rules) == 1
    assert rules[0].rule_id == "email_not_null"
    assert rules[0].rule_type == RuleType.NULLABILITY
    assert rules[0].severity == Severity.HIGH


# ================================================================
# TEST 3: Evaluate Nullability Rule (Pass)
# ================================================================
@pytest.mark.asyncio
async def test_evaluate_nullability_rule_pass(engine):
    """Test nullability rule with no null values (pass)."""
    # Arrange
    rule = QualityRule(
        rule_id="test_not_null",
        rule_type=RuleType.NULLABILITY,
        table_name="test_table",
        column_name="test_column",
        condition={"allow_null": False},
        severity=Severity.HIGH
    )
    
    # Mock query execution - no nulls found
    with patch.object(engine, '_execute_query', new=AsyncMock(return_value=[{"null_count": 0}])):
        # Act
        violation = await engine._evaluate_nullability(
            rule, "main.bronze.test_table", 1000
        )
        
        # Assert
        assert violation is None


# ================================================================
# TEST 4: Evaluate Nullability Rule (Fail)
# ================================================================
@pytest.mark.asyncio
async def test_evaluate_nullability_rule_fail(engine):
    """Test nullability rule with null values (fail)."""
    # Arrange
    rule = QualityRule(
        rule_id="test_not_null",
        rule_type=RuleType.NULLABILITY,
        table_name="test_table",
        column_name="test_column",
        condition={"allow_null": False},
        severity=Severity.HIGH
    )
    
    # Mock query execution - 50 nulls found
    with patch.object(engine, '_execute_query', new=AsyncMock(return_value=[{"null_count": 50}])):
        # Act
        violation = await engine._evaluate_nullability(
            rule, "main.bronze.test_table", 1000
        )
        
        # Assert
        assert violation is not None
        assert violation.violation_count == 50
        assert "50 null values" in violation.message
        assert violation.severity == Severity.HIGH


# ================================================================
# TEST 5: Evaluate Range Rule (Pass)
# ================================================================
@pytest.mark.asyncio
async def test_evaluate_range_rule_pass(engine):
    """Test range rule with all values within range (pass)."""
    # Arrange
    rule = QualityRule(
        rule_id="age_range",
        rule_type=RuleType.RANGE,
        table_name="customers",
        column_name="age",
        condition={"min": 0, "max": 120},
        severity=Severity.MEDIUM
    )
    
    # Mock query - no violations
    with patch.object(engine, '_execute_query', new=AsyncMock(return_value=[])):
        # Act
        violation = await engine._evaluate_range(
            rule, "main.bronze.customers", 1000
        )
        
        # Assert
        assert violation is None


# ================================================================
# TEST 6: Evaluate Range Rule (Fail)
# ================================================================
@pytest.mark.asyncio
async def test_evaluate_range_rule_fail(engine):
    """Test range rule with values outside range (fail)."""
    # Arrange
    rule = QualityRule(
        rule_id="age_range",
        rule_type=RuleType.RANGE,
        table_name="customers",
        column_name="age",
        condition={"min": 0, "max": 120},
        severity=Severity.MEDIUM
    )
    
    # Mock query - 3 violations
    with patch.object(engine, '_execute_query', new=AsyncMock(return_value=[
        {"age": -5, "violation_count": 1},
        {"age": 150, "violation_count": 1},
        {"age": 999, "violation_count": 1}
    ])):
        # Act
        violation = await engine._evaluate_range(
            rule, "main.bronze.customers", 1000
        )
        
        # Assert
        assert violation is not None
        assert violation.violation_count == 3
        assert violation.sample_values == [-5, 150, 999]


# ================================================================
# TEST 7: Evaluate Format Rule (Regex)
# ================================================================
@pytest.mark.asyncio
async def test_evaluate_format_rule(engine):
    """Test format rule with regex pattern."""
    # Arrange
    rule = QualityRule(
        rule_id="email_format",
        rule_type=RuleType.FORMAT,
        table_name="customers",
        column_name="email",
        condition={"pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"},
        severity=Severity.MEDIUM
    )
    
    # Mock query - 2 invalid emails
    with patch.object(engine, '_execute_query', new=AsyncMock(side_effect=[
        [{"email": "invalid"}, {"email": "also_invalid"}],
        [{"violation_count": 2}]
    ])):
        # Act
        violation = await engine._evaluate_format(
            rule, "main.bronze.customers", 100
        )
        
        # Assert
        assert violation is not None
        assert violation.violation_count == 2


# ================================================================
# TEST 8: Evaluate Length Rule
# ================================================================
@pytest.mark.asyncio
async def test_evaluate_length_rule(engine):
    """Test length rule for string columns."""
    # Arrange
    rule = QualityRule(
        rule_id="name_length",
        rule_type=RuleType.LENGTH,
        table_name="customers",
        column_name="name",
        condition={"min_length": 2, "max_length": 100},
        severity=Severity.LOW
    )
    
    # Mock query - 1 violation
    with patch.object(engine, '_execute_query', new=AsyncMock(side_effect=[
        [{"name": "A", "length": 1}],
        [{"violation_count": 1}]
    ])):
        # Act
        violation = await engine._evaluate_length(
            rule, "main.bronze.customers", 100
        )
        
        # Assert
        assert violation is not None
        assert violation.violation_count == 1


# ================================================================
# TEST 9: Evaluate Uniqueness Rule (Pass)
# ================================================================
@pytest.mark.asyncio
async def test_evaluate_uniqueness_rule_pass(engine):
    """Test uniqueness rule with no duplicates (pass)."""
    # Arrange
    rule = QualityRule(
        rule_id="email_unique",
        rule_type=RuleType.UNIQUENESS,
        table_name="customers",
        column_name="email",
        severity=Severity.HIGH
    )
    
    # Mock query - no duplicates
    with patch.object(engine, '_execute_query', new=AsyncMock(return_value=[])):
        # Act
        violation = await engine._evaluate_uniqueness(
            rule, "main.bronze.customers", 1000
        )
        
        # Assert
        assert violation is None


# ================================================================
# TEST 10: Evaluate Uniqueness Rule (Fail)
# ================================================================
@pytest.mark.asyncio
async def test_evaluate_uniqueness_rule_fail(engine):
    """Test uniqueness rule with duplicates (fail)."""
    # Arrange
    rule = QualityRule(
        rule_id="email_unique",
        rule_type=RuleType.UNIQUENESS,
        table_name="customers",
        column_name="email",
        severity=Severity.HIGH
    )
    
    # Mock query - 2 duplicates
    with patch.object(engine, '_execute_query', new=AsyncMock(return_value=[
        {"email": "test@example.com", "duplicate_count": 3},
        {"email": "duplicate@example.com", "duplicate_count": 2}
    ])):
        # Act
        violation = await engine._evaluate_uniqueness(
            rule, "main.bronze.customers", 100
        )
        
        # Assert
        assert violation is not None
        assert violation.violation_count == 3  # (3-1) + (2-1)


# ================================================================
# TEST 11: Evaluate Enum Rule
# ================================================================
@pytest.mark.asyncio
async def test_evaluate_enum_rule(engine):
    """Test enum rule with allowed values."""
    # Arrange
    rule = QualityRule(
        rule_id="status_enum",
        rule_type=RuleType.ENUM,
        table_name="orders",
        column_name="status",
        condition={"allowed_values": ["pending", "shipped", "delivered"]},
        severity=Severity.MEDIUM
    )
    
    # Mock query - 2 invalid values
    with patch.object(engine, '_execute_query', new=AsyncMock(side_effect=[
        [{"status": "invalid"}, {"status": "unknown"}],
        [{"violation_count": 2}]
    ])):
        # Act
        violation = await engine._evaluate_enum(
            rule, "main.bronze.orders", 100
        )
        
        # Assert
        assert violation is not None
        assert violation.violation_count == 2


# ================================================================
# TEST 12: Calculate Quality Score
# ================================================================
def test_calculate_quality_score(engine):
    """Test quality score calculation with different severity levels."""
    # Arrange
    violations = [
        RuleViolation(
            rule_id="rule1",
            table_name="test",
            column_name="col1",
            violation_count=10,
            sample_values=[],
            severity=Severity.CRITICAL,
            message="Critical issue",
            timestamp=datetime.now()
        ),
        RuleViolation(
            rule_id="rule2",
            table_name="test",
            column_name="col2",
            violation_count=5,
            sample_values=[],
            severity=Severity.HIGH,
            message="High issue",
            timestamp=datetime.now()
        ),
        RuleViolation(
            rule_id="rule3",
            table_name="test",
            column_name="col3",
            violation_count=2,
            sample_values=[],
            severity=Severity.MEDIUM,
            message="Medium issue",
            timestamp=datetime.now()
        )
    ]
    
    # Act
    score = engine._calculate_quality_score(
        rules_passed=7,
        rules_failed=3,
        violations=violations
    )
    
    # Assert
    # Base score: 7/10 = 70%
    # Penalties: 20 (critical) + 10 (high) + 5 (medium) = 35
    # Final: max(0, 70 - 35) = 35%
    assert score == 35.0


# ================================================================
# TEST 13: Evaluate Table with No Rules
# ================================================================
@pytest.mark.asyncio
async def test_evaluate_table_no_rules(engine):
    """Test evaluating table with no rules defined (perfect score)."""
    # Arrange
    with patch.object(engine, 'get_rules', new=AsyncMock(return_value=[])):
        # Act
        report = await engine.evaluate_table("test_table")
        
        # Assert
        assert report.quality_score == 100.0
        assert report.rules_evaluated == 0
        assert len(report.violations) == 0


# ================================================================
# TEST 14: Evaluate Table with Multiple Rules
# ================================================================
@pytest.mark.asyncio
async def test_evaluate_table_multiple_rules(engine):
    """Test evaluating table with multiple rules."""
    # Arrange
    rules = [
        QualityRule(
            rule_id="rule1",
            rule_type=RuleType.NULLABILITY,
            table_name="test",
            column_name="col1",
            condition={"allow_null": False},
            severity=Severity.HIGH
        ),
        QualityRule(
            rule_id="rule2",
            rule_type=RuleType.RANGE,
            table_name="test",
            column_name="col2",
            condition={"min": 0, "max": 100},
            severity=Severity.MEDIUM
        )
    ]
    
    with patch.object(engine, 'get_rules', new=AsyncMock(return_value=rules)):
        with patch.object(engine, '_get_row_count', new=AsyncMock(return_value=1000)):
            with patch.object(engine, '_evaluate_rule', new=AsyncMock(side_effect=[None, None])):
                with patch.object(engine, '_save_report', new=AsyncMock()):
                    # Act
                    report = await engine.evaluate_table("test")
                    
                    # Assert
                    assert report.rules_evaluated == 2
                    assert report.rules_passed == 2
                    assert report.rules_failed == 0
                    assert report.quality_score == 100.0


# ================================================================
# TEST 15: Rule Dataclass Serialization
# ================================================================
def test_quality_rule_to_dict():
    """Test QualityRule serialization to dictionary."""
    # Arrange
    rule = QualityRule(
        rule_id="test_rule",
        rule_type=RuleType.NULLABILITY,
        table_name="test_table",
        column_name="test_col",
        condition={"allow_null": False},
        severity=Severity.HIGH,
        description="Test description"
    )
    
    # Act
    rule_dict = rule.to_dict()
    
    # Assert
    assert rule_dict["rule_id"] == "test_rule"
    assert rule_dict["rule_type"] == "nullability"
    assert rule_dict["severity"] == "high"
    assert rule_dict["condition"] == {"allow_null": False}


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

# Sprint 11: Data Quality Framework - Quick Reference

**Version:** 3.13  
**Status:** ✅ COMPLETE  
**Last Updated:** February 2026

---

## 🚀 Quick Start (3 minutes)

### 1. Basic Usage

```python
# Sprint 11 is AUTOMATIC - Agent C uses it by default

# Generate a table and get quality data instantly
response = await agent_c.transpile_task({
    "asset_name": "customer_orders",
    "platform": "databricks",
    "layer": "bronze"
})

# Check quality
print(f"Quality Score: {response['quality']['quality_score']}%")
print(f"Completeness: {response['metrics']['completeness']}%")
print(f"Anomalies: {response['anomalies']['anomalies_detected']}")
```

### 2. Add Custom Rules (Optional)

```python
from apps.api.services.quality_rule_engine_service import QualityRuleEngine, QualityRule

# Initialize
engine = QualityRuleEngine(tenant_id="...", project_id="...")

# Add a rule
rule = QualityRule(
    rule_type="NULLABILITY",
    table_name="customer_orders",
    column_name="order_id",
    condition={"not_null": True},
    severity="CRITICAL",
    description="Order ID cannot be null"
)
await engine.add_rule(rule)

# Rules are automatically evaluated by Agent C
```

### 3. Manual Evaluation (Advanced)

```python
# Evaluate quality manually (if not using Agent C)
quality = await engine.evaluate_table("customer_orders", "catalog", "schema")

from apps.api.services.metrics_calculator_service import MetricsCalculator
calculator = MetricsCalculator(tenant_id="...", project_id="...")
metrics = await calculator.calculate_metrics("customer_orders", "catalog", "schema")

from apps.api.services.anomaly_detector_service import AnomalyDetector
detector = AnomalyDetector(tenant_id="...", project_id="...")
anomalies = await detector.detect_anomalies("customer_orders", "catalog", "schema")
```

---

## 📖 Agent C Response Structure

### Complete Response

```python
{
    # EXISTING FIELDS (Sprints 0-10)
    "status": "success",
    "generated_code": "...",
    "execution_result": {...},
    "schema_evolution": {...},
    
    # SPRINT 11: QUALITY DATA
    "quality": {
        "table_name": "customer_orders",
        "quality_score": 85.0,              # 0-100% (higher is better)
        "rules_evaluated": 10,
        "rules_passed": 8,
        "rules_failed": 2,
        "violations": [                     # List of issues found
            {
                "rule_id": "rule-001",
                "rule_type": "NULLABILITY",
                "severity": "HIGH",
                "message": "Column 'email' has 15 null values",
                "column_name": "email",
                "violation_count": 15,
                "sample_values": ["null", ...]
            }
        ],
        "evaluation_time": "2026-02-11T10:30:00Z"
    },
    
    "metrics": {
        "table_name": "customer_orders",
        "overall_score": 88.5,              # Weighted average
        "completeness": 95.0,               # % non-null
        "accuracy": 85.0,                   # % passing rules
        "consistency": 90.0,                # FK integrity
        "timeliness": 100.0,                # Data freshness
        "validity": 92.0,                   # Format conformance
        "uniqueness": 88.0,                 # % distinct
        "calculation_time": "2026-02-11T10:30:01Z"
    },
    
    "anomalies": {
        "table_name": "customer_orders",
        "anomalies_detected": 3,
        "critical_count": 0,
        "high_count": 2,
        "medium_count": 1,
        "low_count": 0,
        "anomalies": [
            {
                "anomaly_id": "anom-001",
                "anomaly_type": "STATISTICAL_OUTLIER",
                "severity": "HIGH",
                "description": "Column 'total_amount' has 5 outliers (z>4.0)",
                "affected_column": "total_amount",
                "metric_value": 4.8,
                "details": {
                    "method": "z_score",
                    "outlier_count": 5
                },
                "detected_at": "2026-02-11T10:30:02Z"
            }
        ],
        "detection_time": "2026-02-11T10:30:02Z"
    }
}
```

---

## 🎯 Rule Types (8)

### Quick Reference Table

| Type | Use Case | Example Condition | Severity |
|------|----------|-------------------|----------|
| **NULLABILITY** | Column cannot be null | `{"not_null": true}` | CRITICAL, HIGH |
| **UNIQUENESS** | No duplicates | `{"unique": true}` | HIGH, MEDIUM |
| **RANGE** | Numeric bounds | `{"min": 0, "max": 100}` | HIGH, MEDIUM |
| **FORMAT** | Regex pattern | `{"pattern": "^[A-Z]{2}\\d{4}$"}` | MEDIUM, LOW |
| **LENGTH** | String length | `{"min_length": 3, "max_length": 50}` | MEDIUM, LOW |
| **ENUM** | Allowed values | `{"allowed_values": ["A", "B", "C"]}` | MEDIUM, LOW |
| **REFERENCE** | Foreign key | `{"ref_table": "users", "ref_column": "id"}` | CRITICAL, HIGH |
| **CUSTOM** | Custom SQL | `{"expression": "value >= 0"}` | ANY |

### Code Examples

#### Nullability Rule
```python
QualityRule(
    rule_type="NULLABILITY",
    table_name="customer_orders",
    column_name="order_id",
    condition={"not_null": True},
    severity="CRITICAL",
    description="Order ID is required"
)
```

#### Range Rule
```python
QualityRule(
    rule_type="RANGE",
    table_name="customer_orders",
    column_name="age",
    condition={"min": 0, "max": 120},
    severity="MEDIUM",
    description="Age must be 0-120"
)
```

#### Format Rule (Email)
```python
QualityRule(
    rule_type="FORMAT",
    table_name="customer_orders",
    column_name="email",
    condition={"pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"},
    severity="HIGH",
    description="Email must be valid"
)
```

#### Format Rule (Phone E.164)
```python
QualityRule(
    rule_type="FORMAT",
    table_name="customer_orders",
    column_name="phone",
    condition={"pattern": r"^\+[1-9]\d{1,14}$"},  # E.164 format
    severity="MEDIUM",
    description="Phone must be E.164 format"
)
```

#### Uniqueness Rule
```python
QualityRule(
    rule_type="UNIQUENESS",
    table_name="customer_orders",
    column_name="order_id",
    condition={"unique": True},
    severity="CRITICAL",
    description="Order ID must be unique"
)
```

#### Reference Rule (Foreign Key)
```python
QualityRule(
    rule_type="REFERENCE",
    table_name="customer_orders",
    column_name="customer_id",
    condition={
        "ref_table": "bronze.customers",
        "ref_column": "id"
    },
    severity="CRITICAL",
    description="Must reference valid customer"
)
```

#### Enum Rule
```python
QualityRule(
    rule_type="ENUM",
    table_name="customer_orders",
    column_name="status",
    condition={"allowed_values": ["pending", "completed", "cancelled"]},
    severity="HIGH",
    description="Status must be valid"
)
```

#### Custom Rule
```python
QualityRule(
    rule_type="CUSTOM",
    table_name="customer_orders",
    column_name="total_amount",
    condition={"expression": "total_amount >= 0 AND total_amount <= 10000"},
    severity="HIGH",
    description="Order amount must be reasonable"
)
```

---

## 📊 Metric Dimensions (6)

### Weights & Scoring

| Dimension | Weight | Description | Score Logic |
|-----------|--------|-------------|-------------|
| **COMPLETENESS** | 25% | % non-null values | `(non_null / total) * 100` |
| **ACCURACY** | 25% | % meeting rules | From QualityRuleEngine |
| **CONSISTENCY** | 15% | FK integrity | `(valid_fks / total_fks) * 100` |
| **TIMELINESS** | 15% | Data freshness | Based on timestamp age |
| **VALIDITY** | 10% | Format conformance | Pattern matching % |
| **UNIQUENESS** | 10% | % distinct values | `(distinct / total) * 100` |

### Overall Score Formula

```
Overall = (Completeness × 0.25) + (Accuracy × 0.25) + (Consistency × 0.15) + 
          (Timeliness × 0.15) + (Validity × 0.10) + (Uniqueness × 0.10)
```

### Timeliness Scoring

| Data Age | Score | Use Case |
|----------|-------|----------|
| < 1 hour | 100% | Real-time dashboards |
| 1-24 hours | 90% | Daily reports |
| 1-7 days | 70% | Weekly aggregations |
| 7-30 days | 50% | Monthly reports |
| > 30 days | 30% | Historical analysis |

### Code Example

```python
from apps.api.services.metrics_calculator_service import MetricsCalculator

calculator = MetricsCalculator(tenant_id="...", project_id="...")

# Calculate all metrics
metrics = await calculator.calculate_metrics(
    table_name="customer_orders",
    catalog="analytics_catalog",
    schema="bronze"
)

# Access scores
print(f"Overall: {metrics.overall_score:.1f}%")
print(f"Completeness: {metrics.completeness_score:.1f}%")
print(f"Accuracy: {metrics.accuracy_score:.1f}%")

# Get historical trends
trends = await calculator.get_metric_trends(
    table_name="customer_orders",
    metric_type="COMPLETENESS",
    days=30
)

for point in trends:
    print(f"{point['timestamp']}: {point['score']}%")
```

---

## 🔍 Anomaly Types (8)

### Detection Methods

| Type | Method | Threshold | Severity Logic |
|------|--------|-----------|----------------|
| **STATISTICAL_OUTLIER** | Z-score or IQR | z > 3.0σ | >5σ=CRITICAL, >4σ=HIGH, >3σ=MEDIUM |
| **VOLUME_SPIKE** | Row count Δ | >30% increase | >50%=HIGH, >30%=MEDIUM |
| **VOLUME_DROP** | Row count Δ | >30% decrease | >50%=HIGH, >30%=MEDIUM |
| **NULL_SPIKE** | Null % Δ | >20% increase | >40%=HIGH, >20%=MEDIUM |
| **DUPLICATE_SPIKE** | Dup % Δ | >20% increase | >40%=HIGH, >20%=MEDIUM |
| **PATTERN_BREAK** | Pattern deviation | Custom | Based on deviation |
| **THRESHOLD_VIOLATION** | Value > limit | Custom | Based on threshold |
| **DATA_DRIFT** | Distribution Δ | Custom | Based on shift |

### Z-Score Method

```python
# Formula
z_score = (value - mean) / std_dev

# Interpretation
|z| > 5.0: CRITICAL (1 in 3.5 million)
|z| > 4.0: HIGH (1 in 15,787)
|z| > 3.0: MEDIUM (1 in 370)

# Example
values = [10, 12, 11, 13, 10, 12, 100]
# 100 has z_score = 8.2 → CRITICAL outlier
```

### IQR Method

```python
# Formula
IQR = Q3 - Q1
Lower bound = Q1 - 1.5 * IQR
Upper bound = Q3 + 1.5 * IQR

# Outliers
value < lower_bound OR value > upper_bound

# Example
values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 100]
Q1 = 2.5, Q3 = 7.5, IQR = 5
Lower = -5, Upper = 15
Outliers: [100]
```

### Code Example

```python
from apps.api.services.anomaly_detector_service import AnomalyDetector

detector = AnomalyDetector(tenant_id="...", project_id="...")

# Detect all anomalies
report = await detector.detect_anomalies(
    table_name="customer_orders",
    catalog="analytics_catalog",
    schema="bronze"
)

# Check critical issues
if report.critical_count > 0:
    print(f"🚨 {report.critical_count} CRITICAL anomalies!")
    for anomaly in report.anomalies:
        if anomaly.severity == "CRITICAL":
            print(f"  - {anomaly.description}")

# Detect specific type (statistical outliers)
outliers = await detector.detect_statistical_outliers(
    table_name="customer_orders",
    column="total_amount",
    method="z_score"  # or "iqr"
)

for outlier in outliers:
    print(f"Outlier in {outlier.affected_column}:")
    print(f"  Value: {outlier.details['value']}")
    print(f"  Z-score: {outlier.details['z_score']}")
```

---

## 🎨 Common Use Cases

### Use Case 1: Bronze Layer Ingestion

**Goal:** Ensure raw data meets basic quality standards

```python
# Define rules for bronze layer
bronze_rules = [
    QualityRule(
        rule_type="NULLABILITY",
        table_name="bronze.raw_events",
        column_name="event_id",
        condition={"not_null": True},
        severity="CRITICAL",
        description="Event ID required"
    ),
    QualityRule(
        rule_type="UNIQUENESS",
        table_name="bronze.raw_events",
        column_name="event_id",
        condition={"unique": True},
        severity="CRITICAL",
        description="Event ID must be unique"
    )
]

# Add rules
engine = QualityRuleEngine(tenant_id, project_id)
for rule in bronze_rules:
    await engine.add_rule(rule)

# Generate table (Agent C auto-validates)
response = await agent_c.transpile_task({
    "asset_name": "raw_events",
    "platform": "databricks",
    "layer": "bronze"
})

# Check quality before proceeding
if response['quality']['quality_score'] < 80:
    print("⚠️ Bronze quality too low, investigate source data")
```

### Use Case 2: Silver Layer Transformations

**Goal:** Validate business logic and data consistency

```python
# Define silver layer rules
silver_rules = [
    QualityRule(
        rule_type="REFERENCE",
        table_name="silver.customer_orders",
        column_name="customer_id",
        condition={
            "ref_table": "bronze.customers",
            "ref_column": "id"
        },
        severity="CRITICAL",
        description="Must reference valid customer"
    ),
    QualityRule(
        rule_type="RANGE",
        table_name="silver.customer_orders",
        column_name="order_amount",
        condition={"min": 0, "max": 10000},
        severity="HIGH",
        description="Order amount must be reasonable"
    ),
    QualityRule(
        rule_type="FORMAT",
        table_name="silver.customer_orders",
        column_name="email",
        condition={"pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"},
        severity="MEDIUM",
        description="Email must be valid"
    )
]

# Generate silver table
response = await agent_c.transpile_task({
    "asset_name": "customer_orders",
    "platform": "snowflake",
    "layer": "silver"
})

# Check consistency
metrics = response['metrics']
if metrics['consistency'] < 95:
    print(f"⚠️ Consistency issue: {metrics['consistency']}%")
    # Investigate FK violations
```

### Use Case 3: Gold Layer Aggregations

**Goal:** Ensure business-critical accuracy

```python
# Define gold layer rules (stricter)
gold_rules = [
    QualityRule(
        rule_type="NULLABILITY",
        table_name="gold.monthly_revenue",
        column_name="total_revenue",
        condition={"not_null": True},
        severity="CRITICAL",
        description="Revenue cannot be null"
    ),
    QualityRule(
        rule_type="RANGE",
        table_name="gold.monthly_revenue",
        column_name="total_revenue",
        condition={"min": 0},
        severity="CRITICAL",
        description="Revenue must be non-negative"
    )
]

# Generate gold table
response = await agent_c.transpile_task({
    "asset_name": "monthly_revenue",
    "platform": "databricks",
    "layer": "gold"
})

# Require 100% accuracy for gold layer
if response['metrics']['accuracy'] < 100:
    print("🚨 Gold layer accuracy < 100%, blocking deployment!")
    # Trigger alerts, block pipeline
```

### Use Case 4: Monitoring Data Quality Trends

**Goal:** Track quality over time and detect degradation

```python
from apps.api.services.metrics_calculator_service import MetricsCalculator

calculator = MetricsCalculator(tenant_id, project_id)

# Get 30-day trends
trends = await calculator.get_metric_trends(
    table_name="customer_orders",
    metric_type="COMPLETENESS",
    days=30
)

# Detect degradation
first_score = trends[0]['score']
last_score = trends[-1]['score']

if last_score < first_score - 10:
    print(f"⚠️ ALERT: Completeness degraded by {first_score - last_score}%")
    print(f"  From {first_score}% to {last_score}% over 30 days")
    # Send alert to Slack/PagerDuty
```

### Use Case 5: Quality Gates in CI/CD

**Goal:** Block deployments if quality is too low

```python
async def quality_gate(
    table_name: str,
    min_quality_score: float = 85.0,
    min_completeness: float = 90.0,
    max_critical_anomalies: int = 0
) -> bool:
    """
    Quality gate for CI/CD pipeline.
    Returns True if quality checks pass, False otherwise.
    """
    # Evaluate quality
    engine = QualityRuleEngine(tenant_id, project_id)
    quality = await engine.evaluate_table(table_name, catalog, schema)
    
    calculator = MetricsCalculator(tenant_id, project_id)
    metrics = await calculator.calculate_metrics(table_name, catalog, schema)
    
    detector = AnomalyDetector(tenant_id, project_id)
    anomalies = await detector.detect_anomalies(table_name, catalog, schema)
    
    # Check thresholds
    if quality.quality_score < min_quality_score:
        print(f"❌ Quality score {quality.quality_score}% < {min_quality_score}%")
        return False
    
    if metrics.completeness_score < min_completeness:
        print(f"❌ Completeness {metrics.completeness_score}% < {min_completeness}%")
        return False
    
    if anomalies.critical_count > max_critical_anomalies:
        print(f"❌ Critical anomalies {anomalies.critical_count} > {max_critical_anomalies}")
        return False
    
    print("✅ Quality gate passed")
    return True

# Use in CI/CD pipeline
if not await quality_gate("customer_orders"):
    sys.exit(1)  # Fail build
```

---

## 🧪 Testing Guide

### Running Tests

```bash
# Run all Sprint 11 tests
pytest tests/test_sprint11_*.py -v

# Run specific test file
pytest tests/test_sprint11_quality_rules.py -v
pytest tests/test_sprint11_metrics_calculator.py -v
pytest tests/test_sprint11_anomaly_detector.py -v

# Run with coverage
pytest tests/test_sprint11_*.py --cov=apps.api.services --cov-report=html

# Run parallel (faster)
pytest tests/test_sprint11_*.py -n auto

# Run specific test
pytest tests/test_sprint11_quality_rules.py::test_evaluate_nullability_rule_pass -v
```

### Test Structure

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.fixture
def mock_supabase():
    """Mock Supabase client"""
    mock = MagicMock()
    mock.from_ = MagicMock()
    mock.from_.return_value.insert = AsyncMock()
    mock.from_.return_value.select = AsyncMock()
    return mock

@pytest.fixture
async def service(mock_supabase):
    """Service instance with mocks"""
    with patch('supabase.create_client', return_value=mock_supabase):
        service = QualityRuleEngine("tenant-id", "project-id")
        service._execute_query = AsyncMock()
        return service

@pytest.mark.asyncio
async def test_evaluate_table(service, mock_supabase):
    """Test table evaluation"""
    # Arrange
    mock_supabase.from_.return_value.select.return_value.eq.return_value.execute = AsyncMock(
        return_value=MagicMock(data=[...])
    )
    service._execute_query.return_value = {"count": 1000}
    
    # Act
    report = await service.evaluate_table("test_table", "catalog", "schema")
    
    # Assert
    assert report.quality_score == 100.0
    assert report.rules_passed == 10
```

### Mock Data Examples

```python
# Mock quality report
mock_quality_report = {
    "table_name": "customer_orders",
    "quality_score": 85.0,
    "rules_evaluated": 10,
    "rules_passed": 8,
    "rules_failed": 2,
    "violations": [
        {
            "rule_id": "rule-001",
            "rule_type": "NULLABILITY",
            "severity": "HIGH",
            "message": "Column 'email' has 15 null values",
            "violation_count": 15
        }
    ]
}

# Mock metrics report
mock_metrics_report = {
    "table_name": "customer_orders",
    "overall_score": 88.5,
    "completeness": 95.0,
    "accuracy": 85.0,
    "consistency": 90.0,
    "timeliness": 100.0,
    "validity": 92.0,
    "uniqueness": 88.0
}

# Mock anomaly report
mock_anomaly_report = {
    "table_name": "customer_orders",
    "anomalies_detected": 3,
    "critical_count": 0,
    "high_count": 2,
    "anomalies": [
        {
            "anomaly_type": "STATISTICAL_OUTLIER",
            "severity": "HIGH",
            "description": "5 outliers detected"
        }
    ]
}
```

---

## 🐛 Troubleshooting

### Issue 1: Quality Score Always 100%

**Symptom:** Quality score is always 100% even with issues

**Solution:**
```python
# Check if rules exist
rules = await engine.get_rules("my_table")
print(f"Rules found: {len(rules)}")  # Should be > 0

# Check if rules are enabled
rules = await engine.get_rules("my_table", enabled_only=False)
disabled = [r for r in rules if not r.enabled]
print(f"Disabled rules: {len(disabled)}")

# Ensure table name matches
full_table_name = f"{schema}.{table_name}"
report = await engine.evaluate_table(full_table_name, catalog, schema)
```

### Issue 2: Metrics Calculation Fails

**Symptom:** KeyError or missing metrics

**Solution:**
```python
# Verify table exists
result = await execute_query(f"SELECT COUNT(*) FROM {table_name}")

# Check for timestamp columns (required for timeliness)
result = await execute_query(f"""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = '{table_name}' 
      AND data_type IN ('timestamp', 'timestamptz')
""")

# Grant permissions
GRANT SELECT ON ALL TABLES IN SCHEMA bronze TO service_role;
```

### Issue 3: No Anomalies Detected

**Symptom:** Anomaly count is always 0

**Solution:**
```python
# Check row count (need >30 for statistical analysis)
result = await execute_query(f"SELECT COUNT(*) as count FROM {table_name}")
if result['count'] < 30:
    print("⚠️ Insufficient data for statistical analysis")

# Check for numeric columns (required for outliers)
result = await execute_query(f"""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = '{table_name}' 
      AND data_type IN ('int', 'float', 'double', 'numeric')
""")

# If no anomalies, data might be uniform (which is good!)
```

### Issue 4: High Memory Usage

**Symptom:** MemoryError

**Solution:**
```python
# Use SQL aggregations instead of loading all data
result = await execute_query(f"""
    SELECT 
        AVG(column) as mean,
        STDDEV(column) as stddev
    FROM {table_name}
""")

# Limit violation samples
SAMPLE_LIMIT = 10
violations = await execute_query(f"""
    SELECT * FROM {table_name}
    WHERE {condition}
    LIMIT {SAMPLE_LIMIT}
""")

# Process tables in batches
BATCH_SIZE = 10
for i in range(0, len(tables), BATCH_SIZE):
    batch = tables[i:i+BATCH_SIZE]
    await process_batch(batch)
```

### Issue 5: Slow Performance (>5s)

**Symptom:** Evaluation takes too long

**Solution:**
```python
# Add indexes
CREATE INDEX idx_table_column ON my_table(column_name);

# Use sampling for large tables (>10M rows)
if total_rows > 10_000_000:
    sample_query = f"""
        SELECT * FROM {table_name}
        TABLESAMPLE BERNOULLI(1)  -- 1% sample
        LIMIT 100000
    """

# Parallel rule evaluation
import asyncio
tasks = [self._evaluate_rule(rule, ...) for rule in rules]
violations = await asyncio.gather(*tasks)

# Cache frequently accessed data
from functools import lru_cache

@lru_cache(maxsize=100)
async def get_table_stats(table_name: str):
    return await execute_query(f"SELECT COUNT(*) FROM {table_name}")
```

---

## 📚 Best Practices

### 1. Layer-Specific Rules

```python
# Bronze: Minimal rules (focus on ingestion)
bronze_rules = [
    "NULLABILITY on ID columns",
    "UNIQUENESS on ID columns"
]

# Silver: Business logic rules
silver_rules = [
    "REFERENCE integrity",
    "FORMAT validation",
    "RANGE checks"
]

# Gold: Strictest rules
gold_rules = [
    "NULLABILITY on all columns",
    "100% accuracy requirement",
    "Zero critical anomalies"
]
```

### 2. Severity Guidelines

```python
# Use CRITICAL for:
# - Primary key violations
# - Null values in required fields
# - Data loss scenarios

# Use HIGH for:
# - Foreign key violations
# - Business rule violations
# - Significant outliers

# Use MEDIUM for:
# - Format inconsistencies
# - Non-critical ranges
# - Minor anomalies

# Use LOW for:
# - Cosmetic issues
# - Optional field validation
# - Informational alerts
```

### 3. Quality Thresholds

```python
# Recommended thresholds by layer
thresholds = {
    "bronze": {
        "quality_score": 70,
        "completeness": 80,
        "max_critical_anomalies": 5
    },
    "silver": {
        "quality_score": 85,
        "completeness": 90,
        "max_critical_anomalies": 2
    },
    "gold": {
        "quality_score": 95,
        "completeness": 98,
        "max_critical_anomalies": 0
    }
}
```

### 4. Monitoring Strategy

```python
# Daily: Check critical tables
critical_tables = ["gold.monthly_revenue", "silver.customer_360"]
for table in critical_tables:
    report = await engine.evaluate_table(table, ...)
    if report.quality_score < 90:
        send_alert(f"Critical table {table} quality: {report.quality_score}%")

# Weekly: Review trends
trends = await calculator.get_metric_trends(table, "COMPLETENESS", days=7)
if trends[-1]['score'] < trends[0]['score'] - 5:
    send_alert(f"Quality degrading for {table}")

# Monthly: Full quality audit
all_tables = await get_all_tables()
quality_audit = await run_quality_audit(all_tables)
generate_quality_report(quality_audit)
```

### 5. Auto-Healing Rules

```python
# Define auto-fix strategies
auto_fix_strategies = {
    "NULLABILITY": {
        "action": "fill_with_default",
        "default_values": {
            "string": "",
            "int": 0,
            "float": 0.0,
            "timestamp": "CURRENT_TIMESTAMP"
        }
    },
    "FORMAT": {
        "action": "normalize",
        "normalizers": {
            "email": "LOWER(TRIM(email))",
            "phone": "REGEXP_REPLACE(phone, '[^0-9+]', '')"
        }
    }
}

# Apply auto-fixes
async def auto_fix_violations(report: QualityReport):
    for violation in report.violations:
        strategy = auto_fix_strategies.get(violation.rule_type)
        if strategy:
            await apply_fix(violation, strategy)
```

---

## 📊 Database Queries

### Useful Quality Queries

```sql
-- 1. Quality score distribution (last 7 days)
SELECT 
    DATE(timestamp) as date,
    AVG(quality_score) as avg_score,
    MIN(quality_score) as min_score,
    MAX(quality_score) as max_score
FROM utm_quality_reports
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY DATE(timestamp);

-- 2. Tables with low quality (<70%)
SELECT 
    table_name,
    quality_score,
    rules_failed,
    timestamp
FROM utm_quality_latest_reports
WHERE quality_score < 70
ORDER BY quality_score ASC;

-- 3. Critical anomalies (last 24 hours)
SELECT 
    table_name,
    critical_count,
    anomalies
FROM utm_anomaly_reports
WHERE critical_count > 0 
  AND timestamp >= NOW() - INTERVAL '24 hours';

-- 4. Metric trends (30 days)
SELECT 
    table_name,
    date,
    avg_completeness_score,
    avg_accuracy_score
FROM utm_quality_trends
WHERE date >= CURRENT_DATE - 30
ORDER BY table_name, date;

-- 5. Rule effectiveness
SELECT 
    rule_type,
    COUNT(*) as total_rules,
    SUM(CASE WHEN enabled THEN 1 ELSE 0 END) as enabled_rules,
    AVG(CASE WHEN severity = 'CRITICAL' THEN 1 ELSE 0 END) as pct_critical
FROM utm_quality_rules
GROUP BY rule_type;
```

---

## 🔗 Resource Links

### Documentation

- [Sprint 11 Implementation Report](SPRINT_11_DATA_QUALITY_REPORT.md) - Full technical documentation
- [Sprint 11 Migration SQL](migrations/sprint_11_data_quality.sql) - Database schema
- [Release Plan](RELEASE_PLAN_ANALYSIS.md) - Overall project status

### Source Code

- [QualityRuleEngine](apps/api/services/quality_rule_engine_service.py) - Rule-based validation (600 LOC)
- [MetricsCalculator](apps/api/services/metrics_calculator_service.py) - Quality metrics (400 LOC)
- [AnomalyDetector](apps/api/services/anomaly_detector_service.py) - Anomaly detection (500 LOC)
- [Agent C Service](apps/api/services/agent_c_service.py) - Integration point (lines 395-502)

### Tests

- [Quality Rules Tests](tests/test_sprint11_quality_rules.py) - 15 tests
- [Metrics Calculator Tests](tests/test_sprint11_metrics_calculator.py) - 15 tests
- [Anomaly Detector Tests](tests/test_sprint11_anomaly_detector.py) - 10 tests

### Related Sprints

- Sprint 7: Data Profiling Engine
- Sprint 8: Real-Time Validation
- Sprint 9: Zero-Hardcode Generation
- Sprint 10: Schema Evolution
- **Sprint 11: Data Quality Framework** ← YOU ARE HERE
- Sprint 12: Performance Optimization (next)

---

## ✅ Summary

**Sprint 11 provides automatic data quality validation for all generated tables.**

- **3 Services:** QualityRuleEngine, MetricsCalculator, AnomalyDetector
- **8 Rule Types:** NULLABILITY, UNIQUENESS, RANGE, FORMAT, LENGTH, ENUM, REFERENCE, CUSTOM
- **6 Metric Dimensions:** Completeness, Accuracy, Consistency, Timeliness, Validity, Uniqueness
- **8 Anomaly Types:** Statistical + pattern-based detection
- **40 Tests:** Complete coverage
- **<500ms:** Fast evaluation
- **100% Automatic:** Integrated with Agent C

**Next:** Sprint 12 - Performance Optimization (2 weeks)

---

**End of Quick Reference**

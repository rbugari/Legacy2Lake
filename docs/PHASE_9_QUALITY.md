# Phase 9: Data Quality Contracts (Optional)

## Overview
**Phase 9** auto-generates **validation suites** (Great Expectations & Soda) from column mapping metadata. This is an **optional** feature—contracts are only created when quality rules are defined.

## The Value Proposition
Modern data platforms require **data contracts** to ensure reliability:
- **Prevent bad data**: Catch nulls, type mismatches early
- **Compliance**: Document data quality SLAs
- **Observability**: Integrate with monitoring (Monte Carlo, etc.)

## Optionality Model
```
IF column has rules (NOT NULL, PII, type constraints)
  THEN generate validation suite
ELSE
  SKIP generation (graceful)
```

**This means:**
- No rules defined? No contracts generated ✅
- Partial rules? Partial contracts ✅
- Full metadata? Full validation coverage ✅

## Supported Frameworks

### 1. Great Expectations (GX)
Industry-standard Python validation library.

**Example Output:**
```json
{
  "expectation_suite_name": "customers.warning",
  "expectations": [
    {
      "expectation_type": "expect_column_values_to_not_be_null",
      "kwargs": {"column": "email"},
      "meta": {"notes": "Derived from is_nullable=False"}
    },
    {
      "expectation_type": "expect_column_values_to_be_of_type",
      "kwargs": {"column": "age", "type_": "Integer"}
    }
  ]
}
```

### 2. Soda Core
YAML-based data quality checks.

**Example Output:**
```yaml
checks for customers:
  - missing_count(email) = 0
  - invalid_percent(phone) < 5%
```

## Rule to Contract Mapping

| Column Rule | GX Expectation | Soda Check |
|:---|:---|:---|
| `is_nullable=False` | `expect_column_values_to_not_be_null` | `missing_count(col) = 0` |
| `datatype=Integer` | `expect_column_values_to_be_of_type(int)` | `invalid_percent(col) < 1%` |
| `is_pii=True` | `expect_column_values_to_not_be_null` | Field presence check |

## Implementation

### Service: `quality_service.py`
```python
class QualityService:
    def generate_great_expectations_json(self, asset_name, mappings):
        expectations = []
        
        for mapping in mappings:
            # Rule 1: NOT NULL
            if mapping.get("is_nullable") is False:
                expectations.append({
                    "expectation_type": "expect_column_values_to_not_be_null",
                    "kwargs": {"column": mapping["source_column"]}
                })
            
            # Rule 2: Type Check
            dtype = mapping.get("source_datatype")
            if dtype:
                expectations.append({
                    "expectation_type": "expect_column_values_to_be_of_type",
                    "kwargs": {"column": mapping["source_column"], "type_": dtype}
                })
        
        # OPTIONAL: return None if no expectations
        return None if not expectations else {
            "expectation_suite_name": f"{asset_name}.warning",
            "expectations": expectations
        }
```

### Integration: `governance_service.py`
```python
async def create_export_bundle(self, project_id):
    ...
    
    # OPTIONAL: Generate quality contracts
    for asset in assets:
        mappings = await db.get_asset_mappings(asset.id)
        
        gx_suite = self.quality.generate_great_expectations_json(
            asset.name, mappings
        )
        
        # Only add if contracts exist
        if gx_suite:
            zip_file.writestr(
                f"quality_contracts/gx/great_expectations_{asset.name}.json",
                json.dumps(gx_suite, indent=2)
            )
```

## Frontend: Data Quality Tab

### `GovernanceView.tsx`
New tab displays:
```tsx
<button onClick={() => setActiveTab("quality")}>
    <Shield size={16} /> Data Quality
</button>

{activeTab === "quality" && (
    <div>
        <h2>Automated Data Quality Contracts</h2>
        <p>
            Contracts derived from your Column Mappings. 
            This feature is <strong>optional</strong>; 
            if no rules are defined, no contracts will be generated.
        </p>
        
        <div className="grid grid-cols-2 gap-8">
            <CodePreview type="GX" />
            <CodePreview type="Soda" />
        </div>
    </div>
)}
```

## Export Structure
```
solution_export.zip
└── quality_contracts/
    ├── gx/
    │   ├── great_expectations_customers.json
    │   └── great_expectations_orders.json
    └── soda/
        ├── checks_customers.yaml
        └── checks_orders.yaml
```

**If no rules**: `quality_contracts/` folder is empty or omitted.

## Deployment Usage
The receiving team can:
1. **Great Expectations:**
   ```python
   import great_expectations as gx
   context = gx.get_context()
   context.add_expectation_suite("customers.warning")
   ```

2. **Soda:**
   ```bash
   soda scan -d databricks -c checks_customers.yaml
   ```

## Future Enhancements (Not Implemented)
- [ ] Custom regex patterns for email/phone validation
- [ ] Range checks (min/max for numeric columns)
- [ ] Referential integrity (FK checks)
- [ ] Integration with Unity Catalog quality metrics

## Testing
See `test_phase9_quality.py`:
- ✅ Active generation when rules exist
- ✅ Graceful skip when no rules
- ✅ Correct GX schema output

## Benefits
- **Zero Manual Setup**: Contracts auto-generated from metadata
- **Optional Adoption**: Not forced if team doesn't use DQ tools
- **Standards Compliant**: Uses industry-standard frameworks
- **Handover Ready**: Contracts included in export bundle

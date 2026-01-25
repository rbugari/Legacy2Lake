# Phase 6: Intelligent Code Generation

## Overview
**Phase 6** connects the forensic intelligence from Architect v2.0 to the code generation engine. Instead of generic transpilation, Agent C now generates **context-aware, optimized PySpark** tailored to each asset's characteristics.

## The Shift
| Before Phase 6 | After Phase 6 |
|:---|:---|
| Generic `.write.save()` for all assets | `.partitionBy()` for high-volume data |
| Manual column masking post-generation | Automatic `SHA2()` for PII fields |
| One-size-fits-all merge logic | Optimized joins based on volume |

## Core Features

### 1. Contextual Transpilation
Agent C's prompt now includes Architect v2.0 metadata:

**Input to Agent C:**
```json
{
  "asset_name": "FactSales",
  "metadata": {
    "volume": "HIGH",
    "partition_key": "transaction_date",
    "is_pii": false
  }
}
```

**Generated Output:**
```python
# High-volume optimization applied
df_sales.write \
    .partitionBy("transaction_date") \
    .mode("overwrite") \
    .save("s3://bucket/gold/fact_sales")
```

### 2. Transformation Logic Editor
New UI component in **Column Mapping** allows per-column custom expressions:

```sql
-- Example: Custom transformation
CASE 
    WHEN age < 18 THEN 'Minor'
    WHEN age >= 65 THEN 'Senior'
    ELSE 'Adult'
END as age_group
```

These expressions are injected into the generated PySpark:
```python
.withColumn("age_group", 
    when(col("age") < 18, "Minor")
    .when(col("age") >= 65, "Senior")
    .otherwise("Adult"))
```

### 3. PII Masking (Automatic)
If `metadata.is_pii = true`:
```python
# Auto-generated for email column
.withColumn("email_masked", sha2(col("email"), 256))
```

## Implementation

### Backend: `agent_c_service.py`
Updated `transpile_task()` method:
```python
async def transpile_task(self, node_data, context):
    metadata = node_data.get("metadata", {})
    
    # Inject metadata into LLM context
    human_content = f"""
    METADATA (Architect v2.0):
    - Volume: {metadata.get("volume")}
    - Partition Key: {metadata.get("partition_key")}
    - PII Exposure: {metadata.get("is_pii")}
    
    Generate optimized PySpark code.
    """
```

### Frontend: `ColumnMappingEditor.tsx`
New "Transformation Logic" text area per column:
```tsx
<textarea
    placeholder="Custom SQL expression..."
    value={column.logic}
    onChange={(e) => updateColumnLogic(column.id, e.target.value)}
/>
```

## Prompt Engineering Update

### `agent_c_interpreter.md`
```markdown
## Input
4. **Operational Metadata (Architect v2.0)**:
    - **Partition Key**: If provided, MUST include `.partitionBy(col)`
    - **Volume**: If HIGH, optimize for shuffles
    - **PII Exposure**: If true, apply masking_rule logic
```

## Code Blueprint Preview
New feature in Drafting Stage shows a **read-only preview** of what will be generated:

```python
# PREVIEW (before running transpilation)
# Asset: DimCustomer
# Strategy: MERGE INTO (SCD Type 2)
# Partitions: registration_year
# PII Masking: email, phone
...
```

## Integration Points

### From Phase 5 (Architect)
Receives:
- `partition_key`
- `volume` (LOW/MED/HIGH)
- `is_pii`

### To Phase 7 (Governance)
Agent G verifies:
- Partition key was used if suggested
- PII masking was applied if flagged

## Testing
See `test_phase6_intelligence.py`:
- ✅ Partition logic injection
- ✅ Custom transformation logic
- ✅ PII masking application

## Benefits
- **Zero Manual Optimization**: Partitioning, masking automated
- **Business Logic Preservation**: Custom expressions supported
- **Production-Ready**: Code follows best practices by default

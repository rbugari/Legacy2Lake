# Phase 5: Architect v2.0 & Discovery Heatmaps

## Overview
**Phase 5** introduces **Architect v2.0**, an intelligent metadata inference engine that transforms the Discovery stage from passive file listing into active forensic analysis. This phase automatically detects data characteristics, security requirements, and operational patterns.

## The Problem
Traditional migration tools treat all files equally, leading to:
- **Over-provisioning**: Small lookup tables processed with same resources as fact tables
- **Under-optimization**: High-volume data without partitioning strategies
- **Security gaps**: PII data detected post-migration

## The Solution: Architect v2.0

### High-Resolution Metadata Inference
Agent A (The Architect) automatically analyzes source metadata to infer:

| Metadata Field | Detection Method | Use Case |
|:---|:---|:---|
| **Data Volume** | Row count estimates from source schema | Partition strategy, cluster sizing |
| **PII Exposure** | Column name heuristics (`email`, `ssn`) | Masking rules, compliance checks |
| **Execution Latency** | Historical execution logs (if available) | Batch window planning |
| **Business Criticality** | Usage frequency + dependencies | Migration priority |
| **Partition Key** | High-cardinality date columns | `.partitionBy()` generation |

### Discovery Heatmaps
Visual intelligence displays in the Discovery UI:

#### 1. PII Exposure Heatmap
- **Red Zone**: Assets with high PII concentration
- **Yellow Zone**: Partial PII (e.g., name fields)
- **Green Zone**: Safe for standard processing

#### 2. Criticality Matrix
- **X-Axis**: Business Criticality (Usage Frequency)
- **Y-Axis**: Data Volume (Scale)
- **Quadrants**: Helps prioritize migration order

## Implementation

### Backend: `architect_service.py`
```python
async def infer_metadata(asset_id: str) -> Dict[str, Any]:
    """
    Analyzes source asset and returns Architect v2.0 metadata.
    """
    # 1. Estimate Volume
    volume = estimate_volume_from_schema(asset)
    
    # 2. Detect PII
    pii_columns = detect_pii_columns(asset.columns)
    
    # 3. Suggest Partition Key
    partition_key = suggest_partition_key(asset.columns)
    
    return {
        "volume": volume,  # LOW | MED | HIGH
        "is_pii": len(pii_columns) > 0,
        "pii_columns": pii_columns,
        "partition_key": partition_key,
        "latency": "DAILY"  # Future: infer from logs
    }
```

### Frontend: `DiscoveryView.tsx`
New heatmap visualization using **color-coded badges** and **interactive filters**.

## Integration with Other Phases

### → Phase 6 (Intelligence)
Architect metadata flows into Agent C's prompt:
```javascript
// If Architect suggests partition_key = "transaction_date"
// Agent C generates:
df.write.partitionBy("transaction_date").save(...)
```

### → Phase 7 (Governance)
Agent G uses PII flags to verify masking compliance:
```json
{
  "check_name": "PII Masking",
  "status": "PASSED",
  "detail": "SHA2 applied to email, ssn"
}
```

## Testing
See `test_phase5_architect.py`:
- ✅ Volume inference from row estimates
- ✅ PII detection via column name patterns
- ✅ Partition key suggestions for date columns

## User Workflow
1. Upload SSIS package → **Discovery runs automatically**
2. View **PII Heatmap** in Discovery Dashboard
3. (Optional) Override inferred metadata in Triage
4. Proceed to Drafting with enriched context

## Benefits
- **Automated Forensics**: Zero manual metadata entry
- **Risk Awareness**: PII exposure visible from day 1
- **Optimized Output**: Code tailored to data characteristics

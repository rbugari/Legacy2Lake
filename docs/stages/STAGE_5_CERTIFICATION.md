# Stage 5: Certification (AI-Driven Quality Assurance & Governance)

## 📌 Overview

> **v4.0 Note**: Certification stage integrates with utm_generation_outcomes analytics for quality trend analysis.
**Certification** is the automated quality gate that ensures generated code meets enterprise standards before deployment. **Agent G (Governor)** audits code for security, performance, compliance, and best practices, then generates a certification package.

> **v3.5 Update**: **Parallel batch processing** - Agent G scans hundreds of files simultaneously from R2, generating compliance scores in minutes.

> **v3.9 GA Status**: ✅ **COMPLETE** - Visualization dashboards integrated (Feb 13, 2026). Deployment readiness dashboards available in Refinement phase with 4 validation tabs.

## 🎯 Objectives
- **Security Audit**: Detect PII exposure, SQL injection risks, hardcoded credentials
- **Performance Review**: Validate join strategies, partitioning, caching
- **Code Standards**: Ensure naming conventions, idempotency, error handling
- **Compliance Scoring**: Generate 0-100 certification score
- **Documentation**: Auto-generate Modernization Runbook and lineage diagrams
- **Bundle Packaging**: Create ready-to-deploy COP (Certified Output Package) bundle
- **Future (v3.9.1)**: Deployment readiness dashboards with resource provisioning, test results, rollback safety

## 👨‍💻 User Guide

### 1. Pre-Certification Check

Before running certification, ensure:
- ✅ Refinement stage is complete (all code generated)
- ✅ Target technology is configured (Databricks, Snowflake, etc.)
- ✅ At least 80% of CORE assets have generated code
- ✅ No critical Agent F rejections remain unresolved

### 2. Run AI Audit

1. **Navigate**: Go to project → Certification tab
2. **Click "Run AI Audit"**: Initiates Agent G (Governor)
3. **Batch Processing**: Agent G:
   - Fetches file inventory from `utm_file_inventory`
   - Reads all generated code from R2 in parallel batches
   - Applies 15+ compliance checks per file
   - Aggregates results into comprehensive scorecard

**Audit Duration**: ~2-5 minutes for 100 files

### 3. Review Compliance Dashboard

**Certification Scorecard**:
```
┌─────────────────────────────────────┐
│ COMPLIANCE SCORE: 92/100           │
│ Status: ✅ CERTIFIED                │
├─────────────────────────────────────┤
│ Category Scores:                    │
│ • Security:       95/100  ✅        │
│ • Performance:    88/100  ✅        │
│ • Best Practices: 92/100  ✅        │
│ • Documentation:  90/100  ✅        │
└─────────────────────────────────────┘
```

**Detailed Findings**:
- **Passed Checks** (Green): Files meeting all criteria
- **Warnings** (Yellow): Minor issues, deployment-safe but improvement recommended
- **Failures** (Red): Critical issues blocking certification

**Badge Meanings**:
- 🟢 **CERTIFIED** (Score ≥ 85): Ready for production deployment
- 🟡 **CONDITIONAL** (Score 70-84): Deployable with known limitations
- 🔴 **REJECTED** (Score < 70): Requires remediation before deployment

### 4. Review Audit Report

**Generated Artifacts**:
1. **`compliance_audit.json`**: Machine-readable scorecard
   ```json
   {
     "overall_score": 92,
     "total_files": 48,
     "passed": 44,
     "warnings": 3,
     "failures": 1,
     "checks": [
       {
         "check_id": "SEC-001",
         "name": "PII Masking Validation",
         "status": "PASSED",
         "files_checked": 25,
         "issues": []
       },
       {
         "check_id": "PERF-003",
         "name": "Partition Key Usage",
         "status": "WARNING",
         "files_checked": 18,
         "issues": [
           {
             "file": "dim_customer.py",
             "message": "No partitioning detected for HIGH volume table",
             "recommendation": "Add .partitionBy('modified_date')"
           }
         ]
       }
     ]
   }
   ```

2. **`Modernization_Runbook.md`**: Human-readable deployment guide
   - Executive Summary
   - Architecture Overview
   - Deployment Instructions
   - Runtime Variables Manifest
   - Data Quality Validation Suite
   - Rollback Plan
   - Known Limitations

### 5. Address Issues (If Needed)

**If Score < 85**:
1. **Review Failures**: Click each red item to see specific file/line
2. **Fix in Refinement**: Return to Stage 4, adjust IR or override code
3. **Re-certify**: Run audit again after fixes
4. **Iterate**: Repeat until passing score achieved

**Common Issues & Fixes**:
| Issue | Fix |
|-------|-----|
| Hardcoded credentials | Replace with `${VAR_NAME}` placeholders |
| Missing partitioning | Add partition keys to metadata |
| Non-idempotent INSERT | Change to MERGE/UPSERT operations |
| Exposed PII | Apply masking functions (SHA2, redaction) |

### 6. Proceed to Handover

Once certified (**score ≥ 85**):
- **"Download COP Bundle"** button becomes active
- **"Proceed to Handover"** advances to Stage 6
- Certification freeze: Code is locked and versioned

## ⚙️ Technical Details

### Services
- **GovernanceService**: Orchestrates Agent G execution
- **PersistenceService**: Fetches code from R2 in batches
- **AgentGService**: AI-powered code audit and documentation
- **PackagingService**: Creates ZIP bundles memory-efficiently

### Agent G (Governor)

**Compliance Checks (v3.5)**:

**Security (SEC)**:
- SEC-001: PII field masking validation
- SEC-002: SQL injection pattern detection
- SEC-003: Credential hardcoding scan
- SEC-004: Row-level security (RLS) enforcement

**Performance (PERF)**:
- PERF-001: Broadcast join optimization (tables < 10MB)
- PERF-002: Partition key presence for large tables
- PERF-003: Caching strategy for iterative operations
- PERF-004: Shuffle minimization patterns

**Best Practices (BP)**:
- BP-001: Idempotent operations (MERGE not INSERT)
- BP-002: Error handling and retry logic
- BP-003: Naming convention adherence
- BP-004: Code modularity and reusability

**Documentation (DOC)**:
- DOC-001: Inline comments for complex logic
- DOC-002: Function/procedure docstrings
- DOC-003: Business intent annotations
- DOC-004: Column-level lineage tracking

### Database Tables

**utm_execution_logs**: Certification audit trail
```sql
{
  log_id: uuid,
  project_id: uuid,
  tenant_id: uuid,
  stage: "CERTIFICATION",
  agent: "AGENT_G",
  status: "SUCCESS | FAILED",
  certification_score: 92,
  audit_results: jsonb,          -- Full compliance_audit.json
  runbook_generated: true,
  bundle_created: true,
  timestamp: "2026-02-01T21:00:00Z"
}
```

### COP Bundle Structure

**Certified Output Package (COP)**:
```
project_demo1_certified_2026-02-01.zip
├── source_code/
│   ├── bronze/
│   ├── silver/
│   └── gold/
├── schema/
│   └── ddl_reference.sql
├── docs/
│   ├── Modernization_Runbook.md
│   ├── compliance_audit.json
│   └── lineage_diagram.png
├── config/
│   └── variables_manifest.json
└── README.md
```

**Variables Manifest**:
```json
{
  "database_name": "${TARGET_DATABASE}",
  "storage_account": "${AZURE_STORAGE_ACCOUNT}",
  "service_principal_id": "${SP_CLIENT_ID}",
  "key_vault_url": "${KEY_VAULT_URL}"
}
```

### Cloud-Native Performance (v3.5)

**Parallel Batch Processing**:
1. **List Files**: Query `utm_file_inventory` (fast, no S3 calls)
2. **Batch Download**: Fetch 10 files from R2 simultaneously
3. **Parallel Audit**: Process files in parallel threads
4. **Aggregate Results**: Combine scores into single report

**Memory-Efficient Bundling**:
- ZIP created in-memory using `BytesIO`
- Files streamed from R2 directly into ZIP buffer
- No temp disk usage
- Upload final bundle to R2 `packages/` directory

**Performance Metrics**:
- **50 files**: ~2 minutes
- **200 files**: ~5 minutes
- **1000 files**: ~15 minutes (enterprise projects)

---

> [!TIP]
> **Score Interpretation**: 85-89 = Good, 90-94 = Excellent, 95+ = Outstanding. Aim for 90+ for production deployments.

> [!IMPORTANT]
> **Certification Lock**: Once certified, the code version is frozen. Any changes require re-certification to maintain compliance traceability.

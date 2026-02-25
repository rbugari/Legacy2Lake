# Stage 6: Handover (Production-Ready Deployment Package)

## 📌 Overview

> **v4.0 Note**: Handover packages include utm_prompts version history and utm_column_profiles forensic data for compliance documentation.
**Handover** is the final delivery stage that packages certified code, deployment documentation, and configuration manifests into a production-ready **Certified Output Package (COP)**. This ZIP bundle can be handed off to DevOps teams or deployed directly to cloud environments.

> **v3.5 Update**: **Secure signed URLs** with time-limited access. COP bundles are generated in-memory and delivered via temporary R2 download links.

> **v3.9 GA Status**: ✅ **COMPLETE** - Visualization dashboards integrated (Feb 13, 2026). Real-time monitoring and performance tracking available across 4 phases (Triage, Drafting, Refinement, Certification).

## 🎯 Objectives
- **Variable Injection**: Replace hardcoded values with CI/CD-ready placeholders
- **Runbook Generation**: Auto-generate comprehensive deployment guide
- **COP Packaging**: Create production-ready ZIP bundle with all artifacts
- **Deployment Validation**: Include test queries and rollback scripts
- **Secure Delivery**: Generate time-limited signed URL for download
- **Archival**: Store COP in R2 for audit and version control
- **Future (v3.9.1)**: Post-deployment observability dashboards

## 👨‍💻 User Guide

### 1. Review Variable Manifest

Before generating the final bundle, review the **Variables Table**:

**Auto-Detected Variables**:
```
┌────────────────────────────────────────┬─────────────────────────────┐
│ Variable Name                          │ Example Value               │
├────────────────────────────────────────┼─────────────────────────────┤
│ ${TARGET_DATABASE}                     │ analytics_prod              │
│ ${STORAGE_ACCOUNT}                     │ mystorageaccount            │
│ ${SERVICE_PRINCIPAL_ID}                │ sp-databricks-prod          │
│ ${KEY_VAULT_URL}                       │ https://kv-prod.vault.az... │
│ ${PARTITION_DATE_COLUMN}               │ event_date                  │
└────────────────────────────────────────┴─────────────────────────────┘
```

**Actions**:
- ✅ **Verify**: Check that all placeholders are correct
- ✏️ **Edit**: Update variable names or add descriptions
- ➕ **Add**: Include custom variables not auto-detected
- 💾 **Save**: Update `variables_manifest.json`

### 2. Configure Deployment Options

**Deployment Target**:
- **Cloud Provider**: Azure (Databricks) | AWS (EMR) | GCP (Dataproc)
- **Environment**: Dev | UAT | Production
- **Naming Prefix**: Optional prefix for all resources

**Included Components** (Toggle):
- ✅ Source Code (Bronze/Silver/Gold)
- ✅ Schema DDL
- ✅ Orchestration (Workflows, DAGs)
- ✅ Documentation (Runbook, Audit Report)
- ✅ Test Suite (Validation queries)
- ⬜ Original Legacy Files (for reference)

### 3. Generate Runbook

Open the left **Sidebar** and click **"View Runbook"** (or Generate) to create the deployment guide:

**Runbook Sections**:
1. **Executive Summary**: Project scope, migration statistics
2. **Architecture Overview**: Medallion layers, data flow diagram
3. **Pre-Deployment Checklist**:
   - Infrastructure prerequisites (compute, storage)
   - Service principal permissions
   - Network/firewall rules
   - Secret vault configuration
4. **Deployment Instructions**:
   - Step-by-step deployment commands
   - Dependency order (tables → views → procedures)
   - Orchestration setup (Databricks Jobs, Airflow DAGs)
5. **Variable Configuration**:
   - Complete list of ${VARIABLES} with descriptions
   - Environment-specific value examples
6. **Validation Suite**:
   - Post-deployment smoke tests
   - Data quality assertions
   - Performance benchmarks
7. **Rollback Plan**:
   - Restore procedures
   - Cleanup scripts
8. **Known Limitations**:
   - Edge cases not migrated
   - Manual intervention required

### 4. Export COP Bundle

1. **Open Sidebar**: Go to the **Export Options** section in the left sidebar.
2. **Click "Export Delivery"**
3. **Bundle Generation**: System creates ZIP in-memory (~30 seconds for 100 files)
3. **R2 Upload**: COP stored at:
   ```
   tenant-{id}/projects/{pid}/packages/cop_{timestamp}.zip
   ```
4. **Signed URL Generated**: Time-limited download link (expires in 4 hours)
5. **Download**: Click link to download COP to local machine

**Bundle Structure**:
```
project_demo1_certified_2026-02-01_v1.0.zip
├── source_code/
│   ├── bronze/
│   │   ├── src_customers.py
│   │   ├── src_orders.py
│   │   └── src_products.py
│   ├── silver/
│   │   ├── stg_customers.py
│   │   ├── stg_orders.py
│   │   └── stg_order_lines.py
│   └── gold/
│       ├── dim_customer.py
│       ├── dim_product.py
│       └── fact_sales.py
├── schema/
│   ├── ddl_bronze_layer.sql
│   ├── ddl_silver_layer.sql
│   └── ddl_gold_layer.sql
├── orchestration/
│   ├── databricks_workflow.json
│   ├── job_dependencies.yaml
│   └── schedule_config.json
├── docs/
│   ├── Modernization_Runbook.md
│   ├── compliance_audit.json
│   ├── lineage_diagram.png
│   └── agent_execution_log.txt
├── config/
│   ├── variables_manifest.json
│   ├── environment_template.env
│   └── deployment_config.yaml
├── tests/
│   ├── validation_queries.sql
│   ├── data_quality_checks.py
│   └── performance_benchmarks.sql
├── README.md
└── CHANGELOG.md
```

### 5. Deployment Handoff

**Option A: Manual Deployment**
1. Extract ZIP to deployment environment
2. Update `environment_template.env` with actual values
3. Run deployment scripts in order:
   ```bash
   ./deploy_schema.sh
   ./deploy_code.sh
   ./validate_deployment.sh
   ```

**Option B: CI/CD Pipeline**
1. Upload COP to artifact repository (Azure DevOps, GitLab, etc.)
2. Configure pipeline variables from `variables_manifest.json`
3. Trigger automated deployment pipeline
4. Review validation results

**Option C: Direct Cloud Deployment** (Future)
- One-click deploy to Databricks Workspace
- Automatic job creation and scheduling
- Built-in validation and rollback

### 6. Post-Deployment Validation

Run included validation suite:

**Smoke Tests**:
```sql
-- Check table existence
SHOW TABLES IN dim;

-- Verify row counts
SELECT COUNT(*) FROM dim_customer;

-- Test sample query
SELECT * FROM fact_sales WHERE sale_date >= CURRENT_DATE - 7;
```

**Data Quality Checks**:
- Primary key uniqueness
- Foreign key integrity
- NULL value thresholds
- Date range validation

**Performance Benchmarks**:
- Query execution time baselines
- Partition pruning verification
- Cache hit rates

## ⚙️ Technical Details

### Services
- **GovernanceService**: Orchestrates COP generation
- **PersistenceService**: R2 bundle storage and signed URL generation
- **PackagingService**: Memory-efficient ZIP creation
- **AgentGService**: Runbook and documentation generation

### Agent G (Governor) - Packaging Mode

**Responsibilities**:
- Aggregate all generated artifacts from R2
- Generate comprehensive Modernization Runbook
- Create variable manifest with smart defaults
- Package everything into deployment-ready structure
- Generate validation test suite

### Database Tables

**utm_execution_logs**: Handover record
```sql
{
  log_id: uuid,
  project_id: uuid,
  tenant_id: uuid,
  stage: "HANDOVER",
  agent: "AGENT_G",
  status: "SUCCESS",
  cop_bundle_path: "tenant-x/projects/y/packages/cop_2026-02-01T21-00-00Z.zip",
  cop_size_bytes: 4567890,
  signed_url: "https://...r2.cloudflarestorage.com/...?X-Amz-Expires=14400",
  signed_url_expires_at: "2026-02-02T01:00:00Z",
  variables_count: 12,
  files_packaged: 48,
  timestamp: "2026-02-01T21:00:00Z"
}
```

### Certified Output Package - COP (v3.5)

**Security Features**:
- **Signed URLs**: Time-limited download links (default: 4 hours)
- **Tenant Isolation**: R2 prefix enforcement
- **Audit Trail**: All downloads logged
- **Versioning**: Timestamp-based COP naming

**Memory-Efficient Packaging**:
```python
# ZIP created entirely in memory
buffer = BytesIO()
with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
    # Stream files from R2 directly into ZIP
    for file in file_inventory:
        content = r2_client.get_object(file.path)
        zf.writestr(file.relative_path, content)
    
    # Add generated docs
    zf.writestr('docs/Modernization_Runbook.md', runbook_content)
    zf.writestr('config/variables_manifest.json', variables_json)

# Upload to R2
r2_client.put_object(cop_r2_path, buffer.getvalue())

# Generate signed URL (4-hour expiry)
signed_url = r2_client.generate_presigned_url(
    'get_object',
    Params={'Bucket': bucket, 'Key': cop_r2_path},
    ExpiresIn=14400
)
```

**Variable Injection**:
All generated code uses placeholders:
```python
# Before variable injection (hardcoded)
database = "analytics_prod"
storage_account = "mystorageaccount"

# After variable injection (CI/CD ready)
database = "${TARGET_DATABASE}"
storage_account = "${STORAGE_ACCOUNT}"
```

**Deployment Configuration Template**:
```yaml
# deployment_config.yaml
environment: production
cloud_provider: azure
region: eastus2

variables:
  TARGET_DATABASE: analytics_prod
  STORAGE_ACCOUNT: mystorageaccount
  SERVICE_PRINCIPAL_ID: sp-databricks-prod
  KEY_VAULT_URL: https://kv-prod.vault.azure.net

compute:
  cluster_type: job_cluster
  node_type: Standard_DS3_v2
  workers: 4
  spark_version: 13.3.x-scala2.12

deployment_order:
  - schema/ddl_bronze_layer.sql
  - schema/ddl_silver_layer.sql
  - schema/ddl_gold_layer.sql
  - source_code/bronze/*
  - source_code/silver/*
  - source_code/gold/*
```

---

> [!TIP]
> **Version Control**: Store COP bundles in Git LFS or artifact repository for compliance and rollback capability.

> [!IMPORTANT]
> **Signed URL Expiry**: Download links expire after 4 hours. If link expires, regenerate from Handover tab without recreating the entire COP.

> [!NOTE]
> **Production Readiness**: The COP is fully self-contained. No additional files or Legacy2Lake access is required for deployment.

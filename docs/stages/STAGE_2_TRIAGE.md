# Stage 2: Triage (Strategy & Scoping)

## 📌 Overview
**Triage** is where the "noise" is filtered out and source technology is automatically detected. You define the **migration scope** by classifying assets into CORE, SUPPORT, or IGNORED.

> **v3.5 Enhancement**: Automatic technology detection using **Agent S (Scout)** analyzes source artifacts to identify SQL dialects, ETL tools, and platform versions.

## 🎯 Objectives
- **Technology Detection**: Identify source platform (SQL Server, Oracle, SSIS, DataStage, etc.)
- **Visual Classification**: Organize assets by migration priority
- **Dependency Inference**: Build dependency mesh architecture
- **Risk and Complexity Scoring**: Automated analysis of migration difficulty

## 👨‍💻 User Guide

### 1. Technology Detection (Agent S)
When you start Triage, **Agent S (Scout)** automatically:
- **Analyzes File Extensions**: `.dtsx` → SSIS, `.dsx` → DataStage, `.sql` → SQL dialect detection
- **Inspects Content**: Detects T-SQL vs PL/SQL vs MySQL syntax
- **Suggests Configuration**: Proposes source/target technology pairing
- **Updates Project Settings**: Stores detected tech in `utm_projects.settings`

You can review and override the detection in the Triage configuration panel.

### 2. Classification Canvas
- **CORE**: Business critical logic. Everything here *will* be migrated.
- **IGNORED**: Legacy backups, temp tables, logs - excluded from processing.
- **SUPPORT**: Required for the build but not migrated directly (e.g., config files, DDL scripts).

### 3. Actions
- **Drag & Drop**: Move items between columns to define scope.
- **Run Analysis**: Activates **Agent A (Architect v2.0)** in Forensics Mode:
    - Calculates `Cyclomatic Complexity`
    - Identifies `P1/P2/P3` criticality
    - Detects **PII** exposure risk
    - Estimates **Data Volumes** (Small/Medium/Large)
    - Suggests **Partition Keys** for optimization
- **Graph View**: Switch to the Graph tab to see a visual dependency mesh.
- **Approve Triage**: Locks the scope and advances to Drafting stage

### 4. V3.9 Visualization Dashboards ⭐ NEW

Triage now includes **4 advanced visualization tabs** providing deep insights into data quality, schema structure, privacy compliance, and optimization opportunities.

#### Quality Dashboard
**Purpose**: Real-time data quality monitoring

**Features**:
- **6 Quality Dimensions**:
  - Completeness (92%)
  - Accuracy (88%)
  - Consistency (90%)
  - Conformity (85%)
  - Uniqueness (95%)
  - Timeliness (78%)
- **Violation Tracking**: Sortable list of quality issues by severity
- **Anomaly Detection**: ML-powered outlier identification
- **Historical Trends**: Quality evolution across assets

**Component**: `QualityDashboard`  
**Endpoint**: `GET /api/visualization/projects/{project_id}/quality`

**Use Cases**:
- Identify problematic legacy assets before migration
- Prioritize remediation efforts
- Set quality gates for stage progression

#### Schema Viewer
**Purpose**: Interactive exploration of data structures

**Features**:
- **Table Browser**: Navigate all discovered tables/views
- **Column Details**: Name, type, nullable, constraints, descriptions
- **Relationship Mapping**: Primary keys, foreign keys visualization
- **Row Count Estimates**: From forensics analysis
- **DDL Preview**: Generate CREATE TABLE statements

**Component**: `SchemaViewer`  
**Endpoint**: `GET /api/visualization/projects/{project_id}/schema`

**Use Cases**:
- Understand legacy schema complexity
- Identify normalization opportunities
- Document business glossary terms

#### PII Heatmap
**Purpose**: Privacy compliance and sensitive data detection

**Features**:
- **PII Detection**: Email, phone, SSN, credit card patterns
- **Severity Levels**: Critical (direct PII) vs Warning (quasi-identifiers)
- **Field Highlighting**: Visual indication of sensitive columns
- **Compliance Score**: GDPR/CCPA readiness assessment
- **Remediation Suggestions**: Masking/encryption recommendations

**Component**: `PIIHeatmap`  
**Endpoint**: `GET /api/visualization/projects/{project_id}/pii-analysis`

**Use Cases**:
- Privacy impact assessment (PIA)
- Plan data anonymization strategy
- Compliance documentation

#### Partition Recommendations
**Purpose**: AI-powered optimization strategy

**Features**:
- **Partition Key Suggestions**: Based on access patterns and cardinality
- **Strategy Selection**: Time-based, hash, range partitioning
- **Performance Impact**: Estimated query speedup and cost reduction
- **Volume Analysis**: Row counts and growth trends per partition
- **Platform-Specific**: Optimized for target cloud (Delta Lake, BigQuery, etc.)

**Component**: `PartitionRecommendations`  
**Endpoint**: `GET /api/visualization/projects/{project_id}/partitions`

**Use Cases**:
- Modernization best practices
- Cost optimization planning
- Performance tuning strategy

**Access**: All 4 dashboards available as tabs in Triage stage UI

### 5. User Context & Annotations
- Select any file to add "User Context".
- Example: *"This table is deprecated, map it to `sales_history` instead."*
- Context is stored in `utm_solution_context` and injected into all agent prompts

### 6. Process Cancellation (v3.6)
- **Immediate Termination**: If a Triage analysis is taking too long or was started by mistake, you can use the **"Cancel Process"** button.
- **Graceful Detection**: The backend checks for a `cancellation_requested` flag in `utm_projects` between agent calls (Agent S and Agent A).
- **Auto-Cleanup**: When a process is cancelled, the project state remains in Triage, allowing you to re-configure and restart when ready.

---

## 🚀 v4.0 Deep Forensic Triage (Feature 2)

### Overview
**Sprint 14 Feature**: Field-level forensic analysis with 99%+ PII detection accuracy and automated quality scoring.

**Status**: ✅ Backend 100% Complete | ⚠️ UI 50% Complete (Triage tab pending)

### ForensicAnalyzer Service (583 lines)

**Capabilities**:
- **Column Profiling**: 22-field analysis per column (type, nullability, cardinality, statistical profile)
- **PII Detection**: 
  - Email: 99%+ accuracy (regex + DNS validation)
  - Phone: 95%+ accuracy (libphonenumber international)
  - SSN: 98%+ accuracy (US format + checksum)
  - Credit Card: 99%+ accuracy (Luhn algorithm)
- **Quality Scoring**: 0-100 score based on null ratio, pattern coverage, constraint compliance
- **Pattern Detection**: Email, UUID, ISO dates, phone formats, custom regex
- **Statistical Profiling**: Min/max, mean, median, stddev, percentiles (JSONB)
- **Sample Values**: Top 5, bottom 5, random 5 (for data preview)
- **Recommendations**: Suggested constraints, indexes, transformations

**API Endpoints**:
```http
POST /api/v1/projects/{project_id}/forensics/analyze
GET  /api/v1/projects/{project_id}/forensics/profiles
GET  /api/v1/projects/{project_id}/forensics/profiles/{object_name}
```

**Example Response**:
```json
{
  "column_name": "email_address",
  "inferred_type": "STRING",
  "nullability_score": 0.02,
  "distinct_ratio": 0.98,
  "semantic_tags": ["PII", "EMAIL"],
  "pii_detected": true,
  "pii_confidence": 0.99,
  "quality_score": 95,
  "detected_patterns": ["email"],
  "pattern_coverage": 0.99,
  "sample_values": {
    "top_5": ["john.doe@example.com", "jane.smith@acme.org", ...],
    "random_5": ["user123@test.com", ...]
  },
  "recommendations": {
    "constraints": ["NOT NULL", "UNIQUE"],
    "indexes": ["btree"],
    "transformations": ["lowercase", "trim"]
  }
}
```

### utm_column_profiles Table

**Storage**: Field-level forensics stored in `utm_column_profiles` (22 columns)

**Key Fields**:
- `profile_id` (UUID primary key)
- `project_id`, `tenant_id`, `object_id` (foreign keys with RLS)
- `column_name`, `column_index`, `inferred_type`, `declared_type`
- `nullability_score`, `cardinality`, `distinct_ratio`
- `semantic_tags[]` (TEXT[]) - PII, EMAIL, PHONE, SSN, CREDIT_CARD
- `pii_detected`, `pii_confidence` (BOOLEAN, FLOAT)
- `quality_score` (0-100 INTEGER)
- `statistical_profile` (JSONB) - min, max, mean, median, stddev, percentiles
- `detected_patterns[]`, `pattern_coverage`
- `sample_values` (JSONB), `recommendations` (JSONB)

**Indexes**:
- 6 indexes including GIN for JSONB and array searches
- Partial index on `pii_detected = TRUE` for fast privacy audits

**Use Cases**:
- GDPR/CCPA privacy impact assessments
- Data quality gates before migration
- Type inference for schema generation
- Validation rule recommendation

### Parser Catalog Integration (v4.0 Feature 4)

**Database-Driven Technology Detection**:
- **utm_parser_catalog**: 10 registered parsers (SSIS, Oracle, DataStage, etc.)
- **utm_source_tech_catalog**: 15+ technologies with capabilities metadata
- **Dynamic Loading**: New technology support via 2 SQL INSERTs (no code deployment)

**Medulla Config** (JSONB):
```json
{
  "file_extensions": [".dtsx", ".xml"],
  "xml_root": "DTS:Executable",
  "component_path": "//DTS:Executable[@DTS:ExecutableType='STOCK:SEQUENCE']",
  "connection_path": "//DTS:ConnectionManager",
  "expressions": {
    "package_name": "//@DTS:ObjectName",
    "description": "//@DTS:Description"
  }
}
```

**Benefits**:
- No hardcoded parsers in codebase
- Tenant-specific parser configurations
- AI-assisted parser generation (future)

### Planned UI Enhancements (Sprint 14 Phase 3)

**Triage Tab - Column Profiles View**:
- [ ] **Table Browser**: Navigate discovered objects with row count badges
- [ ] **Column Grid**: Sortable/filterable list with PII indicators
- [ ] **Quality Dashboard**: Aggregate scores with drill-down
- [ ] **PII Heatmap**: Visual privacy compliance map
- [ ] **Profile Details Panel**: Statistical profile charts, sample values, recommendations

**Status**: Backend API ready, UI components pending

**Design Mockup**: See `docs/usr/WIREFRAME_TRIAGE_v4.0.md`

---

## ⚙️ Technical Details

### Services

**v4.0 Services**:
- **ForensicAnalyzer**: 583 lines - Field-level profiling, PII detection (99%+ accuracy)
- **ValidationService**: 572 lines - Real-time validation (integrated in Refinement)
- **AgentAService**: Architect v2.0 for forensics analysis
- **AgentSService**: Scout for technology detection
- **KnowledgePacketService**: Refactored for parser catalog (-230 lines)

**Legacy Services**:
- **DiscoveryService**: Scans R2 bucket for artifacts
- **GraphService**: Builds dependency mesh

### Database Tables

**v4.0 Tables**:
- **utm_column_profiles**: Field-level forensics (22 columns, 6 indexes)
  - `semantic_tags[]`: ['PII', 'EMAIL', 'PHONE', 'SSN', 'CREDIT_CARD']
  - `statistical_profile`: JSONB with min/max/mean/median/stddev
  - `pii_detected`, `pii_confidence`: Privacy flags
  - `quality_score`: 0-100 integer
  - `recommendations`: Suggested constraints, indexes, transformations
- **utm_parser_catalog**: Technology parser configurations (10 parsers)
- **utm_source_tech_catalog**: Technology definitions (15+ technologies)

**Legacy Tables**:
- **utm_objects**: Asset inventory with metadata (`metadata` JSONB field)
  - `metadata.pii_exposure`: Boolean flag (v3.5 legacy)
  - `metadata.volume`: "SMALL" | "MEDIUM" | "LARGE"
  - `metadata.partition_key`: Suggested partitioning column
  - `metadata.complexity`: Cyclomatic complexity score
- **utm_projects**: Project settings
  - `settings.source_tech`: Detected source (e.g., "SQLSERVER", "ORACLE")
  - `settings.target_tech`: Selected target (e.g., "DATABRICKS", "SNOWFLAKE")
  - `triage_approved_at`: Timestamp when triage was approved

### Technology Knowledge Injection

**v4.0 (Database-Driven)**:
1. Query `utm_parser_catalog` for source technology
2. Load `medulla_config` JSONB (XML paths, file extensions, expressions)
3. Dynamically instantiate parser class (`python_module.python_class`)
4. Inject technology-specific patterns into Agent prompts

**Legacy (v3.9)**:
1. Load hardcoded prompt from `prompt_lab_export/origins/{tech}/`
2. Inject technology-specific patterns
3. Configure cartridge selection

### Metadata Forensics

**v4.0 (Deep Forensic Triage)**:
- **Field-Level Analysis**: utm_column_profiles table (22 fields per column)
- **PII Detection**: Pattern-based + semantic validation (99%+ accuracy)
- **Quality Scoring**: Automated 0-100 score (null ratio, pattern coverage, constraints)
- **Statistical Profiling**: JSONB with min/max/mean/median/stddev/percentiles
- **Recommendations**: AI-generated constraints, indexes, transformations
- **Sample Values**: Top 5, bottom 5, random 5 (JSONB)

**Legacy (v3.5)**:
- **Object-Level Analysis**: utm_objects.metadata JSONB
- **PII Detection**: Boolean flag only (no confidence score)
- **Volume Estimation**: "SMALL" | "MEDIUM" | "LARGE" strings
- **Partition Key Suggestion**: Single recommended column

**Forensics Output Evolution**:
```json
// v3.5 (utm_objects.metadata)
{
  "pii_exposure": true,
  "volume": "LARGE",
  "partition_key": "order_date",
  "complexity": 42
}

// v4.0 (utm_column_profiles)
{
  "column_name": "email_address",
  "semantic_tags": ["PII", "EMAIL"],
  "pii_detected": true,
  "pii_confidence": 0.99,
  "quality_score": 95,
  "statistical_profile": {
    "min_length": 10,
    "max_length": 50,
    "avg_length": 28
  },
  "recommendations": {
    "constraints": ["NOT NULL", "UNIQUE"],
    "indexes": ["btree"]
  }
}
```

---

> [!TIP]
> **Multi-Tenant Isolation**: All triage data is scoped by `tenant_id`. User A cannot see User B's project metadata, even in the same Supabase instance.

> [!NOTE]
> **v4.0 Migration**: Legacy forensics (utm_objects.metadata) remain for backward compatibility. New projects use utm_column_profiles exclusively.

---

**Document Version:** 2.0 (v4.0)  
**Last Updated:** Febrero 17, 2026  
**Sprint:** Sprint 14 Phase 2  
**Status:** Backend 100% Complete | UI 50% Complete  

**See Also**:
- [DATABASE_SCHEMA.md](../DATABASE_SCHEMA.md) - utm_column_profiles schema
- [SYSTEM_ARCHITECTURE.md](../SYSTEM_ARCHITECTURE.md) - Deep Forensic Triage architecture
- [STAGE_3_DRAFTING.md](STAGE_3_DRAFTING.md) - Zero-Hardcode generation
- [STAGE_4_REFINEMENT.md](STAGE_4_REFINEMENT.md) - Real-time validation

---

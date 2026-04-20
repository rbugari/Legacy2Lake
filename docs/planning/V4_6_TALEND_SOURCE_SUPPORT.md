# v4.6 Plan - Talend DI Source Support

> Created: 2026-04-20
> Status: Proposed
> Target Release: v4.6 or v5.0
> Scope: Backend + Parser + Cartridge + Discovery + Agent Integration

---

## 1. Executive Summary

### Problem Statement

UTM (Legacy2Lake) currently supports **SSIS** as the primary ETL migration source, with additional support for SQL, DDL, and manifests. However, **Talend Data Integration (DI)** is one of the most widely deployed open-source ETL platforms globally, with significant market presence in:

- Mid-market companies (cost-conscious alternatives to Informatica/DataStage)
- European and Latin American markets
- Java/Spring ecosystem shops
- Organizations modernizing from Talend to Databricks/Snowflake/Fabric

**Competitive gap:** Next Pathway supports Informatica, Teradata, Ab Initio, and Oracle. UTM's current SSIS-only ETL coverage limits addressable market share in non-Microsoft environments.

### Opportunity

A **copilot-agents repository** developed by third-party contributors contains production-ready agent logic for:

- Parsing Talend `.item` XML files (job definitions, tMap logic, context variables, metadata schemas)
- Analyzing Talend component topology and data flows
- Extracting dependencies and migration waves
- Component-to-target pattern mapping

**This work can be leveraged** to add Talend support to UTM with **minimal redundant engineering**, positioning UTM as the only AI-driven platform covering **both Microsoft (SSIS) and Open Source (Talend)** ETL migration.

### Strategic Value

| Metric | Impact |
|--------|--------|
| **Market Expansion** | +25-35% addressable market (Talend install base ~50K+ companies) |
| **Competitive Differentiation** | Only platform with SSIS + Talend + AI-driven modernization |
| **Cost of Acquisition** | Low (reuse existing parser logic + agent patterns) |
| **Revenue Potential** | Open European/LATAM markets where Talend dominates SSIS |

---

## 2. Current State Analysis

### UTM Source Support (v4.5)

| Source Technology | Support Level | Parser | Cartridge | Agent Coverage |
|------------------|---------------|--------|-----------|----------------|
| **SSIS (.dtsx)** | ✅ Full | ✅ SSISCartridge | ✅ Registered | ✅ All agents |
| **SQL/DDL** | ✅ Full | ✅ Generic | ✅ Yes | ✅ All agents |
| **Informatica** | ❌ None | - | - | - |
| **Talend DI** | ❌ None | - | - | - |
| **DataStage** | ❌ None | - | - | - |
| **Ab Initio** | ❌ None | - | - | - |

### Competitive Landscape

| Platform | SSIS | Talend | Informatica | DataStage | Ab Initio |
|----------|------|--------|-------------|-----------|-----------|
| **Next Pathway** | ❌ | ❌ | ✅ | ✅ | ✅ |
| **LeapLogic** | ❌ | ❌ | ✅ | ⚠️ | ❌ |
| **UTM (current)** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **UTM (with v4.6)** | ✅ | ✅ | ❌ | ❌ | ❌ |

**Immediate differentiation:** No competitor covers both SSIS + Talend with AI-driven modernization.

---

## 3. Talend Technical Overview

### Talend Project Structure

```
TalendProject/
├── talend.project          # Project metadata (language, version, author)
├── process/                # Job definitions (.item XML files)
│   ├── MainJob_0.1.item
│   └── ChildJob_0.1.item
├── context/                # Context variable definitions (.item)
│   └── Default_0.1.item
├── metadata/               # Connection metadata
│   ├── connections/        # Database connections
│   ├── fileDelimited/      # CSV/delimited schemas
│   ├── filePositional/     # Fixed-width schemas
│   ├── fileXml/            # XML schemas
│   └── fileJSON/           # JSON schemas
└── routines/               # Reusable Java code
    └── CustomUtils.item
```

### Key Talend Components (100+ types)

| Category | Examples | Complexity |
|----------|----------|------------|
| **Data Transform** | tMap, tJavaRow, tFilterRow, tAggregateRow, tSortRow | 🟡 Medium-High |
| **File I/O** | tFileInputDelimited, tFileOutputDelimited, tFileInputExcel, tFileInputJSON | 🟢 Low-Medium |
| **Database** | tDBInput, tDBOutput, tDBRow, tDBConnection (PostgreSQL, MySQL, Oracle, Snowflake) | 🟢 Low-Medium |
| **Control Flow** | tRunJob, tPrejob, tPostjob, tFlowToIterate, tLoop, tParallelize | 🟡 Medium |
| **FTP/Cloud** | tFTPGet, tFTPPut, tS3Get, tS3Put, tSFTPGet | 🟢 Low |
| **Logging** | tLogRow, tLogCatcher, tWarn, tDie | 🟢 Low |

**Total component coverage in copilot-agents:** ~60 core components + extensible pattern framework.

---

## 4. Proposed Architecture

### 4.1 Cartridge Layer (Discovery + Parsing)

**New module:** `apps/utm/cartridges/talend/`

```
talend/
├── __init__.py
├── parser.py              # TalendCartridge (implements CartridgeBase + BaseParser)
├── component_registry.py  # Maps Talend components to UTM semantic types
└── utils.py               # XML parsing helpers, tMap extractor
```

#### `TalendCartridge` Interface

```python
class TalendCartridge(CartridgeBase, BaseParser):
    """
    Cartridge for Talend DI (.item) Ingestion.
    Parses job XML, context variables, metadata schemas, and routines.
    """
    
    def can_handle(self, ext: str, content_hint: str = None) -> bool:
        """Returns True for .item files in process/ or context/ folders."""
        return ext.lower() == 'item'
    
    def parse(self, file_path: str, content: bytes) -> List[EvidenceItem]:
        """
        [V5] Extracts deterministic evidence from Talend .item XML.
        
        Returns:
        - Job summary (name, version, purpose from description)
        - Component topology (nodes + connections)
        - tMap transformation logic (input/output mappings, expressions)
        - Context variables (if context .item)
        - Metadata schemas (if metadata .item)
        - Custom routine code (if routine .item)
        """
```

**Evidence extraction strategy:**

1. **Job files** (`process/*.item`):
   - Extract component graph (subjobs, nodes, connections)
   - Parse tMap XML blocks → input/output/var tables + expression mappings
   - Identify tRunJob calls → dependency graph
   - Extract context variable references (`context.VAR_NAME`)

2. **Context files** (`context/*.item`):
   - Extract variable name, type, default value, prompt flag
   - Detect encrypted passwords (`enc:system.encryption.key.v1:...`) → flag for manual replacement

3. **Metadata files** (`metadata/**/*.item`):
   - Database connections → connection strings, credentials (flagged if encrypted)
   - File schemas → column names, types, delimiters, encoding

4. **Routine files** (`routines/*.item`):
   - Extract full Java source code → store as reusable utility evidence

### 4.2 Agent Integration

**Existing UTM agents already support multi-format evidence:**

| Agent | Talend Support Strategy |
|-------|-------------------------|
| **agent-qa** | Parse evidence items → assess complexity, identify blockers (e.g., custom Java routines, encrypted vars) |
| **agent-s** | Build dependency graph from tRunJob topology, classify jobs by wave |
| **agent-a** | Map Talend components to target equivalents (already cartridge-driven) |
| **agent-c** | Generate target code (PySpark/Snowflake/Fabric) from component evidence |
| **agent-f** | Critique generated code (no change needed) |
| **agent-g** | Governance + runbook (no change needed) |

**Key enhancement needed:** Cartridge prompts must include Talend → Target component mappings.

#### Example Cartridge Prompt Addition (PySpark Bronze)

```markdown
## Talend Component Mappings

| Talend Component | PySpark Equivalent | Notes |
|-----------------|-------------------|-------|
| tFileInputDelimited | spark.read.csv() | Map delimiter, quote, escape, encoding |
| tMap | DataFrame.withColumn() + select() | Flatten tMap expressions to column transforms |
| tFilterRow | DataFrame.filter() | Translate Talend expression to PySpark SQL |
| tDBInput | spark.read.jdbc() | Map connection metadata to JDBC URL |
| tDBOutput | DataFrame.write.jdbc() | Map insert/update/upsert modes |
| tRunJob | Call child Spark job as function | Preserve dependency order |
```

### 4.3 Component Mapping Strategy

**Leverage copilot-agents patterns:**

The copilot-agents Talend migrator includes a **Spring Batch architect** that performs component-to-target pattern assignment. UTM can reuse this logic by:

1. Extracting the **component pattern taxonomy** from `spring-batch-architect.agent.md`
2. Translating Spring Batch patterns → UTM target equivalents:

| Talend Pattern | Spring Batch | UTM PySpark | UTM Snowflake SQL | UTM Fabric |
|---------------|--------------|-------------|-------------------|------------|
| Row iteration | ItemReader → Processor → Writer | spark.read → transform → write | COPY INTO → MERGE | COPY → MERGE |
| Single task | Tasklet | Python script task | Stored proc | Notebook task |
| File loop | Partitioner (one per file) | Glob pattern reader | External stage | ForEach activity |
| DB aggregation | Push to SQL in Reader | Push to SQL or DataFrame.groupBy() | Push to SQL | Push to SQL |

**Optimization decisions** (from copilot-agents Task D):

- Push filters to SQL when possible
- Collapse sequential independent steps → parallelize
- Replace explicit connection management with framework defaults
- Detect shared components → extract as reusable functions

---

## 5. Deliverables

### Phase 1 — Parser + Cartridge (4-6 weeks)

| Deliverable | Description | Owner |
|------------|-------------|-------|
| `TalendCartridge` | Parse .item XML → evidence items | Backend |
| Component registry | Map 60 core Talend components → UTM semantic types | Backend |
| Unit tests | Parse fixtures from copilot-agents test suite | QA |
| CartridgeRegistry update | Auto-register Talend cartridge | Backend |

### Phase 2 — Agent Cartridge Prompts (3-4 weeks)

| Deliverable | Description | Owner |
|------------|-------------|-------|
| Talend → PySpark mappings | Add to bronze/silver/gold/direct cartridge prompts | Prompts |
| Talend → Snowflake SQL mappings | Add to Snowflake cartridge prompts | Prompts |
| Talend → Fabric mappings | Add to Fabric cartridge prompts | Prompts |
| Context variable → Env var mapping | Standardize approach across targets | Prompts |

### Phase 3 — E2E Validation (2-3 weeks)

| Deliverable | Description | Owner |
|------------|-------------|-------|
| Talend test fixture | Real-world Talend project (3-5 jobs, tMap, tRunJob, DB + file I/O) | QA |
| Discovery → Drafting pipeline | Validate full flow for Talend source | QA |
| Golden output comparison | Verify functional equivalence vs. original Talend execution | QA |

### Phase 4 — UI + Documentation (2 weeks)

| Deliverable | Description | Owner |
|------------|-------------|-------|
| Source selector UI | Add "Talend DI" option in project creation | Frontend |
| Upload instructions | Guide users to upload `talend.project` + folders | Docs |
| Migration guide | Talend-specific best practices (encryption, routines, tMap complexity) | Docs |

**Total Effort:** 11-15 weeks (2.5-3.5 months)

---

## 6. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **tMap complexity** | 🔴 High — Talend's tMap allows arbitrary Java expressions and lookups | Start with simple tMaps; flag complex ones for manual review |
| **Custom routines** | 🟡 Medium — Java code must be translated to Python/SQL | Extract as evidence, flag for human validation, optionally use LLM to translate |
| **Encrypted passwords** | 🟡 Medium — Cannot decrypt, must replace with env vars | Parser detects pattern, flags in gaps/blockers, provides replacement template |
| **Version compatibility** | 🟢 Low — Talend XML schema stable since v6.x | Test against v6, v7, v8 fixtures |
| **Component coverage** | 🟡 Medium — 100+ components, copilot-agents covers ~60 | Start with core 60, add others incrementally based on demand |

---

## 7. Success Criteria

### MVP Definition (v4.6)

- ✅ UTM can ingest a Talend project (`.item` files + metadata)
- ✅ Discovery stage identifies jobs, dependencies, components, and blockers
- ✅ Triage stage builds dependency graph and migration waves
- ✅ Drafting stage generates PySpark/Snowflake/Fabric code for 60 core components
- ✅ E2E validation passes for a real Talend project (3-5 jobs)

### Success Metrics

| Metric | Target |
|--------|--------|
| **Component coverage** | 60+ components (80% of typical Talend projects) |
| **Parser accuracy** | 95%+ deterministic extraction (no LLM inference needed) |
| **E2E success rate** | 80%+ jobs migrate without manual intervention |
| **Time to first draft** | <5 min for 10-job Talend project |

---

## 8. Competitive Impact

### Before v4.6

| Platform | SSIS | Talend | AI-Driven | Multi-Target | Price |
|----------|------|--------|-----------|--------------|-------|
| **Next Pathway** | ❌ | ❌ | ⚠️ | ✅ | $$$$ |
| **UTM** | ✅ | ❌ | ✅✅ | ✅ | $$ |

### After v4.6

| Platform | SSIS | Talend | AI-Driven | Multi-Target | Price |
|----------|------|--------|-----------|--------------|-------|
| **Next Pathway** | ❌ | ❌ | ⚠️ | ✅ | $$$$ |
| **UTM** | ✅ | ✅ | ✅✅ | ✅ | $$ |

**Unique positioning:** Only platform covering Microsoft + Open Source ETL with AI-driven modernization at mid-market pricing.

---

## 9. Go-to-Market Implications

### Target Segments

1. **European mid-market** (strong Talend presence, cost-sensitive)
2. **LATAM enterprises** (Talend + Oracle → Snowflake/Databricks migrations common)
3. **Java/Spring shops** (prefer open-source ETL, modernizing to cloud)

### Messaging

> "UTM is the only AI-powered migration platform that covers both Microsoft SSIS and Open Source Talend, enabling you to modernize your entire ETL estate—regardless of vendor lock-in—to Snowflake, Databricks, or Microsoft Fabric."

### Pricing Impact

- **No price increase** (same per-project pricing model)
- **Positioning as premium vs. competitors** (justify 2x Next Pathway price with broader coverage)

---

## 10. Recommendation

**Priority:** 🟡 **MEDIUM-HIGH** (v4.6 or early v5.0)

**Rationale:**
- Low engineering cost (reuse copilot-agents parser logic)
- High market impact (+25-35% addressable market)
- Strategic differentiation (only SSIS + Talend platform)
- Complements v4.5 intelligence/readiness work (no conflict)

**Suggested Timeline:**
- Start after v4.5 stabilization (May 2026)
- Target GA: Q3 2026 (Sep-Oct 2026)

**Sequencing vs. Other Roadmap Items:**
- **Before:** Git integration, self-service onboarding, API v1 (v4.1 enterprise blockers)
- **After or parallel:** Slack/Teams, column lineage UI, Airflow export (v4.2 polish items)

---

## 11. Next Steps

### Immediate Actions (if approved)

1. **Week 1:** Audit copilot-agents codebase → extract reusable parser logic
2. **Week 2:** Spike `TalendCartridge` prototype → validate .item parsing
3. **Week 3:** Source 2-3 real Talend projects as test fixtures
4. **Week 4:** Kickoff sprint planning for Phase 1

### Decision Required

- ✅ Approve for v4.6 roadmap?
- ✅ Allocate 1 backend dev + 1 prompt engineer for 3 months?
- ✅ Approve using copilot-agents reference code (MIT licensed)?

---

*Document Owner: Product Strategy*  
*Contributors: Engineering, Prompts, Competitive Intelligence*  
*Created: 2026-04-20*  
*Status: Awaiting Approval*

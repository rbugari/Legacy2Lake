# Zero-Hardcode Architecture - v4.0

**Status:** ✅ Implemented (Sprint 14)  
**Date:** February 16, 2026  
**Scope:** Phase B - Knowledge Packet Service

---

## 🎯 Problem Statement

**v3.x Architecture (HARDCODED):**
```python
# ❌ WRONG: Adding Talend requires SERVICE code changes
if source_tech == "SSIS":
    result = self._extract_ssis_intelligence(medulla)
elif source_tech == "Oracle":
    result = self._extract_oracle_intelligence(medulla)
elif source_tech == "DataStage":
    result = self._extract_datastage_intelligence(medulla)
# Adding Talend = new elif + new method (SERVICE CHANGE) ❌
```

**Impact:**
- Every new technology requires service code changes
- Violates Open/Closed Principle (open for extension, closed for modification)
- Not truly "cartridge-based" if services have tech-specific logic

---

## ✅ Solution: Database-Driven Parser Registry

**v4.0 Architecture (ZERO-HARDCODE):**

### 1. Parser Catalog Tables

```sql
-- Technology catalog (like MCP agent_catalog)
CREATE TABLE utm_source_tech_catalog (
    tech_id         TEXT PRIMARY KEY,
    tech_name       TEXT NOT NULL,
    tech_aliases    TEXT[],  -- ["SSIS", "SQL Server", "SqlServer"]
    vendor          TEXT,
    category        TEXT,
    is_active       BOOLEAN DEFAULT TRUE
);

-- Parser registry with configuration
CREATE TABLE utm_parser_catalog (
    parser_id       TEXT PRIMARY KEY,
    parser_name     TEXT NOT NULL,
    tech_id         TEXT REFERENCES utm_source_tech_catalog(tech_id),
    
    -- 🔥 KEY: JSONB configuration (data-driven)
    medulla_config  JSONB NOT NULL,
    -- Example:
    -- {
    --   "main_key": "data_flow_logic",
    --   "sql_keys": ["SqlCommand", "OpenRowset"],
    --   "transformation_types": ["DerivedColumn", "Lookup"],
    --   "complexity_weights": {"Lookup": 3, "Script": 8}
    -- }
    
    python_module   TEXT,
    python_class    TEXT,
    priority        INTEGER DEFAULT 100,
    is_active       BOOLEAN DEFAULT TRUE
);
```

### 2. Resolution Function

```sql
CREATE FUNCTION resolve_parser_by_tech(p_source_tech TEXT)
RETURNS TABLE (parser_id, medulla_config JSONB, ...)
AS $$
    SELECT p.parser_id, p.medulla_config, ...
    FROM utm_parser_catalog p
    INNER JOIN utm_source_tech_catalog t ON p.tech_id = t.tech_id
    WHERE UPPER(p_source_tech) = ANY(
        SELECT UPPER(unnest(t.tech_aliases))
    )
    ORDER BY p.priority ASC
    LIMIT 1;
$$;
```

### 3. Service Implementation (Data-Driven)

```python
async def _extract_source_intelligence(self, metadata: Dict) -> Dict:
    """
    ✅ ZERO-HARDCODE: No if/elif tech checks.
    """
    source_tech = metadata.get("source_tech", "UNKNOWN")
    medulla = metadata.get("logical_medulla", {})
    
    # 🔥 Resolve parser from DATABASE
    parser_config = await self._resolve_parser_config(source_tech)
    
    # 🔥 Use config to extract data dynamically
    return self._extract_intelligence_dynamic(medulla, parser_config)

def _extract_intelligence_dynamic(self, medulla: Dict, config: Dict) -> tuple:
    """
    Uses config JSONB to locate data (NO tech-specific code).
    """
    main_key = config["main_key"]  # "data_flow_logic" or "stages"
    sql_keys = config["sql_keys"]  # ["SqlCommand"] or ["sql_query"]
    
    for component in medulla.get(main_key, []):
        # Extract SQL from dynamic keys
        for sql_key in sql_keys:
            if sql_key in component:
                source_query = component[sql_key]
                break
        
        # Extract transformations using config
        # Extract complexity using config weights
        # ...
    
    return (source_query, transformations, complexity)
```

---

## 🚀 How to Add New Technology (Zero Code Changes)

### Example: Adding Talend Support

**Step 1: Insert Technology**
```sql
INSERT INTO utm_source_tech_catalog VALUES (
    'talend',
    'Talend Open Studio',
    ARRAY['Talend', 'TOS', 'Talend Open Studio'],
    'Talend',
    'ETL',
    true
);
```

**Step 2: Insert Parser Configuration**
```sql
INSERT INTO utm_parser_catalog VALUES (
    'parser-talend',
    'Talend Intelligence Extractor',
    'talend',
    '{
        "main_key": "subjobs",
        "sql_keys": ["query", "dbquery"],
        "transformation_types": ["tMap", "tJoin", "tAggregateRow"],
        "complexity_weights": {
            "tmap": 5,
            "tjoin": 4,
            "taggregaterow": 6
        }
    }'::jsonb,
    'apps.api.services.knowledge_packet_service',
    'KnowledgePacketService._extract_intelligence_dynamic',
    100
);
```

**Step 3: Done ✅**
- No service code changes
- No redeployment required (just run migration)
- Parser automatically resolved for Talend assets

---

## 📊 Supported Technologies (v4.0)

| Tech ID | Name | Status | Parser ID |
|---------|------|--------|-----------|
| `ssis` | SQL Server Integration Services | ✅ Active | `parser-ssis` |
| `oracle` | Oracle Database (PL/SQL) | 🟡 Stub | `parser-oracle` |
| `datastage` | IBM DataStage | 🟡 Stub | `parser-datastage` |
| `informatica` | Informatica PowerCenter | 🟡 Stub | `parser-informatica` |
| `talend` | Talend Open Studio | ⚪ Registered | `parser-talend` |
| `pentaho` | Pentaho Data Integration | ⚪ Registered | N/A |
| `sap-bods` | SAP BusinessObjects DS | ⚪ Registered | N/A |
| `ab-initio` | Ab Initio | ⚪ Registered | N/A |
| `teradata` | Teradata | ⚪ Registered | N/A |
| `generic` | Generic SQL | ✅ Fallback | `parser-generic` |

**Legend:**
- ✅ Active: Fully implemented with medulla_config
- 🟡 Stub: Config registered, awaits parser implementation
- ⚪ Registered: In catalog, no parser yet

---

## 🔬 Configuration Schema Reference

### medulla_config JSONB Structure

```typescript
interface MedullaConfig {
    // Primary key in medulla containing components/stages/procedures
    main_key: string;  // "data_flow_logic" | "stages" | "stored_procedures"
    
    // Keys that may contain SQL queries
    sql_keys: string[];  // ["SqlCommand", "OpenRowset"] | ["sql_query"]
    
    // Component types considered transformations
    transformation_types: string[];  // ["DerivedColumn", "Lookup"] | ["Transformer"]
    
    // Complexity weights by component type (0-10 per component)
    complexity_weights: {
        [component_type: string]: number;
    };
}
```

### Example Configurations

**SSIS:**
```json
{
    "main_key": "data_flow_logic",
    "sql_keys": ["SqlCommand", "OpenRowset", "TableOrViewName"],
    "transformation_types": ["DerivedColumn", "Lookup", "Sort", "UnionAll"],
    "complexity_weights": {
        "oledbsource": 1,
        "lookup": 3,
        "script": 8,
        "fuzzy": 10
    }
}
```

**Oracle:**
```json
{
    "main_key": "stored_procedures",
    "sql_keys": ["procedure_body", "function_body"],
    "transformation_types": ["CURSOR", "FUNCTION", "TRIGGER"],
    "complexity_weights": {
        "procedure": 5,
        "function": 4,
        "trigger": 6,
        "package": 10
    }
}
```

**DataStage:**
```json
{
    "main_key": "stages",
    "sql_keys": ["sql_query", "user_sql"],
    "transformation_types": ["Transformer", "Aggregator", "Join"],
    "complexity_weights": {
        "oracleconnectorpx": 2,
        "transformer": 3,
        "aggregator": 4
    }
}
```

---

## 🎓 Comparison with Other Catalogs

Legacy2Lake uses **catalog pattern** consistently:

| Catalog | Purpose | Row-Level Security | Example |
|---------|---------|-------------------|---------|
| `utm_agent_catalog` | AI agent registry | Global (RLS read) | Agent A, Agent C, Agent F |
| `utm_model_catalog` | LLM model offerings | Tenant-specific | gpt-4, claude-sonnet |
| `utm_provider_vault` | API keys | Tenant-specific (encrypted) | Azure OpenAI, OpenAI |
| **`utm_parser_catalog`** | **Intelligence extractors** | **Global (RLS read)** | **parser-ssis, parser-oracle** |
| **`utm_source_tech_catalog`** | **Source technologies** | **Global (RLS read)** | **SSIS, Oracle, DataStage** |

All follow same pattern:
1. Global/tenant-aware catalogs
2. RLS policies for multi-tenancy
3. Database-driven resolution (no hardcode)
4. JSON configuration for flexibility

---

## 🧪 Testing Strategy

### Unit Tests

```python
@pytest.mark.asyncio
async def test_resolve_parser_config_ssis(knowledge_service):
    """Test parser resolution from database."""
    config = await knowledge_service._resolve_parser_config("SSIS")
    
    assert config is not None
    assert config["main_key"] == "data_flow_logic"
    assert "SqlCommand" in config["sql_keys"]
    assert "lookup" in config["complexity_weights"]

@pytest.mark.asyncio
async def test_extract_intelligence_dynamic(knowledge_service):
    """Test data-driven extraction (no tech-specific code)."""
    medulla = {
        "data_flow_logic": [
            {
                "type": "OleDbSource",
                "name": "Source",
                "raw_properties": {"SqlCommand": "SELECT * FROM dbo.Customers"}
            }
        ]
    }
    
    config = {
        "main_key": "data_flow_logic",
        "sql_keys": ["SqlCommand"],
        "transformation_types": ["DerivedColumn"],
        "complexity_weights": {"oledbsource": 1}
    }
    
    query, transforms, complexity = knowledge_service._extract_intelligence_dynamic(medulla, config)
    
    assert query == "SELECT * FROM dbo.Customers"
    assert complexity > 0
```

### Integration Tests

```python
async def test_end_to_end_zero_hardcode():
    """Test that adding new tech requires ZERO service changes."""
    
    # 1. Insert new tech in database
    db.execute("""
        INSERT INTO utm_source_tech_catalog VALUES (
            'talend', 'Talend', ARRAY['Talend', 'TOS'], 'Talend', 'ETL', true
        )
    """)
    
    # 2. Register parser config
    db.execute("""
        INSERT INTO utm_parser_catalog VALUES (
            'parser-talend', 'Talend Extractor', 'talend',
            '{"main_key": "subjobs", "sql_keys": ["query"], ...}'::jsonb,
            ..., 100
        )
    """)
    
    # 3. Process Talend asset (NO service code changes)
    asset = create_talend_asset()
    packet = await knowledge_service.get_packet(asset.id)
    
    assert packet.source_tech == "talend"  # ✅ Works immediately
    assert packet.source_intelligence is not None
```

---

## 📈 Performance Considerations

### Caching Strategy

```python
class KnowledgePacketService:
    def __init__(self):
        self._parser_cache: Dict[str, Dict] = {}  # In-memory cache
    
    async def _resolve_parser_config(self, source_tech: str) -> Dict:
        """Cache parser configs to avoid repeated DB calls."""
        cache_key = source_tech.upper()
        
        if cache_key in self._parser_cache:
            return self._parser_cache[cache_key]
        
        # Resolve from DB
        config = await self._db_resolve_parser(source_tech)
        
        # Cache for duration of service instance
        self._parser_cache[cache_key] = config
        return config
```

### Expected Performance

- **First call:** ~50ms (DB query + processing)
- **Cached calls:** ~5ms (memory lookup)
- **Cold start (Railway):** Config loaded on first request per deployment

---

## 🔐 Security & Multi-Tenancy

### RLS Policies

```sql
-- Parser catalogs are GLOBAL (not tenant-specific)
CREATE POLICY parser_catalog_read 
ON utm_parser_catalog 
FOR SELECT 
TO authenticated 
USING (is_active = true);

-- Similar to:
-- - utm_agent_catalog (global agent registry)
-- - utm_model_catalog (available models)
```

**Rationale:**
- Parser configurations are **technology definitions**, not tenant data
- All tenants use same parsers (like all tenants use same AI agents)
- Tenant isolation happens at **asset level** (utm_objects has tenant_id)

### Tenant Customization (Future)

If needed, allow tenant-specific parser overrides:

```sql
CREATE TABLE utm_parser_overrides (
    override_id     TEXT PRIMARY KEY,
    tenant_id       UUID REFERENCES utm_tenants(tenant_id),
    parser_id       TEXT REFERENCES utm_parser_catalog(parser_id),
    custom_config   JSONB,  -- Override medulla_config for this tenant
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 📝 Migration Checklist

- [x] Create `utm_source_tech_catalog` table
- [x] Create `utm_parser_catalog` table
- [x] Create `resolve_parser_by_tech()` function
- [x] Seed 10 source technologies
- [x] Register 5 parsers (SSIS, Oracle, DataStage, Informatica, Generic)
- [x] Refactor `KnowledgePacketService._extract_source_intelligence()`
- [x] Implement `_extract_intelligence_dynamic()` (data-driven)
- [x] Remove deprecated tech-specific methods (6 methods deleted)
- [x] Add parser config caching
- [ ] Update unit tests to mock/use real DB
- [ ] Integration test for Zero-Hardcode workflow
- [ ] Performance benchmarks (compare v3.x vs v4.0)
- [ ] Documentation for parser developers

---

## 🎯 Future Enhancements

### 1. Parser Plugins (External Python Modules)
```python
# Load parser from external module (vs inline methods)
parser_class = importlib.import_module(config["python_module"])
extractor = getattr(parser_class, config["python_class"])()
result = extractor.extract(medulla)
```

### 2. Visual Parser Builder (UI)
- Admin interface to register new technologies
- JSON schema editor for medulla_config
- Test parser against sample medulla
- Deploy without code changes

### 3. Parser Marketplace
- Community-contributed parsers
- Version control for parser configs
- A/B testing different extraction strategies

---

## 📚 Related Documentation

- [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) - Overall v4.0 architecture
- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) - Schema reference
- [technical/cartridge_manual.md](technical/cartridge_manual.md) - Cartridge development
- [copilot-instructions.md](../.github/copilot-instructions.md) - Coding standards

---

**Questions?** Contact: Legacy2Lake Architecture Team  
**Last Updated:** 2026-02-16 (Sprint 14)

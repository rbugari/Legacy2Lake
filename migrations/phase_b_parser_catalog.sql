-- ============================================
-- Phase B: Parser Catalog (Zero-Hardcode)
-- Sprint 14 - v4.0
-- Date: 2026-02-16
-- ============================================
--
-- Problem: knowledge_packet_service has hardcoded tech detection:
--   if source_tech.upper() in ["SSIS", "SQL SERVER"]:  ❌ HARDCODE
--
-- Solution: Database-driven parser registry (like utm_agent_catalog)
--
-- ============================================

-- ============================================
-- 1. Source Technology Catalog
-- ============================================

CREATE TABLE IF NOT EXISTS utm_source_tech_catalog (
    tech_id         TEXT PRIMARY KEY,
    tech_name       TEXT NOT NULL,
    tech_aliases    TEXT[] NOT NULL,  -- ["SSIS", "SQL Server", "SqlServer"]
    vendor          TEXT,              -- Microsoft, Oracle, IBM, Informatica, etc.
    category        TEXT,              -- ETL, Database, DataWarehouse, etc.
    description     TEXT,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 2. Parser Registry (Intelligence Extractors)
-- ============================================

CREATE TABLE IF NOT EXISTS utm_parser_catalog (
    parser_id       TEXT PRIMARY KEY,
    parser_name     TEXT NOT NULL,
    tech_id         TEXT NOT NULL REFERENCES utm_source_tech_catalog(tech_id),
    
    -- Medulla structure configuration (JSONB for flexibility)
    medulla_config  JSONB NOT NULL,
    -- Example: {
    --   "main_key": "data_flow_logic",
    --   "sql_keys": ["SqlCommand", "OpenRowset"],
    --   "transformation_key": "type",
    --   "complexity_weights": {"Lookup": 3, "Script": 8}
    -- }
    
    -- Python implementation reference
    python_module   TEXT,  -- "apps.api.services.intelligence_extractors.ssis"
    python_class    TEXT,  -- "SSISIntelligenceExtractor"
    
    priority        INTEGER DEFAULT 100,  -- Lower = higher priority
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 3. Indexes
-- ============================================

CREATE INDEX IF NOT EXISTS idx_parser_catalog_tech 
ON utm_parser_catalog(tech_id, is_active);

CREATE INDEX IF NOT EXISTS idx_source_tech_active 
ON utm_source_tech_catalog(is_active);

-- ============================================
-- 4. Enable Row Level Security
-- ============================================

-- These are GLOBAL catalogs (not tenant-specific)
-- Similar to utm_agent_catalog

ALTER TABLE utm_source_tech_catalog ENABLE ROW LEVEL SECURITY;
ALTER TABLE utm_parser_catalog ENABLE ROW LEVEL SECURITY;

-- Policy: Service role can see all
CREATE POLICY parser_catalog_service_role 
ON utm_parser_catalog 
FOR ALL 
TO service_role 
USING (true);

CREATE POLICY source_tech_service_role 
ON utm_source_tech_catalog 
FOR ALL 
TO service_role 
USING (true);

-- Policy: Authenticated users can read (for UI dropdowns)
CREATE POLICY parser_catalog_read 
ON utm_parser_catalog 
FOR SELECT 
TO authenticated 
USING (is_active = true);

CREATE POLICY source_tech_read 
ON utm_source_tech_catalog 
FOR SELECT 
TO authenticated 
USING (is_active = true);

-- ============================================
-- 5. Seed Data - Source Technologies
-- ============================================

INSERT INTO utm_source_tech_catalog (tech_id, tech_name, tech_aliases, vendor, category, description) VALUES
('ssis', 'SQL Server Integration Services', ARRAY['SSIS', 'SQL Server', 'SqlServer', 'Microsoft SSIS'], 'Microsoft', 'ETL', 'Microsoft SQL Server Integration Services'),
('oracle', 'Oracle Database', ARRAY['Oracle', 'PL/SQL', 'PLSQL', 'Oracle Database'], 'Oracle', 'Database', 'Oracle Database with PL/SQL stored procedures'),
('datastage', 'IBM DataStage', ARRAY['DataStage', 'IBM DataStage', 'DS', 'InfoSphere'], 'IBM', 'ETL', 'IBM InfoSphere DataStage'),
('informatica', 'Informatica PowerCenter', ARRAY['Informatica', 'PowerCenter', 'Informatica PowerCenter'], 'Informatica', 'ETL', 'Informatica PowerCenter'),
('talend', 'Talend Open Studio', ARRAY['Talend', 'Talend Open Studio', 'TOS'], 'Talend', 'ETL', 'Talend Open Studio / Enterprise'),
('pentaho', 'Pentaho Data Integration', ARRAY['Pentaho', 'Kettle', 'PDI', 'Pentaho DI'], 'Hitachi Vantara', 'ETL', 'Pentaho Data Integration (Kettle)'),
('sap-bods', 'SAP BusinessObjects Data Services', ARRAY['SAP BODS', 'BODS', 'SAP DS', 'BusinessObjects'], 'SAP', 'ETL', 'SAP BusinessObjects Data Services'),
('ab-initio', 'Ab Initio', ARRAY['Ab Initio', 'AbInitio'], 'Ab Initio', 'ETL', 'Ab Initio data processing platform'),
('teradata', 'Teradata', ARRAY['Teradata', 'TD'], 'Teradata', 'DataWarehouse', 'Teradata Database'),
('generic', 'Generic SQL', ARRAY['Generic', 'SQL', 'Unknown'], 'N/A', 'Generic', 'Generic SQL-based source')
ON CONFLICT (tech_id) DO NOTHING;

-- ============================================
-- 6. Seed Data - Parser Registry
-- ============================================

-- SSIS Parser (already implemented)
INSERT INTO utm_parser_catalog (parser_id, parser_name, tech_id, medulla_config, python_module, python_class, priority) VALUES
(
    'parser-ssis',
    'SSIS Intelligence Extractor',
    'ssis',
    '{
        "main_key": "data_flow_logic",
        "sql_keys": ["SqlCommand", "OpenRowset", "TableOrViewName"],
        "transformation_types": ["DerivedColumn", "Lookup", "Sort", "UnionAll", "ConditionalSplit"],
        "complexity_weights": {
            "oledbsource": 1,
            "oledbdestination": 1,
            "derivedcolumn": 2,
            "lookup": 3,
            "conditionalsplit": 4,
            "aggregate": 5,
            "merge": 5,
            "mergejoin": 5,
            "script": 8,
            "fuzzy": 10
        }
    }'::jsonb,
    'apps.api.services.knowledge_packet_service',
    'KnowledgePacketService._extract_ssis_intelligence',
    100
),

-- Oracle Parser (stub - to be implemented)
(
    'parser-oracle',
    'Oracle PL/SQL Extractor',
    'oracle',
    '{
        "main_key": "stored_procedures",
        "sql_keys": ["procedure_body", "function_body"],
        "transformation_types": ["CURSOR", "FUNCTION", "TRIGGER", "PACKAGE"],
        "complexity_weights": {
            "procedure": 5,
            "function": 4,
            "trigger": 6,
            "package": 10,
            "cursor": 3
        }
    }'::jsonb,
    'apps.api.services.knowledge_packet_service',
    'KnowledgePacketService._extract_oracle_intelligence',
    100
),

-- DataStage Parser (stub - to be implemented)
(
    'parser-datastage',
    'IBM DataStage Extractor',
    'datastage',
    '{
        "main_key": "stages",
        "sql_keys": ["sql_query", "user_sql"],
        "transformation_types": ["Transformer", "Aggregator", "Join", "Lookup", "Sort"],
        "complexity_weights": {
            "oracleconnectorpx": 2,
            "odbcconnector": 2,
            "transformer": 3,
            "aggregator": 4,
            "join": 4,
            "lookup": 3,
            "sort": 2
        }
    }'::jsonb,
    'apps.api.services.knowledge_packet_service',
    'KnowledgePacketService._extract_datastage_intelligence',
    100
),

-- Informatica Parser (stub - to be implemented)
(
    'parser-informatica',
    'Informatica PowerCenter Extractor',
    'informatica',
    '{
        "main_key": "transformations",
        "sql_keys": ["sql_override", "user_defined_sql"],
        "transformation_types": ["Expression", "Aggregator", "Lookup", "Router", "Joiner"],
        "complexity_weights": {
            "source": 1,
            "target": 1,
            "expression": 2,
            "aggregator": 4,
            "lookup": 3,
            "router": 3,
            "joiner": 4,
            "sorter": 2
        }
    }'::jsonb,
    'apps.api.services.knowledge_packet_service',
    'KnowledgePacketService._extract_informatica_intelligence',
    100
),

-- Generic Parser (fallback)
(
    'parser-generic',
    'Generic Intelligence Extractor',
    'generic',
    '{
        "main_key": "components",
        "sql_keys": ["sql_query", "query", "sql_command", "source_query"],
        "transformation_types": ["UNKNOWN"],
        "complexity_weights": {
            "default": 2
        }
    }'::jsonb,
    'apps.api.services.knowledge_packet_service',
    'KnowledgePacketService._extract_generic_intelligence',
    999
)
ON CONFLICT (parser_id) DO NOTHING;

-- ============================================
-- 7. Helper Functions
-- ============================================

-- Function: Resolve parser by source_tech
CREATE OR REPLACE FUNCTION resolve_parser_by_tech(p_source_tech TEXT)
RETURNS TABLE (
    parser_id TEXT,
    parser_name TEXT,
    medulla_config JSONB,
    python_module TEXT,
    python_class TEXT
)
LANGUAGE sql
STABLE
AS $$
    SELECT 
        p.parser_id,
        p.parser_name,
        p.medulla_config,
        p.python_module,
        p.python_class
    FROM utm_parser_catalog p
    INNER JOIN utm_source_tech_catalog t ON p.tech_id = t.tech_id
    WHERE t.is_active = true
    AND p.is_active = true
    AND (
        UPPER(p_source_tech) = ANY(
            SELECT UPPER(unnest(t.tech_aliases))
        )
    )
    ORDER BY p.priority ASC
    LIMIT 1;
$$;

-- Function: List all supported technologies
CREATE OR REPLACE FUNCTION list_supported_technologies()
RETURNS TABLE (
    tech_id TEXT,
    tech_name TEXT,
    tech_aliases TEXT[],
    vendor TEXT,
    has_parser BOOLEAN
)
LANGUAGE sql
STABLE
AS $$
    SELECT 
        t.tech_id,
        t.tech_name,
        t.tech_aliases,
        t.vendor,
        EXISTS(
            SELECT 1 FROM utm_parser_catalog p 
            WHERE p.tech_id = t.tech_id AND p.is_active = true
        ) as has_parser
    FROM utm_source_tech_catalog t
    WHERE t.is_active = true
    ORDER BY t.tech_name;
$$;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION resolve_parser_by_tech(TEXT) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION list_supported_technologies() TO authenticated, service_role;

-- ============================================
-- 8. Verification Queries
-- ============================================

-- Verify technologies
SELECT * FROM list_supported_technologies();

-- Verify parsers
SELECT 
    p.parser_id,
    p.parser_name,
    t.tech_name,
    p.is_active
FROM utm_parser_catalog p
INNER JOIN utm_source_tech_catalog t ON p.tech_id = t.tech_id
ORDER BY p.priority;

-- Test resolver
SELECT * FROM resolve_parser_by_tech('SSIS');
SELECT * FROM resolve_parser_by_tech('Oracle');
SELECT * FROM resolve_parser_by_tech('DataStage');

-- ============================================
-- 9. Comments
-- ============================================

COMMENT ON TABLE utm_source_tech_catalog IS 
'Global catalog of supported source technologies (like utm_agent_catalog for parsers)';

COMMENT ON TABLE utm_parser_catalog IS 
'Registry of intelligence extractors for different source technologies. Enables Zero-Hardcode extraction strategy.';

COMMENT ON COLUMN utm_parser_catalog.medulla_config IS 
'JSONB configuration defining medulla structure for this technology. Enables data-driven extraction without hardcoded if/else.';

COMMENT ON FUNCTION resolve_parser_by_tech(TEXT) IS 
'Resolves parser configuration by source technology name (case-insensitive, supports aliases)';

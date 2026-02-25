-- =========================================================================
-- Migration: v4.1_restore_essential_tables.sql
-- Description: Restores tables that were accidentally dropped in v4.0.
--              These tables are actively used by the Triage and Refinement 
--              analysis APIs (/quality and /tables/summary endpoints).
-- Date: 2026-02-24
-- =========================================================================

-- ================================================================
-- 1. Restore utm_asset_columns
-- ================================================================

-- The conflicting index was removed.
CREATE TABLE IF NOT EXISTS utm_asset_columns (
    column_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id            UUID NOT NULL REFERENCES utm_objects(object_id) ON DELETE CASCADE,
    project_id          UUID NOT NULL REFERENCES utm_projects(project_id) ON DELETE CASCADE,
    column_name         TEXT NOT NULL,
    column_position     INTEGER,
    
    data_type           TEXT,
    inferred_type       TEXT,
    max_length          INTEGER,
    precision_scale     TEXT,
    
    distinct_count      BIGINT,
    cardinality_ratio   NUMERIC(5,4),
    null_count          BIGINT,
    null_percentage     NUMERIC(5,2),
    
    sample_values       JSONB,
    min_value           TEXT,
    max_value           TEXT,
    
    is_pii              BOOLEAN DEFAULT FALSE,
    pii_category        TEXT,
    pii_confidence      NUMERIC(3,2),
    pii_pattern         TEXT,
    
    is_primary_key      BOOLEAN DEFAULT FALSE,
    is_foreign_key      BOOLEAN DEFAULT FALSE,
    is_nullable         BOOLEAN DEFAULT TRUE,
    is_indexed          BOOLEAN DEFAULT FALSE,
    
    partition_candidate BOOLEAN DEFAULT FALSE,
    partition_score     NUMERIC(3,2),
    partition_reason    TEXT,
    
    analysis_timestamp  TIMESTAMPTZ DEFAULT NOW(),
    analysis_version    TEXT DEFAULT 'v1.0',
    raw_metadata        JSONB DEFAULT '{}',
    
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT utm_asset_columns_unique_per_asset UNIQUE (asset_id, column_name)
);

CREATE INDEX IF NOT EXISTS idx_asset_columns_asset ON utm_asset_columns(asset_id);
CREATE INDEX IF NOT EXISTS idx_asset_columns_project ON utm_asset_columns(project_id);
CREATE INDEX IF NOT EXISTS idx_asset_columns_pii ON utm_asset_columns(is_pii) WHERE is_pii = TRUE;
CREATE INDEX IF NOT EXISTS idx_asset_columns_partition ON utm_asset_columns(partition_candidate) WHERE partition_candidate = TRUE;

ALTER TABLE utm_asset_columns ENABLE ROW LEVEL SECURITY;

CREATE OR REPLACE FUNCTION update_utm_asset_columns_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_utm_asset_columns_updated_at
    BEFORE UPDATE ON utm_asset_columns
    FOR EACH ROW
    EXECUTE FUNCTION update_utm_asset_columns_timestamp();

-- ================================================================
-- 2. Restore utm_table_impacts
-- ================================================================

CREATE TABLE IF NOT EXISTS utm_table_impacts (
    impact_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES utm_tenants(tenant_id) ON DELETE CASCADE,
    project_id      UUID NOT NULL REFERENCES utm_projects(project_id) ON DELETE CASCADE,
    
    schema_name     TEXT,
    table_name      TEXT NOT NULL,
    full_name       TEXT GENERATED ALWAYS AS (
                        COALESCE(schema_name || '.', '') || table_name
                    ) STORED,
    
    asset_id        UUID REFERENCES utm_objects(object_id) ON DELETE CASCADE,
    asset_name      TEXT NOT NULL,
    
    operation       TEXT NOT NULL CHECK (operation IN ('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'MERGE', 'TRUNCATE', 'UNKNOWN')),
    access_pattern  TEXT CHECK (access_pattern IN ('FULL_LOAD', 'INCREMENTAL', 'LOOKUP', 'UPSERT', 'SCD')),
    
    is_source       BOOLEAN DEFAULT FALSE,
    is_target       BOOLEAN DEFAULT FALSE,
    
    sql_statement   TEXT,
    columns_affected TEXT[],
    
    detected_at     TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE (project_id, asset_id, full_name, operation)
);

CREATE INDEX IF NOT EXISTS idx_impacts_by_table ON utm_table_impacts(project_id, full_name);
CREATE INDEX IF NOT EXISTS idx_impacts_by_asset ON utm_table_impacts(project_id, asset_id);
CREATE INDEX IF NOT EXISTS idx_impacts_operation ON utm_table_impacts(operation);

ALTER TABLE utm_table_impacts ENABLE ROW LEVEL SECURITY;

-- ================================================================
-- 3. Restore RPC Functions for Table Impacts
-- ================================================================

CREATE OR REPLACE FUNCTION get_table_summary(p_project_id UUID)
RETURNS TABLE (
    table_name TEXT,
    readers_count BIGINT,
    writers_count BIGINT,
    total_impacts BIGINT,
    operations TEXT[]
)
LANGUAGE sql
STABLE
AS $$
    SELECT 
        full_name as table_name,
        COUNT(*) FILTER (WHERE is_source = true) as readers_count,
        COUNT(*) FILTER (WHERE is_target = true) as writers_count,
        COUNT(*) as total_impacts,
        ARRAY_AGG(DISTINCT operation ORDER BY operation) as operations
    FROM utm_table_impacts
    WHERE project_id = p_project_id
    GROUP BY full_name
    ORDER BY total_impacts DESC, full_name;
$$;

CREATE OR REPLACE FUNCTION get_table_detail(p_project_id UUID, p_table_name TEXT)
RETURNS TABLE (
    asset_name TEXT,
    operation TEXT,
    access_pattern TEXT,
    is_source BOOLEAN,
    is_target BOOLEAN,
    sql_statement TEXT,
    columns_affected TEXT[]
)
LANGUAGE sql
STABLE
AS $$
    SELECT 
        asset_name,
        operation,
        access_pattern,
        is_source,
        is_target,
        sql_statement,
        columns_affected
    FROM utm_table_impacts
    WHERE project_id = p_project_id 
    AND full_name = p_table_name
    ORDER BY operation, asset_name;
$$;

CREATE OR REPLACE FUNCTION get_dependency_pairs(p_project_id UUID)
RETURNS TABLE (
    from_asset TEXT,
    to_asset TEXT,
    via_table TEXT
)
LANGUAGE sql
STABLE
AS $$
    SELECT DISTINCT
        writers.asset_name as from_asset,
        readers.asset_name as to_asset,
        writers.full_name as via_table
    FROM utm_table_impacts writers
    INNER JOIN utm_table_impacts readers 
        ON writers.project_id = readers.project_id
        AND writers.full_name = readers.full_name
        AND writers.asset_id != readers.asset_id
    WHERE writers.project_id = p_project_id
    AND writers.is_target = true
    AND readers.is_source = true
    ORDER BY via_table, from_asset, to_asset;
$$;

GRANT EXECUTE ON FUNCTION get_table_summary(UUID) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION get_table_detail(UUID, TEXT) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION get_dependency_pairs(UUID) TO authenticated, service_role;

SELECT 'Essential tables restored and functions created successfully' as status;

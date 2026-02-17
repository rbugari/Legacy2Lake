-- ============================================
-- Phase C: Table Impact Registry
-- Sprint 14 - v4.0
-- Date: 2026-02-15
-- ============================================

-- ============================================
-- 1. Create utm_table_impacts table
-- ============================================

CREATE TABLE IF NOT EXISTS utm_table_impacts (
    impact_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES utm_tenants(tenant_id) ON DELETE CASCADE,
    project_id      UUID NOT NULL REFERENCES utm_projects(project_id) ON DELETE CASCADE,
    
    -- The affected table
    schema_name     TEXT,
    table_name      TEXT NOT NULL,
    full_name       TEXT GENERATED ALWAYS AS (
                        COALESCE(schema_name || '.', '') || table_name
                    ) STORED,
    
    -- The asset that touches it
    asset_id        UUID REFERENCES utm_objects(object_id) ON DELETE CASCADE,
    asset_name      TEXT NOT NULL,
    
    -- Operation type
    operation       TEXT NOT NULL CHECK (operation IN ('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'MERGE', 'TRUNCATE', 'UNKNOWN')),
    access_pattern  TEXT CHECK (access_pattern IN ('FULL_LOAD', 'INCREMENTAL', 'LOOKUP', 'UPSERT', 'SCD')),
    
    -- Direction
    is_source       BOOLEAN DEFAULT FALSE,
    is_target       BOOLEAN DEFAULT FALSE,
    
    -- Details
    sql_statement   TEXT,
    columns_affected TEXT[],
    
    -- Metadata
    detected_at     TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE (project_id, asset_id, full_name, operation)
);

-- ============================================
-- 2. Create indexes for fast queries
-- ============================================

-- Query by table (most common: "show me all impacts on table X")
CREATE INDEX IF NOT EXISTS idx_impacts_by_table 
ON utm_table_impacts(project_id, full_name);

-- Query by asset (less common: "show me all tables touched by asset Y")
CREATE INDEX IF NOT EXISTS idx_impacts_by_asset 
ON utm_table_impacts(project_id, asset_id);

-- Tenant isolation
CREATE INDEX IF NOT EXISTS idx_impacts_tenant 
ON utm_table_impacts(tenant_id);

-- Query by operation type (for analytics)
CREATE INDEX IF NOT EXISTS idx_impacts_operation 
ON utm_table_impacts(operation);

-- Query readers vs writers
CREATE INDEX IF NOT EXISTS idx_impacts_direction 
ON utm_table_impacts(project_id, is_source, is_target);

-- ============================================
-- 3. Enable Row Level Security
-- ============================================

ALTER TABLE utm_table_impacts ENABLE ROW LEVEL SECURITY;

-- Policy: Service role can see all
CREATE POLICY table_impacts_service_role 
ON utm_table_impacts 
FOR ALL 
TO service_role 
USING (true);

-- Policy: Tenant isolation for authenticated users
CREATE POLICY table_impacts_tenant_isolation 
ON utm_table_impacts 
FOR ALL 
TO authenticated 
USING (
    tenant_id = COALESCE(
        (current_setting('app.current_tenant', true))::uuid,
        (current_setting('request.jwt.claims', true)::jsonb->>'tenant_id')::uuid
    )
);

-- ============================================
-- 4. Helper functions
-- ============================================

-- Function: Get table summary (readers/writers count)
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

-- Function: Get table detail (all impacts on specific table)
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

-- Function: Get dependency pairs (writer→reader relationships)
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

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION get_table_summary(UUID) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION get_table_detail(UUID, TEXT) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION get_dependency_pairs(UUID) TO authenticated, service_role;

-- ============================================
-- 5. Verification queries
-- ============================================

-- Verify table was created
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'utm_table_impacts'
ORDER BY ordinal_position;

-- Verify indexes were created
SELECT 
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'utm_table_impacts'
ORDER BY indexname;

-- Verify RLS policies
SELECT 
    schemaname,
    tablename,
    policyname,
    roles,
    cmd
FROM pg_policies
WHERE tablename = 'utm_table_impacts'
ORDER BY policyname;

-- Verify functions were created
SELECT 
    routine_name,
    routine_type,
    data_type as return_type
FROM information_schema.routines
WHERE routine_name IN ('get_table_summary', 'get_table_detail', 'get_dependency_pairs')
ORDER BY routine_name;

-- ============================================
-- 6. Comments
-- ============================================

COMMENT ON TABLE utm_table_impacts IS 
'Table-centric registry of all asset impacts on tables. Tracks which assets read/write which tables and how.';

COMMENT ON COLUMN utm_table_impacts.full_name IS 
'Generated column: schema.table or just table if no schema';

COMMENT ON COLUMN utm_table_impacts.operation IS 
'SQL operation type: SELECT, INSERT, UPDATE, DELETE, MERGE, TRUNCATE, UNKNOWN';

COMMENT ON COLUMN utm_table_impacts.access_pattern IS 
'High-level pattern: FULL_LOAD, INCREMENTAL, LOOKUP, UPSERT, SCD (Slowly Changing Dimension)';

COMMENT ON COLUMN utm_table_impacts.columns_affected IS 
'Array of column names affected by operation. NULL=all columns, []= unknown, [col1, col2]=specific columns';

COMMENT ON FUNCTION get_table_summary(UUID) IS 
'Returns summary of all tables in project with reader/writer counts';

COMMENT ON FUNCTION get_table_detail(UUID, TEXT) IS 
'Returns all impacts on a specific table';

COMMENT ON FUNCTION get_dependency_pairs(UUID) IS 
'Returns writer→reader dependency pairs for DAG construction';

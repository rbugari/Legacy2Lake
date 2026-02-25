-- ================================================================
-- Sprint 7 - DEPLOYMENT COMPLETE
-- Feature: Deep Forensic Triage (Column-Level Analysis)
-- Date: 2026-02-19
-- Estimated Time: ~5 seconds
-- ================================================================
-- This script combines:
--   1. Table creation (utm_asset_columns)
--   2. Indexes (7 indexes for performance)
--   3. RLS policies (multi-tenant isolation)
--   4. Permissions (authenticated + service_role)
--   5. Triggers (updated_at auto-update)
-- ================================================================

-- ================================================================
-- PART 1: TABLE CREATION (Idempotent - Safe to Re-run)
-- ================================================================

-- Clean slate: Drop ALL related objects (handles partial/failed deployments)
-- NOTE: unique_column_per_asset exists in utm_column_mappings - don't drop it!
-- We'll use a different constraint name for utm_asset_columns
DROP INDEX IF EXISTS idx_asset_columns_asset CASCADE;
DROP INDEX IF EXISTS idx_asset_columns_project CASCADE;
DROP INDEX IF EXISTS idx_asset_columns_pii CASCADE;
DROP INDEX IF EXISTS idx_asset_columns_pii_category CASCADE;
DROP INDEX IF EXISTS idx_asset_columns_partition CASCADE;
DROP INDEX IF EXISTS idx_asset_columns_cardinality CASCADE;
DROP INDEX IF EXISTS idx_asset_columns_nulls CASCADE;

-- Drop table last (after indexes are gone)
DROP TABLE IF EXISTS utm_asset_columns CASCADE;

-- Create fresh table
CREATE TABLE utm_asset_columns (
    column_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id            UUID NOT NULL REFERENCES utm_objects(object_id) ON DELETE CASCADE,
    project_id          UUID NOT NULL REFERENCES utm_projects(project_id) ON DELETE CASCADE,
    column_name         TEXT NOT NULL,
    column_position     INTEGER,  -- Ordinal position in table/file
    
    -- Data Type Information
    data_type           TEXT,  -- Native type (VARCHAR, INT, etc.)
    inferred_type       TEXT,  -- AI-inferred type (STRING, NUMERIC, DATE, etc.)
    max_length          INTEGER,
    precision_scale     TEXT,  -- e.g., "18,2" for DECIMAL
    
    -- Cardinality & Distribution
    distinct_count      BIGINT,  -- Number of unique values
    cardinality_ratio   NUMERIC(5,4),  -- distinct/total (0.0-1.0)
    null_count          BIGINT,  -- Number of nulls
    null_percentage     NUMERIC(5,2),  -- % of nulls (0-100)
    
    -- Sample Data
    sample_values       JSONB,  -- Array of 5-10 sample values
    min_value           TEXT,  -- Min value (as string for comparability)
    max_value           TEXT,  -- Max value
    
    -- PII Detection
    is_pii              BOOLEAN DEFAULT FALSE,
    pii_category        TEXT,  -- EMAIL, SSN, PHONE, NAME, ADDRESS, etc.
    pii_confidence      NUMERIC(3,2),  -- 0.0-1.0 confidence score
    pii_pattern         TEXT,  -- Regex pattern detected (optional)
    
    -- Business Intelligence
    is_primary_key      BOOLEAN DEFAULT FALSE,
    is_foreign_key      BOOLEAN DEFAULT FALSE,
    is_nullable         BOOLEAN DEFAULT TRUE,
    is_indexed          BOOLEAN DEFAULT FALSE,
    
    -- Partition Recommendations
    partition_candidate BOOLEAN DEFAULT FALSE,
    partition_score     NUMERIC(3,2),  -- 0.0-1.0 suitability score
    partition_reason    TEXT,  -- Why recommended (e.g., "High cardinality + Date type")
    
    -- Metadata
    analysis_timestamp  TIMESTAMPTZ DEFAULT NOW(),
    analysis_version    TEXT DEFAULT 'v1.0',  -- Profiler version
    raw_metadata        JSONB DEFAULT '{}',  -- Additional AI insights
    
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints (renamed to avoid collision with utm_column_mappings constraint)
    CONSTRAINT uq_asset_columns_asset_column UNIQUE (asset_id, column_name)
);

-- ================================================================
-- PART 2: INDEXES (Performance Optimization)
-- ================================================================

CREATE INDEX IF NOT EXISTS idx_asset_columns_asset ON utm_asset_columns(asset_id);
CREATE INDEX IF NOT EXISTS idx_asset_columns_project ON utm_asset_columns(project_id);
CREATE INDEX IF NOT EXISTS idx_asset_columns_pii ON utm_asset_columns(is_pii) WHERE is_pii = TRUE;
CREATE INDEX IF NOT EXISTS idx_asset_columns_pii_category ON utm_asset_columns(pii_category) WHERE pii_category IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_asset_columns_partition ON utm_asset_columns(partition_candidate) WHERE partition_candidate = TRUE;
CREATE INDEX IF NOT EXISTS idx_asset_columns_cardinality ON utm_asset_columns(cardinality_ratio);
CREATE INDEX IF NOT EXISTS idx_asset_columns_nulls ON utm_asset_columns(null_percentage);

-- ================================================================
-- PART 3: ROW-LEVEL SECURITY (Multi-Tenant Isolation)
-- ================================================================

ALTER TABLE utm_asset_columns ENABLE ROW LEVEL SECURITY;

-- Drop policy if exists (for re-runs)
DROP POLICY IF EXISTS tenant_column_isolation ON utm_asset_columns;

-- Create RLS policy
CREATE POLICY tenant_column_isolation ON utm_asset_columns
    USING (
        project_id IN (
            SELECT project_id 
            FROM utm_projects 
            WHERE tenant_id = current_setting('app.current_tenant', true)::uuid
        )
    );

-- ================================================================
-- PART 4: PERMISSIONS (Access Control)
-- ================================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON utm_asset_columns TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON utm_asset_columns TO service_role;
GRANT ALL ON utm_asset_columns TO postgres;

GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO service_role;

-- ================================================================
-- PART 5: TRIGGERS (Auto-Update Timestamps)
-- ================================================================

-- Drop existing trigger and function (for clean re-deployment)
DROP TRIGGER IF EXISTS trigger_utm_asset_columns_updated_at ON utm_asset_columns;
DROP FUNCTION IF EXISTS update_utm_asset_columns_timestamp() CASCADE;

-- Create trigger function
CREATE OR REPLACE FUNCTION update_utm_asset_columns_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
CREATE TRIGGER trigger_utm_asset_columns_updated_at
    BEFORE UPDATE ON utm_asset_columns
    FOR EACH ROW
    EXECUTE FUNCTION update_utm_asset_columns_timestamp();

-- ================================================================
-- PART 6: METADATA (Documentation)
-- ================================================================

COMMENT ON TABLE utm_asset_columns IS 'Sprint 7: Column-level profiling for Deep Forensic Triage (v4.0)';
COMMENT ON COLUMN utm_asset_columns.cardinality_ratio IS 'Ratio of distinct values to total rows (0.0-1.0)';
COMMENT ON COLUMN utm_asset_columns.pii_confidence IS 'AI confidence score for PII detection (0.0-1.0)';
COMMENT ON COLUMN utm_asset_columns.partition_score IS 'Suitability score for partitioning (0.0-1.0)';

-- ================================================================
-- DEPLOYMENT VERIFICATION
-- ================================================================

-- Check table exists
SELECT 
    'utm_asset_columns table created successfully' AS status,
    COUNT(*) AS index_count
FROM pg_indexes
WHERE tablename = 'utm_asset_columns';

-- Check RLS enabled
SELECT 
    tablename,
    CASE WHEN rowsecurity THEN '✅ RLS Enabled' ELSE '❌ RLS Disabled' END AS rls_status
FROM pg_tables
WHERE tablename = 'utm_asset_columns';

-- Check policies
SELECT 
    policyname,
    '✅ Policy Active' AS status
FROM pg_policies
WHERE tablename = 'utm_asset_columns';

-- ================================================================
-- SPRINT 7 DEPLOYMENT COMPLETE ✅
-- ================================================================
-- Next Steps:
--   1. Run Triage on project "fff" again
--   2. Agent A will populate utm_asset_columns with PII detection
--   3. Test Code Quality tab (/projects/{id}/quality)
--   4. Test PII Detection tab (/projects/{id}/pii-heatmap)
-- ================================================================

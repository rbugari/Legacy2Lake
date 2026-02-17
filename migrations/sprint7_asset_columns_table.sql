-- Migration: Sprint 7 - Deep Forensic Triage (Column-Level Analysis)
-- Purpose: Add utm_asset_columns table for field-level profiling
-- Date: 2026-02-11
-- Sprint: 7 (Feature: Deep Forensic Triage)

-- ================================================================
-- TABLE: utm_asset_columns
-- Purpose: Store column-level analysis metrics for each asset
-- Used by: Agent A (Column Profiling), Triage UI (Heatmaps)
-- ================================================================

CREATE TABLE IF NOT EXISTS utm_asset_columns (
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
    
    -- Constraints
    CONSTRAINT unique_column_per_asset UNIQUE (asset_id, column_name)
);

-- ================================================================
-- INDEXES
-- ================================================================

-- Fast lookup by asset
CREATE INDEX idx_asset_columns_asset ON utm_asset_columns(asset_id);

-- Fast lookup by project (for project-wide heatmaps)
CREATE INDEX idx_asset_columns_project ON utm_asset_columns(project_id);

-- PII detection queries
CREATE INDEX idx_asset_columns_pii ON utm_asset_columns(is_pii) WHERE is_pii = TRUE;
CREATE INDEX idx_asset_columns_pii_category ON utm_asset_columns(pii_category) WHERE pii_category IS NOT NULL;

-- Partition candidate queries
CREATE INDEX idx_asset_columns_partition ON utm_asset_columns(partition_candidate) WHERE partition_candidate = TRUE;

-- Cardinality analysis
CREATE INDEX idx_asset_columns_cardinality ON utm_asset_columns(cardinality_ratio);

-- Null analysis
CREATE INDEX idx_asset_columns_nulls ON utm_asset_columns(null_percentage);

-- ================================================================
-- ROW-LEVEL SECURITY (RLS)
-- ================================================================

-- Enable RLS on the table
ALTER TABLE utm_asset_columns ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see columns from their tenant's projects
CREATE POLICY tenant_column_isolation ON utm_asset_columns
    USING (
        project_id IN (
            SELECT project_id 
            FROM utm_projects 
            WHERE tenant_id = current_setting('app.current_tenant', true)::uuid
        )
    );

-- ================================================================
-- HELPER FUNCTIONS
-- ================================================================

-- Function: Update updated_at timestamp on row modification
CREATE OR REPLACE FUNCTION update_utm_asset_columns_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto-update updated_at
CREATE TRIGGER trigger_utm_asset_columns_updated_at
    BEFORE UPDATE ON utm_asset_columns
    FOR EACH ROW
    EXECUTE FUNCTION update_utm_asset_columns_timestamp();

-- ================================================================
-- SAMPLE QUERIES (For Testing)
-- ================================================================

-- Get all PII columns for a project
-- SELECT column_name, pii_category, pii_confidence, asset_id
-- FROM utm_asset_columns
-- WHERE project_id = '<project_uuid>' AND is_pii = TRUE
-- ORDER BY pii_confidence DESC;

-- Get partition candidates for an asset
-- SELECT column_name, partition_score, partition_reason
-- FROM utm_asset_columns
-- WHERE asset_id = '<asset_uuid>' AND partition_candidate = TRUE
-- ORDER BY partition_score DESC;

-- Get high-cardinality columns (potential issues)
-- SELECT column_name, distinct_count, cardinality_ratio
-- FROM utm_asset_columns
-- WHERE project_id = '<project_uuid>' AND cardinality_ratio > 0.95
-- ORDER BY distinct_count DESC;

-- Get columns with high null percentage (data quality issues)
-- SELECT column_name, null_percentage, null_count
-- FROM utm_asset_columns
-- WHERE project_id = '<project_uuid>' AND null_percentage > 50.0
-- ORDER BY null_percentage DESC;

-- ================================================================
-- ROLLBACK (If needed)
-- ================================================================

-- DROP TRIGGER IF EXISTS trigger_utm_asset_columns_updated_at ON utm_asset_columns;
-- DROP FUNCTION IF EXISTS update_utm_asset_columns_timestamp();
-- DROP TABLE IF EXISTS utm_asset_columns CASCADE;

-- ================================================================
-- MIGRATION COMPLETE
-- ================================================================

COMMENT ON TABLE utm_asset_columns IS 'Sprint 7: Column-level profiling for Deep Forensic Triage';
COMMENT ON COLUMN utm_asset_columns.cardinality_ratio IS 'Ratio of distinct values to total rows (0.0-1.0)';
COMMENT ON COLUMN utm_asset_columns.pii_confidence IS 'AI confidence score for PII detection (0.0-1.0)';
COMMENT ON COLUMN utm_asset_columns.partition_score IS 'Suitability score for partitioning (0.0-1.0)';

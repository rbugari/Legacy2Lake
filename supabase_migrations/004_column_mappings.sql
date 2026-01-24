-- Migration: Column-level mapping table
-- Phase A - Column Mapping Engine
-- Stores source → target column mappings with transformation rules

CREATE TABLE utm_column_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES utm_objects(object_id) ON DELETE CASCADE,
    source_column VARCHAR(255) NOT NULL,
    source_datatype VARCHAR(100),
    target_column VARCHAR(255),
    target_datatype VARCHAR(100),
    transformation_rule TEXT,  -- 'CAST', 'TRIM', 'COALESCE', or custom SQL expression
    is_pii BOOLEAN DEFAULT FALSE,
    is_nullable BOOLEAN DEFAULT TRUE,
    default_value TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure unique column mappings per asset
    CONSTRAINT unique_column_per_asset UNIQUE (asset_id, source_column)
);

-- Indices for performance
CREATE INDEX idx_column_mappings_asset ON utm_column_mappings(asset_id);
CREATE INDEX idx_column_mappings_pii ON utm_column_mappings(is_pii) WHERE is_pii = TRUE;

-- RLS policies
ALTER TABLE utm_column_mappings ENABLE ROW LEVEL SECURITY;

CREATE POLICY column_mappings_select ON utm_column_mappings
    FOR SELECT USING (true);

CREATE POLICY column_mappings_insert ON utm_column_mappings
    FOR INSERT WITH CHECK (true);

CREATE POLICY column_mappings_update ON utm_column_mappings
    FOR UPDATE USING (true);

CREATE POLICY column_mappings_delete ON utm_column_mappings
    FOR DELETE USING (true);

-- Documentation
COMMENT ON TABLE utm_column_mappings IS 'Stores column-level mapping from source to target with transformation rules';
COMMENT ON COLUMN utm_column_mappings.transformation_rule IS 'Transformation type: CAST, TRIM, COALESCE, or custom SQL';
COMMENT ON COLUMN utm_column_mappings.is_pii IS 'Flag for personally identifiable information';

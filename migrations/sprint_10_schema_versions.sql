-- Sprint 10: Schema Evolution - Database Migration
-- Creates utm_schema_versions table for tracking schema changes over time

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create utm_schema_versions table
CREATE TABLE IF NOT EXISTS utm_schema_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES utm_tenants(tenant_id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES utm_projects(project_id) ON DELETE CASCADE,
    asset_id UUID NOT NULL REFERENCES utm_objects(object_id) ON DELETE CASCADE,
    version_number INT NOT NULL CHECK (version_number > 0),
    schema_snapshot JSONB NOT NULL,
    changes_from_previous JSONB,
    breaking_changes BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id),
    
    -- Constraints
    UNIQUE(tenant_id, project_id, asset_id, version_number),
    CHECK (schema_snapshot IS NOT NULL AND jsonb_typeof(schema_snapshot) = 'object')
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_utm_schema_versions_tenant_project 
    ON utm_schema_versions(tenant_id, project_id);

CREATE INDEX IF NOT EXISTS idx_utm_schema_versions_asset 
    ON utm_schema_versions(asset_id);

CREATE INDEX IF NOT EXISTS idx_utm_schema_versions_version 
    ON utm_schema_versions(asset_id, version_number DESC);

CREATE INDEX IF NOT EXISTS idx_utm_schema_versions_breaking 
    ON utm_schema_versions(asset_id, breaking_changes) 
    WHERE breaking_changes = TRUE;

CREATE INDEX IF NOT EXISTS idx_utm_schema_versions_created 
    ON utm_schema_versions(created_at DESC);

-- GIN index for JSONB queries on schema_snapshot
CREATE INDEX IF NOT EXISTS idx_utm_schema_versions_schema_snapshot 
    ON utm_schema_versions USING GIN (schema_snapshot);

-- GIN index for JSONB queries on changes
CREATE INDEX IF NOT EXISTS idx_utm_schema_versions_changes 
    ON utm_schema_versions USING GIN (changes_from_previous);

-- Add comments
COMMENT ON TABLE utm_schema_versions IS 
    'Sprint 10: Tracks schema version history for data assets, enabling schema evolution and migration planning';

COMMENT ON COLUMN utm_schema_versions.version_number IS 
    'Sequential version number for this asset (starts at 1)';

COMMENT ON COLUMN utm_schema_versions.schema_snapshot IS 
    'Complete schema snapshot (columns, types, constraints) at this version';

COMMENT ON COLUMN utm_schema_versions.changes_from_previous IS 
    'Array of changes from previous version (added, removed, modified columns)';

COMMENT ON COLUMN utm_schema_versions.breaking_changes IS 
    'TRUE if this version contains breaking changes (removals, incompatible type changes)';

-- Enable Row Level Security (RLS)
ALTER TABLE utm_schema_versions ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only see schema versions for their tenant
CREATE POLICY utm_schema_versions_tenant_isolation ON utm_schema_versions
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);

-- RLS Policy: Service role can access all
CREATE POLICY utm_schema_versions_service_role ON utm_schema_versions
    FOR ALL
    USING (current_setting('request.jwt.claims', TRUE)::json->>'role' = 'service_role');

-- Grant permissions
GRANT SELECT, INSERT ON utm_schema_versions TO authenticated;
GRANT ALL ON utm_schema_versions TO service_role;

-- Create function to auto-detect schema changes
CREATE OR REPLACE FUNCTION detect_schema_changes()
RETURNS TRIGGER AS $$
DECLARE
    v_previous_version RECORD;
    v_changes JSONB;
BEGIN
    -- Only on INSERT
    IF TG_OP = 'INSERT' AND NEW.version_number > 1 THEN
        -- Get previous version
        SELECT schema_snapshot INTO v_previous_version
        FROM utm_schema_versions
        WHERE asset_id = NEW.asset_id
          AND version_number = NEW.version_number - 1;
        
        IF FOUND THEN
            -- Note: Actual change detection happens in Python service
            -- This is just a placeholder for future enhancements
            NEW.changes_from_previous = jsonb_build_array();
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
CREATE TRIGGER trigger_detect_schema_changes
    BEFORE INSERT ON utm_schema_versions
    FOR EACH ROW
    EXECUTE FUNCTION detect_schema_changes();

-- Create view for latest schema versions
CREATE OR REPLACE VIEW utm_schema_versions_latest AS
SELECT DISTINCT ON (asset_id)
    id,
    tenant_id,
    project_id,
    asset_id,
    version_number,
    schema_snapshot,
    changes_from_previous,
    breaking_changes,
    created_at,
    created_by
FROM utm_schema_versions
ORDER BY asset_id, version_number DESC;

COMMENT ON VIEW utm_schema_versions_latest IS 
    'Shows only the latest schema version for each asset';

-- Grant view access
GRANT SELECT ON utm_schema_versions_latest TO authenticated;
GRANT ALL ON utm_schema_versions_latest TO service_role;

-- Success message
DO $$ 
BEGIN 
    RAISE NOTICE 'Sprint 10 migration completed: utm_schema_versions table created';
END $$;

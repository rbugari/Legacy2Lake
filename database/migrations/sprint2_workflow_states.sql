-- Migration: Create utm_workflow_states table
-- Sprint 2: Workflow State Management
-- Date: 2026-02-11

-- Create utm_workflow_states table
CREATE TABLE IF NOT EXISTS utm_workflow_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_uuid UUID NOT NULL REFERENCES utm_projects(project_uuid) ON DELETE CASCADE,
    tenant_id UUID REFERENCES utm_tenants(tenant_id) ON DELETE CASCADE,
    
    -- Current workflow status
    status TEXT NOT NULL DEFAULT 'PENDING',
    -- PENDING, RUNNING, PAUSED, COMPLETED, FAILED, CANCELLED
    
    -- Complete state data (JSONB for flexibility)
    state_data JSONB NOT NULL DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_status CHECK (
        status IN ('PENDING', 'RUNNING', 'PAUSED', 'COMPLETED', 'FAILED', 'CANCELLED')
    )
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_workflow_states_project ON utm_workflow_states(project_uuid);
CREATE INDEX IF NOT EXISTS idx_workflow_states_tenant ON utm_workflow_states(tenant_id);
CREATE INDEX IF NOT EXISTS idx_workflow_states_status ON utm_workflow_states(status);
CREATE INDEX IF NOT EXISTS idx_workflow_states_updated ON utm_workflow_states(updated_at DESC);

-- Add unique constraint (one active workflow per project)
CREATE UNIQUE INDEX IF NOT EXISTS idx_workflow_states_unique_project 
    ON utm_workflow_states(project_uuid)
    WHERE status IN ('PENDING', 'RUNNING', 'PAUSED');

-- Enable RLS (Row Level Security)
ALTER TABLE utm_workflow_states ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only see workflows for their tenant
CREATE POLICY tenant_isolation ON utm_workflow_states
    FOR ALL
    USING (
        tenant_id = current_setting('app.current_tenant_id')::UUID
        OR tenant_id IS NULL
    );

-- Function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_workflow_states_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at
CREATE TRIGGER workflow_states_updated_at
    BEFORE UPDATE ON utm_workflow_states
    FOR EACH ROW
    EXECUTE FUNCTION update_workflow_states_timestamp();

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON utm_workflow_states TO authenticated;
GRANT SELECT ON utm_workflow_states TO anon;

-- Add comment
COMMENT ON TABLE utm_workflow_states IS 
    'Sprint 2: Stores workflow execution state for pause/resume capability and progress tracking';

COMMENT ON COLUMN utm_workflow_states.state_data IS 
    'Complete workflow state including packages, phases, checkpoints, and metrics';

-- Sample query to check workflow status
-- SELECT 
--     project_uuid,
--     status,
--     state_data->>'current_phase_name' as current_phase,
--     (state_data->>'processed_packages')::int as processed,
--     (state_data->>'total_packages')::int as total,
--     ((state_data->>'processed_packages')::float / (state_data->>'total_packages')::float * 100) as progress_pct,
--     updated_at
-- FROM utm_workflow_states
-- WHERE tenant_id = 'your-tenant-id'
-- ORDER BY updated_at DESC;

-- Sprint 3: Gap & Decision Workspace
-- Creates utm_project_gaps table for formal gap tracking.
--
-- Rollback: DROP TABLE IF EXISTS utm_project_gaps;

CREATE TABLE IF NOT EXISTS utm_project_gaps (
    gap_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id         UUID NOT NULL REFERENCES utm_tenants(tenant_id) ON DELETE CASCADE,
    project_id        UUID NOT NULL REFERENCES utm_projects(project_id) ON DELETE CASCADE,
    asset_id          UUID REFERENCES utm_objects(object_id) ON DELETE SET NULL,

    source_stage      TEXT NOT NULL DEFAULT 'discovery'  -- discovery | triage | refinement | governance
        CHECK (source_stage IN ('discovery','triage','refinement','governance','manual')),

    category          TEXT NOT NULL DEFAULT 'other'
        CHECK (category IN (
            'schema','mappings','business_rules','orchestration',
            'data_quality','compliance','target_architecture','other'
        )),

    severity          TEXT NOT NULL DEFAULT 'MEDIUM'
        CHECK (severity IN ('CRITICAL','HIGH','MEDIUM','LOW')),

    title             TEXT NOT NULL,
    description       TEXT,
    why_it_matters    TEXT,
    recommended_owner TEXT,

    resolution_status TEXT NOT NULL DEFAULT 'OPEN'
        CHECK (resolution_status IN ('OPEN','IN_REVIEW','RESOLVED','WONT_FIX')),

    decision_note     TEXT,

    created_by        UUID REFERENCES utm_users(user_id) ON DELETE SET NULL,
    resolved_by       UUID REFERENCES utm_users(user_id) ON DELETE SET NULL,

    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at       TIMESTAMPTZ
);

COMMENT ON TABLE utm_project_gaps IS
    'Sprint 3 - Gap & Decision Workspace: formal gap items derived from project signals or manually created.';

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_utm_project_gaps_tenant_project
    ON utm_project_gaps (tenant_id, project_id);

CREATE INDEX IF NOT EXISTS idx_utm_project_gaps_tenant_status
    ON utm_project_gaps (tenant_id, resolution_status);

CREATE INDEX IF NOT EXISTS idx_utm_project_gaps_tenant_severity
    ON utm_project_gaps (tenant_id, severity);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION fn_utm_project_gaps_set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_utm_project_gaps_updated_at ON utm_project_gaps;
CREATE TRIGGER trg_utm_project_gaps_updated_at
    BEFORE UPDATE ON utm_project_gaps
    FOR EACH ROW EXECUTE FUNCTION fn_utm_project_gaps_set_updated_at();

-- Row Level Security
ALTER TABLE utm_project_gaps ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "gap_tenant_isolation" ON utm_project_gaps;
CREATE POLICY "gap_tenant_isolation"
    ON utm_project_gaps
    USING (tenant_id = current_setting('app.tenant_id', TRUE)::UUID);

-- Service role bypass (for backend operations)
GRANT ALL ON utm_project_gaps TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON utm_project_gaps TO authenticated;

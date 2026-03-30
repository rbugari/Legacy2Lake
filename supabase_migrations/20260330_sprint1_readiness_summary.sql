-- Sprint 1: Readiness + Confidence Model
-- Adds readiness_summary JSONB column to utm_projects.
-- No new table required — fastest path, low migration risk.
--
-- Rollback: ALTER TABLE utm_projects DROP COLUMN IF EXISTS readiness_summary;

ALTER TABLE utm_projects
    ADD COLUMN IF NOT EXISTS readiness_summary JSONB DEFAULT NULL;

COMMENT ON COLUMN utm_projects.readiness_summary IS
    'Sprint 1 - Readiness + Confidence Model: persisted readiness payload '
    'with status, confidence_score, top_reasons, blockers, '
    'recommended_next_action, source_signals, computed_at.';

-- Index for quick lookup of projects by readiness status (used in dashboards)
CREATE INDEX IF NOT EXISTS idx_utm_projects_readiness_status
    ON utm_projects ((readiness_summary->>'status'))
    WHERE readiness_summary IS NOT NULL;

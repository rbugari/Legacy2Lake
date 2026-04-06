-- ================================================================
-- Fix: Grant permissions for utm_evidence_items
-- Purpose: Allow evidence persistence and evidence review endpoints to access the table
-- ================================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON utm_evidence_items TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON utm_evidence_items TO service_role;
GRANT ALL ON utm_evidence_items TO postgres;

COMMENT ON TABLE utm_evidence_items IS 'Permissions granted for evidence persistence and review';
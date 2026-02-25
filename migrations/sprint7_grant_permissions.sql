-- ================================================================
-- Sprint 7: Grant Permissions for utm_asset_columns
-- Purpose: Ensure proper access for column profiling feature
-- Date: 2026-02-19
-- ================================================================

-- Grant access to authenticated users (RLS remains enabled for tenant isolation)
GRANT SELECT, INSERT, UPDATE, DELETE ON utm_asset_columns TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON utm_asset_columns TO service_role;

-- Grant usage on sequences (if any)
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO service_role;

-- For Postgres direct access (admin operations)
GRANT ALL ON utm_asset_columns TO postgres;

COMMENT ON TABLE utm_asset_columns IS 'Sprint 7: Permissions granted - RLS enabled for multi-tenant isolation';

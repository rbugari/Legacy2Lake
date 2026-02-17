-- ============================================
-- Phase B: Parser Catalog RLS Fix
-- Sprint 14 - v4.0
-- Date: 2026-02-16
-- ============================================
--
-- Fix: RLS policies blocking service_role access
-- These tables are GLOBAL catalogs (like utm_agent_catalog)
--
-- ============================================

-- Drop existing policies
DROP POLICY IF EXISTS parser_catalog_service_role ON utm_parser_catalog;
DROP POLICY IF EXISTS source_tech_service_role ON utm_source_tech_catalog;
DROP POLICY IF EXISTS parser_catalog_read ON utm_parser_catalog;
DROP POLICY IF EXISTS source_tech_read ON utm_source_tech_catalog;

-- Disable RLS for service_role (these are global catalogs)
-- Service role needs unrestricted access for resolution functions

ALTER TABLE utm_source_tech_catalog DISABLE ROW LEVEL SECURITY;
ALTER TABLE utm_parser_catalog DISABLE ROW LEVEL SECURITY;

-- Alternative: If you want to keep RLS enabled, use this instead:
-- CREATE POLICY parser_catalog_all ON utm_parser_catalog FOR ALL USING (true);
-- CREATE POLICY source_tech_all ON utm_source_tech_catalog FOR ALL USING (true);

-- Verify permissions
GRANT SELECT ON utm_source_tech_catalog TO authenticated, service_role, anon;
GRANT SELECT ON utm_parser_catalog TO authenticated, service_role, anon;

-- Verify functions
GRANT EXECUTE ON FUNCTION resolve_parser_by_tech(TEXT) TO authenticated, service_role, anon;
GRANT EXECUTE ON FUNCTION list_supported_technologies() TO authenticated, service_role, anon;

-- Test queries
SELECT 'Parser Catalog RLS Fix Applied' as status;
SELECT * FROM list_supported_technologies();
SELECT * FROM resolve_parser_by_tech('SSIS');

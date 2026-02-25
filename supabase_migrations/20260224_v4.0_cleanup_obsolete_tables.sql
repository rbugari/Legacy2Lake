-- =========================================================================
-- Migration: v4.0_cleanup_obsolete_tables.sql
-- Description: Drops tables that are obsolete, unused, or have been 
--              replaced by new v3.9/v4.0 architectures.
-- Date: 2026-02-24
-- =========================================================================

-- Legacy V3 Tables (Unused in V4.0 Codebase)
DROP TABLE IF EXISTS utm_anomaly_reports CASCADE;
-- REMOVED: utm_asset_columns (Actively used by Quality/Refinement tabs)
DROP TABLE IF EXISTS utm_code_validations CASCADE;
DROP TABLE IF EXISTS utm_function_registry CASCADE;
DROP TABLE IF EXISTS utm_global_config CASCADE;
DROP TABLE IF EXISTS utm_origin_analysis_columns CASCADE;
DROP TABLE IF EXISTS utm_quality_metrics CASCADE;
DROP TABLE IF EXISTS utm_quality_reports CASCADE;
DROP TABLE IF EXISTS utm_quality_rules CASCADE;
DROP TABLE IF EXISTS utm_schema_versions CASCADE;
DROP TABLE IF EXISTS utm_stages CASCADE;
DROP TABLE IF EXISTS utm_supported_techs CASCADE;
-- REMOVED: utm_table_impacts (Actively used by Quality/Refinement tabs)
DROP TABLE IF EXISTS utm_vault CASCADE;
DROP TABLE IF EXISTS utm_workflow_states CASCADE;

-- Tables Replaced in V3.9 / V4.0
DROP TABLE IF EXISTS utm_clients CASCADE;         -- Replaced by utm_tenants
DROP TABLE IF EXISTS utm_file_storage CASCADE;    -- Replaced by utm_file_inventory
DROP TABLE IF EXISTS utm_invitations CASCADE;     -- Replaced by utm_user_invitations
DROP TABLE IF EXISTS utm_agents CASCADE;          -- Replaced by utm_agent_catalog / matrix

-- Analytics tables defined in documentation but never used in code yet
-- Commented out just in case there's an external data warehouse using them
-- DROP TABLE IF EXISTS utm_generation_outcomes CASCADE;
-- DROP TABLE IF EXISTS utm_user_overrides CASCADE;

SELECT 'Cleanup of obsolete tables completed successfully.' as status;

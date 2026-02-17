-- ================================================================
-- Fix Permissions for Sprint Tables (Quality Rules, etc.)
-- ================================================================
-- This script grants necessary permissions to Sprint 11+ tables
-- that are causing "permission denied" errors during code generation
-- ================================================================

-- Sprint 11: Data Quality Tables
DO $$ 
BEGIN
    -- utm_quality_rules
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'utm_quality_rules') THEN
        ALTER TABLE utm_quality_rules DISABLE ROW LEVEL SECURITY;
        GRANT ALL ON utm_quality_rules TO authenticated;
        GRANT ALL ON utm_quality_rules TO anon;
        GRANT ALL ON utm_quality_rules TO service_role;
        GRANT ALL ON utm_quality_rules TO postgres;
        RAISE NOTICE 'Granted permissions on utm_quality_rules';
    END IF;
    
    -- utm_quality_reports
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'utm_quality_reports') THEN
        ALTER TABLE utm_quality_reports DISABLE ROW LEVEL SECURITY;
        GRANT ALL ON utm_quality_reports TO authenticated;
        GRANT ALL ON utm_quality_reports TO anon;
        GRANT ALL ON utm_quality_reports TO service_role;
        GRANT ALL ON utm_quality_reports TO postgres;
        RAISE NOTICE 'Granted permissions on utm_quality_reports';
    END IF;
    
    -- utm_quality_metrics
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'utm_quality_metrics') THEN
        ALTER TABLE utm_quality_metrics DISABLE ROW LEVEL SECURITY;
        GRANT ALL ON utm_quality_metrics TO authenticated;
        GRANT ALL ON utm_quality_metrics TO anon;
        GRANT ALL ON utm_quality_metrics TO service_role;
        GRANT ALL ON utm_quality_metrics TO postgres;
        RAISE NOTICE 'Granted permissions on utm_quality_metrics';
    END IF;
    
    -- utm_anomaly_reports
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'utm_anomaly_reports') THEN
        ALTER TABLE utm_anomaly_reports DISABLE ROW LEVEL SECURITY;
        GRANT ALL ON utm_anomaly_reports TO authenticated;
        GRANT ALL ON utm_anomaly_reports TO anon;
        GRANT ALL ON utm_anomaly_reports TO service_role;
        GRANT ALL ON utm_anomaly_reports TO postgres;
        RAISE NOTICE 'Granted permissions on utm_anomaly_reports';
    END IF;
END $$;

-- Sprint 10: Schema Evolution Tables (if they exist)
DO $$ 
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'utm_schema_versions') THEN
        ALTER TABLE utm_schema_versions DISABLE ROW LEVEL SECURITY;
        GRANT ALL ON utm_schema_versions TO authenticated;
        GRANT ALL ON utm_schema_versions TO anon;
        GRANT ALL ON utm_schema_versions TO service_role;
        GRANT ALL ON utm_schema_versions TO postgres;
    END IF;
END $$;

-- Sprint 12: Performance Tables (if they exist)
DO $$ 
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'utm_query_cache') THEN
        ALTER TABLE utm_query_cache DISABLE ROW LEVEL SECURITY;
        GRANT ALL ON utm_query_cache TO authenticated;
        GRANT ALL ON utm_query_cache TO anon;
        GRANT ALL ON utm_query_cache TO service_role;
        GRANT ALL ON utm_query_cache TO postgres;
    END IF;
END $$;

COMMENT ON TABLE utm_quality_rules IS 'Permissions granted for Sprint 11+ migration testing';

-- Summary of tables processed:
-- ✅ Sprint 11: utm_quality_rules, utm_quality_reports, utm_quality_metrics, utm_anomaly_reports
-- ✅ Sprint 10: utm_schema_versions (conditional)
-- ✅ Sprint 12: utm_query_cache (conditional)

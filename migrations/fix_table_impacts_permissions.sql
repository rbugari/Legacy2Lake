-- ================================================================
-- Fix: Grant permissions for utm_table_impacts and RPC functions
-- ================================================================

-- Grant table permissions to all roles
GRANT ALL ON utm_table_impacts TO authenticated;
GRANT ALL ON utm_table_impacts TO anon;
GRANT ALL ON utm_table_impacts TO service_role;
GRANT ALL ON utm_table_impacts TO postgres;

-- Grant execution permissions for RPC functions
GRANT EXECUTE ON FUNCTION get_table_summary(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION get_table_summary(UUID) TO anon;
GRANT EXECUTE ON FUNCTION get_table_summary(UUID) TO service_role;
GRANT EXECUTE ON FUNCTION get_table_summary(UUID) TO postgres;

GRANT EXECUTE ON FUNCTION get_table_detail(UUID, TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION get_table_detail(UUID, TEXT) TO anon;
GRANT EXECUTE ON FUNCTION get_table_detail(UUID, TEXT) TO service_role;
GRANT EXECUTE ON FUNCTION get_table_detail(UUID, TEXT) TO postgres;

GRANT EXECUTE ON FUNCTION get_dependency_pairs(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION get_dependency_pairs(UUID) TO anon;
GRANT EXECUTE ON FUNCTION get_dependency_pairs(UUID) TO service_role;
GRANT EXECUTE ON FUNCTION get_dependency_pairs(UUID) TO postgres;

-- Make functions SECURITY DEFINER to run with creator privileges
ALTER FUNCTION get_table_summary(UUID) SECURITY DEFINER;
ALTER FUNCTION get_table_detail(UUID, TEXT) SECURITY DEFINER;
ALTER FUNCTION get_dependency_pairs(UUID) SECURITY DEFINER;

-- Verify permissions
SELECT 
    routine_name,
    routine_type,
    security_type
FROM information_schema.routines
WHERE routine_name IN ('get_table_summary', 'get_table_detail', 'get_dependency_pairs');

COMMENT ON TABLE utm_table_impacts IS 
'Fixed permissions - granted to all roles and functions set to SECURITY DEFINER';

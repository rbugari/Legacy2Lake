-- ================================================================
-- Fix: Update get_table_summary to use singular field names
-- ================================================================

-- Function: Get table summary (readers/writers count)
-- FIXED: Use reader_count and writer_count (singular) to match frontend
CREATE OR REPLACE FUNCTION get_table_summary(p_project_id UUID)
RETURNS TABLE (
    table_name TEXT,
    reader_count BIGINT,
    writer_count BIGINT,
    total_impacts BIGINT,
    operations TEXT[]
)
LANGUAGE sql
STABLE
AS $$
    SELECT 
        full_name as table_name,
        COUNT(*) FILTER (WHERE is_source = true) as reader_count,
        COUNT(*) FILTER (WHERE is_target = true) as writer_count,
        COUNT(*) as total_impacts,
        ARRAY_AGG(DISTINCT operation ORDER BY operation) as operations
    FROM utm_table_impacts
    WHERE project_id = p_project_id
    GROUP BY full_name
    ORDER BY total_impacts DESC, full_name;
$$;

-- Verify change
SELECT routine_name, data_type 
FROM information_schema.routines 
WHERE routine_name = 'get_table_summary';

COMMENT ON FUNCTION get_table_summary(UUID) IS 
'Returns table summary with reader/writer counts (singular names for frontend compatibility)';

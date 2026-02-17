-- ================================================================
-- v4.0: Grant Permissions for Template Migration
-- ================================================================

-- Disable RLS temporarily for migration
ALTER TABLE utm_prompts DISABLE ROW LEVEL SECURITY;
ALTER TABLE utm_prompts_history DISABLE ROW LEVEL SECURITY;

-- Grant full access to authenticated users
GRANT ALL ON utm_prompts TO authenticated;
GRANT ALL ON utm_prompts TO anon;
GRANT ALL ON utm_prompts TO service_role;

GRANT ALL ON utm_prompts_history TO authenticated;
GRANT ALL ON utm_prompts_history TO anon;
GRANT ALL ON utm_prompts_history TO service_role;

-- For Postgres direct access
GRANT ALL ON utm_prompts TO postgres;
GRANT ALL ON utm_prompts_history TO postgres;

COMMENT ON TABLE utm_prompts IS 'v4.0: Permissions granted for migration - RLS disabled temporarily';

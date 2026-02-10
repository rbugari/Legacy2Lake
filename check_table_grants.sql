-- Check table permissions and RLS status
SELECT 
    schemaname,
    tablename,
    rowsecurity as rls_enabled,
    tableowner
FROM pg_tables
WHERE tablename = 'utm_project_members';

-- Check if service_role has permissions
SELECT 
    grantee,
    privilege_type
FROM information_schema.role_table_grants
WHERE table_name = 'utm_project_members'
AND grantee = 'service_role';

-- Alternative: Grant ALL to service_role if missing
-- Run this if above shows no grants:
GRANT ALL ON utm_project_members TO service_role;
GRANT ALL ON utm_project_members TO authenticator;
GRANT ALL ON utm_project_members TO authenticated;

-- ============================================
-- Debug RLS Policies for utm_objects
-- Run this in Supabase SQL Editor
-- ============================================

-- 1. Check all RLS policies on utm_objects
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual::text as using_clause,
    with_check::text as check_clause
FROM pg_policies 
WHERE tablename = 'utm_objects'
ORDER BY policyname;

-- 2. Check if RLS is enabled
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE tablename = 'utm_objects';

-- 3. Check current role (should be service_role for API)
SELECT current_user, current_setting('role', true);

-- 4. Test query that's failing
SELECT object_id, name, source_tech, tenant_id
FROM utm_objects
WHERE project_id = 'bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4'
  AND tenant_id = 'daac0ee6-3b28-412d-8acd-43ec51149188'
LIMIT 5;

-- 5. Check column exists and data
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'utm_objects'
  AND column_name = 'tenant_id';

-- Migration: 021b - Fix RLS policies for utm_project_members
-- Problem: RLS policies block service role operations from backend
-- Solution: Disable RLS since backend enforces security via require_manager()

BEGIN;

-- Drop existing restrictive policies
DROP POLICY IF EXISTS utm_project_members_select_own ON utm_project_members;
DROP POLICY IF EXISTS utm_project_members_insert_manager ON utm_project_members;
DROP POLICY IF EXISTS utm_project_members_delete_manager ON utm_project_members;

-- Disable RLS for this table
-- Security is handled by:
-- 1. Backend require_manager() dependency
-- 2. Backend tenant_id validation
-- 3. Service role key is only accessible to backend
ALTER TABLE utm_project_members DISABLE ROW LEVEL SECURITY;

COMMIT;

-- ============================================
-- Sprint 14: Add tenant_id to utm_objects
-- Date: 2026-02-16
-- ============================================
--
-- Problem: utm_objects doesn't have tenant_id column in Supabase
-- This causes 400 Bad Request when KnowledgePacketService and 
-- TableImpactService try to filter by tenant_id.
--
-- Solution: Add tenant_id column and backfill from utm_projects
--
-- ============================================

-- ============================================
-- 1. Add tenant_id column (if not exists)
-- ============================================

ALTER TABLE utm_objects 
ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES utm_tenants(tenant_id) ON DELETE CASCADE;

-- ============================================
-- 2. Backfill tenant_id from utm_projects
-- ============================================

-- Update all existing utm_objects records with tenant_id from their project
UPDATE utm_objects o
SET tenant_id = p.tenant_id
FROM utm_projects p
WHERE o.project_id = p.project_id
AND o.tenant_id IS NULL;

-- ============================================
-- 3. Create index for performance
-- ============================================

CREATE INDEX IF NOT EXISTS idx_utm_objects_tenant 
ON utm_objects(tenant_id);

CREATE INDEX IF NOT EXISTS idx_utm_objects_tenant_project 
ON utm_objects(tenant_id, project_id);

-- ============================================
-- 4. Update RLS policies (if needed)
-- ============================================

-- Drop existing policies if they exist
DROP POLICY IF EXISTS utm_objects_tenant_isolation ON utm_objects;

-- Create tenant isolation policy
CREATE POLICY utm_objects_tenant_isolation 
ON utm_objects 
FOR ALL 
USING (
    tenant_id = current_setting('app.current_tenant_id', true)::uuid
    OR 
    tenant_id IS NULL  -- Allow NULL during transition period
);

-- Service role can access all
CREATE POLICY utm_objects_service_role 
ON utm_objects 
FOR ALL 
TO service_role 
USING (true);

-- ============================================
-- 5. Comments
-- ============================================

COMMENT ON COLUMN utm_objects.tenant_id IS 
'Foreign key to utm_tenants for multi-tenant isolation. Duplicated from utm_projects for query performance.';

-- ============================================
-- 6. Verification queries
-- ============================================

-- Check how many objects don't have tenant_id
SELECT 
    COUNT(*) FILTER (WHERE tenant_id IS NULL) as without_tenant,
    COUNT(*) FILTER (WHERE tenant_id IS NOT NULL) as with_tenant,
    COUNT(*) as total
FROM utm_objects;

-- Sample check
SELECT 
    o.object_id,
    o.project_id,
    o.tenant_id as object_tenant_id,
    p.tenant_id as project_tenant_id,
    CASE 
        WHEN o.tenant_id = p.tenant_id OR (o.tenant_id IS NULL AND p.tenant_id IS NULL) THEN 'OK'
        ELSE 'MISMATCH'
    END as status
FROM utm_objects o
LEFT JOIN utm_projects p ON o.project_id = p.project_id
LIMIT 20;

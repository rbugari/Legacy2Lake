-- =========================================================================
-- Fix Permissions & Policies for restored tables
-- Description: The original restore script enabled RLS but did not add 
--              the policies or permissions. This restores full access.
-- =========================================================================

-- 1. Grant explicit permissions
GRANT ALL ON TABLE utm_asset_columns TO anon, authenticated, service_role;
GRANT ALL ON TABLE utm_table_impacts TO anon, authenticated, service_role;

-- 2. Restore all RLS policies for utm_asset_columns
DROP POLICY IF EXISTS tenant_column_isolation ON utm_asset_columns;
CREATE POLICY tenant_column_isolation ON utm_asset_columns
    FOR ALL
    USING (
        project_id IN (
            SELECT project_id 
            FROM utm_projects 
            WHERE tenant_id = COALESCE(
                (current_setting('app.current_tenant', true))::uuid,
                (current_setting('request.jwt.claims', true)::jsonb->>'tenant_id')::uuid
            )
        )
    );

-- 3. Restore all RLS policies for utm_table_impacts
DROP POLICY IF EXISTS table_impacts_service_role ON utm_table_impacts;
CREATE POLICY table_impacts_service_role 
ON utm_table_impacts 
FOR ALL 
TO service_role 
USING (true);

DROP POLICY IF EXISTS table_impacts_tenant_isolation ON utm_table_impacts;
CREATE POLICY table_impacts_tenant_isolation 
ON utm_table_impacts 
FOR ALL 
TO authenticated 
USING (
    tenant_id = COALESCE(
        (current_setting('app.current_tenant', true))::uuid,
        (current_setting('request.jwt.claims', true)::jsonb->>'tenant_id')::uuid
    )
);

SELECT 'Permissions and Policies restored successfully' as status;

-- v3.9 Migration Script 025
-- Remove org_name field (redundant with tenant_id)
-- Author: Development Team
-- Date: 2026-02-10

-- Description:
-- Simplifies the tenant model by removing the org_name field.
-- Only tenant_id (UUID) and display_name (friendly name) remain.
-- The org_name was not being used for routing or critical logic.

BEGIN;

DO $$
BEGIN
    RAISE NOTICE 'Removing org_name field from utm_tenants...';
END $$;

-- ============================================
-- 1. Drop org_name column
-- ============================================

ALTER TABLE utm_tenants DROP COLUMN IF EXISTS org_name;

DO $$
BEGIN
    RAISE NOTICE 'org_name column removed';
END $$;

-- ============================================
-- 2. Update table comment
-- ============================================

COMMENT ON TABLE utm_tenants IS 'v3.9: Organizations/Companies (identified by tenant_id UUID and display_name)';
COMMENT ON COLUMN utm_tenants.display_name IS 'Friendly display name for the organization (user-facing)';

-- ============================================
-- Verification
-- ============================================

DO $$
DECLARE
    has_org_name BOOLEAN;
    has_display_name BOOLEAN;
BEGIN
    -- Check org_name is gone
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'utm_tenants' AND column_name = 'org_name'
    ) INTO has_org_name;
    
    -- Check display_name still exists
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'utm_tenants' AND column_name = 'display_name'
    ) INTO has_display_name;
    
    IF has_org_name THEN
        RAISE EXCEPTION 'Migration failed: org_name still exists';
    END IF;
    
    IF NOT has_display_name THEN
        RAISE EXCEPTION 'Migration failed: display_name missing';
    END IF;
    
    RAISE NOTICE '✅ Migration successful: utm_tenants simplified (tenant_id + display_name only)';
END $$;

COMMIT;

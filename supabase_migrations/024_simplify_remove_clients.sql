-- v3.9 Migration Script 024
-- Simplify: Remove utm_clients concept
-- Author: Development Team
-- Date: 2026-02-10

-- Description:
-- Simplifies the data model by removing the CLIENT layer.
-- One TENANT = One Organization/Company (no intermediate client concept).
-- Adds display_name field for friendly client name.

BEGIN;

DO $$
BEGIN
    RAISE NOTICE 'Simplifying tenant structure - removing client_id...';
END $$;

-- ============================================
-- 1. Make client_id nullable (in case there's data)
-- ============================================

ALTER TABLE utm_tenants ALTER COLUMN client_id DROP NOT NULL;

DO $$
BEGIN
    RAISE NOTICE 'client_id is now nullable';
END $$;

-- ============================================
-- 2. Add display_name for friendly client representation
-- ============================================

ALTER TABLE utm_tenants ADD COLUMN IF NOT EXISTS display_name VARCHAR(255);

-- Migrate existing org_name to display_name if empty
UPDATE utm_tenants 
SET display_name = org_name 
WHERE display_name IS NULL;

DO $$
BEGIN
    RAISE NOTICE 'display_name field added';
END $$;

-- ============================================
-- 3. Drop client_id column completely
-- ============================================

ALTER TABLE utm_tenants DROP COLUMN IF EXISTS client_id;

DO $$
BEGIN
    RAISE NOTICE 'client_id column removed';
END $$;

-- ============================================
-- 4. Drop unique constraint on client_id (if exists)
-- ============================================

DROP INDEX IF EXISTS idx_tenants_client;

DO $$
BEGIN
    RAISE NOTICE 'client_id index removed';
END $$;

-- ============================================
-- 5. Update table comment
-- ============================================

COMMENT ON TABLE utm_tenants IS 'v3.9: Organizations/Companies (one tenant = one company, no client layer)';
COMMENT ON COLUMN utm_tenants.org_name IS 'Internal organization identifier';
COMMENT ON COLUMN utm_tenants.display_name IS 'Friendly display name for the client/organization';

-- ============================================
-- Verification
-- ============================================

DO $$
DECLARE
    has_client_id BOOLEAN;
    has_display_name BOOLEAN;
BEGIN
    -- Check client_id is gone
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'utm_tenants' AND column_name = 'client_id'
    ) INTO has_client_id;
    
    -- Check display_name exists
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'utm_tenants' AND column_name = 'display_name'
    ) INTO has_display_name;
    
    IF has_client_id THEN
        RAISE EXCEPTION 'Migration failed: client_id still exists';
    END IF;
    
    IF NOT has_display_name THEN
        RAISE EXCEPTION 'Migration failed: display_name not created';
    END IF;
    
    RAISE NOTICE '✅ Migration successful: utm_tenants simplified';
END $$;

COMMIT;

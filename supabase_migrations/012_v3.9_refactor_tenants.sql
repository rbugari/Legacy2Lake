-- v3.9 Migration Script 012
-- Refactor utm_tenants table structure
-- Author: Development Team
-- Date: 2026-02-09

-- ⚠️  CRITICAL: Backs up existing data before schema change
-- Must be run BEFORE script 015 (data migration)

-- Description:
-- 1. Backs up utm_tenants → utm_tenants_old
-- 2. Creates new utm_tenants with organization structure
-- 3. Prepares for S/M/L pricing tier support (v4.0)

BEGIN;

DO $$
BEGIN
    RAISE NOTICE 'Starting utm_tenants refactoring...';
END $$;

-- ============================================
-- STEP 1: Backup existing table
-- ============================================

DO $$
BEGIN
    RAISE NOTICE 'Step 1/3: Creating backup table...';
END $$;

-- Drop old backup if exists (idempotency)
DROP TABLE IF EXISTS utm_tenants_old CASCADE;

-- Create backup
CREATE TABLE utm_tenants_old AS 
SELECT * FROM utm_tenants;

-- Verify backup
DO $$
DECLARE
    original_count INTEGER;
    backup_count INTEGER;
BEGIN
    SELECT count(*) INTO original_count FROM utm_tenants;
    SELECT count(*) INTO backup_count FROM utm_tenants_old;
    
    RAISE NOTICE 'Backup created: % tenants', backup_count;
    
    IF original_count != backup_count THEN
        RAISE EXCEPTION 'BACKUP FAILED: Count mismatch (original=%, backup=%)', original_count, backup_count;
    END IF;
END $$;

-- ============================================
-- STEP 2: Drop and recreate utm_tenants
-- ============================================

DO $$
BEGIN
    RAISE NOTICE 'Step 2/3: Recreating utm_tenants with new structure...';
END $$;

DROP TABLE IF EXISTS utm_tenants CASCADE;

CREATE TABLE utm_tenants (
    tenant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id VARCHAR(50) NOT NULL UNIQUE,
    
    -- Organization Info (not user)
    org_name VARCHAR(255) NOT NULL,
    org_logo_url TEXT,
    
    -- Pricing tier (for future v4.0)
    tier VARCHAR(20) DEFAULT 'STANDARD',
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    suspended_at TIMESTAMP WITH TIME ZONE,
    suspension_reason TEXT,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CHECK (tier IN ('STANDARD', 'PREMIUM', 'ENTERPRISE'))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_tenants_client ON utm_tenants(client_id);
CREATE INDEX IF NOT EXISTS idx_tenants_active ON utm_tenants(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_tenants_tier ON utm_tenants(tier);

-- Comments
COMMENT ON TABLE utm_tenants IS 'v3.9: Organizations/companies (not individual users)';
COMMENT ON COLUMN utm_tenants.org_name IS 'Organization/company name';
COMMENT ON COLUMN utm_tenants.tier IS 'STANDARD, PREMIUM, ENTERPRISE (for future pricing)';

-- ============================================
-- STEP 3: Verify schema change
-- ============================================

DO $$
BEGIN
    RAISE NOTICE 'Step 3/3: Verifying new schema...';
END $$;

DO $$
DECLARE
    has_org_name BOOLEAN;
    has_tier BOOLEAN;
BEGIN
    -- Check new columns exist
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'utm_tenants' AND column_name = 'org_name'
    ) INTO has_org_name;
    
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'utm_tenants' AND column_name = 'tier'
    ) INTO has_tier;
    
    IF NOT has_org_name THEN
        RAISE EXCEPTION 'SCHEMA ERROR: org_name column missing';
    END IF;
    
    IF NOT has_tier THEN
        RAISE EXCEPTION 'SCHEMA ERROR: tier column missing';
    END IF;
    
    RAISE NOTICE '✅ Schema refactoring successful';
    RAISE NOTICE '⚠️  Data migration required (script 015)';
END $$;

COMMIT;

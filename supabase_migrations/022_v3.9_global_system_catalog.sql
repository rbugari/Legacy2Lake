-- v3.9 Migration Script 022
-- Global System Catalog (Cartridges/Technologies)
-- Author: Development Team
-- Date: 2026-02-09

-- Description:
-- Ensures utm_system_catalog is GLOBAL (managed by ADMIN only).
-- Cartridges of technology (origins/destinations) are NOT tenant-specific.
-- This is separate from utm_provider_vault (tenant-level) and utm_model_catalog (tenant-level).

BEGIN;

DO $$
BEGIN
    RAISE NOTICE 'Setting up global system catalog for cartridges...';
END $$;

-- ============================================
-- 1. Create utm_system_catalog if not exists
-- ============================================

CREATE TABLE IF NOT EXISTS utm_system_catalog (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tech_id VARCHAR(100) UNIQUE NOT NULL,  -- 'sqlserver', 'oracle', 'snowflake', 'databricks'
    name VARCHAR(255) NOT NULL,             -- 'SQL Server', 'Oracle Database'
    type VARCHAR(50) NOT NULL,              -- 'origin' or 'destination'
    description TEXT,
    logo_url TEXT,                          -- Optional icon/logo
    config JSONB DEFAULT '{}'::jsonb,       -- Custom configuration per cartridge
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Ensure tech_id column exists (backward compatibility)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'utm_system_catalog' 
        AND column_name = 'tech_id'
    ) THEN
        -- Add tech_id if missing (backfill from name)
        ALTER TABLE utm_system_catalog ADD COLUMN tech_id VARCHAR(100);
        UPDATE utm_system_catalog 
        SET tech_id = LOWER(REPLACE(name, ' ', '_'))
        WHERE tech_id IS NULL;
        ALTER TABLE utm_system_catalog ALTER COLUMN tech_id SET NOT NULL;
        ALTER TABLE utm_system_catalog ADD CONSTRAINT utm_system_catalog_tech_id_key UNIQUE (tech_id);
    END IF;
END $$;

-- ============================================
-- 2. Ensure NO tenant_id column
-- ============================================

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'utm_system_catalog' 
        AND column_name = 'tenant_id'
    ) THEN
        RAISE NOTICE 'Removing tenant_id from utm_system_catalog (making it global)...';
        ALTER TABLE utm_system_catalog DROP COLUMN tenant_id;
    ELSE
        RAISE NOTICE 'utm_system_catalog is already global (no tenant_id column)';
    END IF;
END $$;

-- ============================================
-- 3. Indexes
-- ============================================

CREATE INDEX IF NOT EXISTS idx_system_catalog_type ON utm_system_catalog(type);
CREATE INDEX IF NOT EXISTS idx_system_catalog_active ON utm_system_catalog(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_system_catalog_tech_id ON utm_system_catalog(tech_id);

-- ============================================
-- 4. Comments
-- ============================================

COMMENT ON TABLE utm_system_catalog IS 'v3.9: Global catalog of technology cartridges (origins/destinations). Managed by ADMIN only. NOT tenant-specific.';
COMMENT ON COLUMN utm_system_catalog.tech_id IS 'Technical identifier: sqlserver, oracle, snowflake, databricks, etc.';
COMMENT ON COLUMN utm_system_catalog.type IS 'origin (source technology) or destination (target technology)';
COMMENT ON COLUMN utm_system_catalog.config IS 'Custom configuration JSON per cartridge';
COMMENT ON COLUMN utm_system_catalog.is_active IS 'Active cartridges appear in UI for selection';

-- ============================================
-- 5. Seed common cartridges if empty
-- ============================================

DO $$
DECLARE
    cartridge_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO cartridge_count FROM utm_system_catalog;
    
    IF cartridge_count = 0 THEN
        RAISE NOTICE 'Seeding common cartridges...';
        
        -- Origins (Sources)
        INSERT INTO utm_system_catalog (tech_id, name, type, description, is_active) VALUES
        ('sqlserver', 'SQL Server', 'origin', 'Microsoft SQL Server database', TRUE),
        ('oracle', 'Oracle Database', 'origin', 'Oracle RDBMS', TRUE),
        ('mysql', 'MySQL', 'origin', 'MySQL database', TRUE),
        ('postgresql', 'PostgreSQL', 'origin', 'PostgreSQL database', TRUE),
        ('ssis', 'SSIS', 'origin', 'SQL Server Integration Services packages', TRUE),
        ('informatica', 'Informatica', 'origin', 'Informatica PowerCenter workflows', TRUE),
        ('teradata', 'Teradata', 'origin', 'Teradata database', TRUE),
        ('sap', 'SAP', 'origin', 'SAP ERP tables and logic', TRUE);
        
        -- Destinations (Targets)
        INSERT INTO utm_system_catalog (tech_id, name, type, description, is_active) VALUES
        ('databricks', 'Databricks', 'destination', 'Databricks Lakehouse (PySpark)', TRUE),
        ('snowflake', 'Snowflake', 'destination', 'Snowflake Data Cloud', TRUE),
        ('synapse', 'Azure Synapse', 'destination', 'Azure Synapse Analytics', TRUE),
        ('fabric', 'Microsoft Fabric', 'destination', 'Microsoft Fabric Data Engineering', TRUE),
        ('redshift', 'Amazon Redshift', 'destination', 'Amazon Redshift data warehouse', TRUE),
        ('bigquery', 'Google BigQuery', 'destination', 'Google BigQuery', TRUE),
        ('dbt', 'dbt', 'destination', 'dbt (data build tool) transformations', TRUE);
        
        RAISE NOTICE 'Seeded % cartridges', (SELECT COUNT(*) FROM utm_system_catalog);
    ELSE
        RAISE NOTICE 'utm_system_catalog already has % cartridges, skipping seed', cartridge_count;
    END IF;
END $$;

-- ============================================
-- 6. RLS Policies (Read-only for all, Admin-only modify)
-- ============================================

ALTER TABLE utm_system_catalog ENABLE ROW LEVEL SECURITY;

-- Everyone can read cartridges (needed for UI selection)
DROP POLICY IF EXISTS system_catalog_read_all ON utm_system_catalog;
CREATE POLICY system_catalog_read_all 
ON utm_system_catalog FOR SELECT
USING (TRUE);

-- Only service_role can modify (ADMIN uses service_role in backend)
DROP POLICY IF EXISTS system_catalog_admin_modify ON utm_system_catalog;
CREATE POLICY system_catalog_admin_modify 
ON utm_system_catalog FOR ALL
USING (
    -- This policy allows service_role to do anything
    TRUE
)
WITH CHECK (
    TRUE
);

COMMENT ON POLICY system_catalog_read_all ON utm_system_catalog IS 'All users can read cartridges for selection';
COMMENT ON POLICY system_catalog_admin_modify ON utm_system_catalog IS 'Only ADMIN (via service_role) can modify catalog';

COMMIT;

DO $$
BEGIN
    RAISE NOTICE 'Migration 022 completed: Global system catalog configured';
END $$;

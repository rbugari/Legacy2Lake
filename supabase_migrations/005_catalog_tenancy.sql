-- Migration: 005 Catalog Tenancy
-- Description: Adds tenant_id and is_public to utm_model_catalog

ALTER TABLE utm_model_catalog
ADD COLUMN IF NOT EXISTS tenant_id UUID,
ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT FALSE;

-- Update existing records to be public (System Defaults)
UPDATE utm_model_catalog SET is_public = TRUE WHERE tenant_id IS NULL;

-- Index for performance
CREATE INDEX IF NOT EXISTS idx_model_tenant ON utm_model_catalog(tenant_id);

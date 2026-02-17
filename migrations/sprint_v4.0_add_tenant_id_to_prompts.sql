-- ================================================================
-- v4.0: Add tenant_id column to utm_prompts (Optional Column)
-- ================================================================

-- Add tenant_id column (nullable) for future tenant-specific prompts
ALTER TABLE utm_prompts ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES utm_tenants(tenant_id);

-- Create index on tenant_id
CREATE INDEX IF NOT EXISTS idx_prompts_tenant ON utm_prompts(tenant_id) WHERE tenant_id IS NOT NULL;

COMMENT ON COLUMN utm_prompts.tenant_id IS 'Optional: tenant-specific prompt override (NULL = global)';

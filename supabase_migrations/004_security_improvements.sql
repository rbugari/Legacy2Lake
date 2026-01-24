-- ============================================
-- Migration: Security Improvements
-- Date: 2026-01-24
-- Description: Adds bcrypt password support and vault table for encrypted API keys
-- ============================================

-- 1. Add bcrypt password column to utm_tenants
ALTER TABLE utm_tenants 
ADD COLUMN IF NOT EXISTS password_hash_bcrypt TEXT;

-- Comment for documentation
COMMENT ON COLUMN utm_tenants.password_hash_bcrypt IS 'bcrypt hashed password (replaces SHA256 password_hash)';

-- 2. Create utm_vault table for encrypted API key storage
CREATE TABLE IF NOT EXISTS utm_vault (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    provider VARCHAR(50) NOT NULL,
    api_key_encrypted TEXT NOT NULL,
    base_url_encrypted TEXT,
    metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tenant_id, provider)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_vault_tenant ON utm_vault(tenant_id);
CREATE INDEX IF NOT EXISTS idx_vault_provider ON utm_vault(provider);

-- Enable RLS (Row Level Security)
ALTER TABLE utm_vault ENABLE ROW LEVEL SECURITY;

-- 3. Create utm_audit_log table for security auditing
CREATE TABLE IF NOT EXISTS utm_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID,
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(255),
    message TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for audit log queries
CREATE INDEX IF NOT EXISTS idx_audit_tenant ON utm_audit_log(tenant_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON utm_audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON utm_audit_log(timestamp DESC);

-- ============================================
-- ROLLBACK SCRIPT (if needed):
-- ============================================
-- ALTER TABLE utm_tenants DROP COLUMN IF EXISTS password_hash_bcrypt;
-- DROP TABLE IF EXISTS utm_vault;
-- DROP TABLE IF EXISTS utm_audit_log;
-- ============================================

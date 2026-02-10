-- v3.9 Migration Script 010
-- Create utm_users table
-- Author: Development Team
-- Date: 2026-02-09

-- Description:
-- Separates user identity from tenant/organization concept.
-- Allows multiple users per tenant with role-based access.

BEGIN;

-- Create utm_users table
CREATE TABLE IF NOT EXISTS utm_users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES utm_tenants(tenant_id) ON DELETE CASCADE,
    
    -- Identity
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(100) NOT NULL,
    password_hash_bcrypt TEXT NOT NULL,
    
    -- Role (ONLY 3 options for simplicity)
    role VARCHAR(20) NOT NULL DEFAULT 'VIEWER',
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP WITH TIME ZONE,
    
    -- Basic profile info
    display_name VARCHAR(255),
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(tenant_id, email),
    CHECK (role IN ('ADMIN', 'COLLABORATOR', 'VIEWER'))
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_tenant ON utm_users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON utm_users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON utm_users(role);
CREATE INDEX IF NOT EXISTS idx_users_active ON utm_users(is_active) WHERE is_active = TRUE;

-- Comments
COMMENT ON TABLE utm_users IS 'v3.9: User identities separate from tenants/organizations';
COMMENT ON COLUMN utm_users.role IS 'ADMIN (full control), COLLABORATOR (create/edit), VIEWER (read-only)';
COMMENT ON COLUMN utm_users.email IS 'Unique across all tenants for global login';

-- Verify creation
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'utm_users') THEN
        RAISE NOTICE 'Table utm_users created successfully';
    ELSE
        RAISE EXCEPTION 'Failed to create utm_users table';
    END IF;
END $$;

COMMIT;

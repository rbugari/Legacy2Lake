-- v3.9 Migration Script 011
-- Create utm_user_invitations table
-- Author: Development Team
-- Date: 2026-02-09

-- Description:
-- Manages pending user invitations to join a tenant.
-- Supports email-based invite workflow with token validation.

BEGIN;

-- Create utm_user_invitations table
CREATE TABLE IF NOT EXISTS utm_user_invitations (
    invitation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES utm_tenants(tenant_id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'VIEWER',
    
    -- Token for secure acceptance
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Status tracking
    status VARCHAR(20) DEFAULT 'PENDING',
    
    -- Who invited
    invited_by UUID REFERENCES utm_users(user_id) ON DELETE SET NULL,
    invited_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Acceptance tracking
    accepted_at TIMESTAMP WITH TIME ZONE,
    accepted_by_ip VARCHAR(45),
    
    -- Constraints
    UNIQUE(tenant_id, email),
    CHECK (role IN ('ADMIN', 'COLLABORATOR', 'VIEWER')),
    CHECK (status IN ('PENDING', 'ACCEPTED', 'EXPIRED', 'REVOKED'))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_invitations_tenant ON utm_user_invitations(tenant_id);
CREATE INDEX IF NOT EXISTS idx_invitations_email ON utm_user_invitations(email);
CREATE INDEX IF NOT EXISTS idx_invitations_token ON utm_user_invitations(token);
CREATE INDEX IF NOT EXISTS idx_invitations_status ON utm_user_invitations(status);
CREATE INDEX IF NOT EXISTS idx_invitations_expires ON utm_user_invitations(expires_at);

-- Function to auto-expire old invitations
CREATE OR REPLACE FUNCTION expire_old_invitations()
RETURNS void AS $$
BEGIN
    UPDATE utm_user_invitations
    SET status = 'EXPIRED'
    WHERE status = 'PENDING'
    AND expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- Comments
COMMENT ON TABLE utm_user_invitations IS 'v3.9: Pending user invitations with token-based acceptance';
COMMENT ON COLUMN utm_user_invitations.token IS 'UUID-based secure token for invite acceptance URL';
COMMENT ON COLUMN utm_user_invitations.expires_at IS 'Invitations expire after 7 days by default';

-- Verify creation
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'utm_user_invitations') THEN
        RAISE NOTICE 'Table utm_user_invitations created successfully';
    ELSE
        RAISE EXCEPTION 'Failed to create utm_user_invitations table';
    END IF;
END $$;

COMMIT;

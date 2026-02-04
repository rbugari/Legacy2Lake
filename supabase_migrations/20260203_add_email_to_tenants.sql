-- Migration: Add email to utm_tenants
-- Created: 2026-02-03
-- Description: Adds email column for user invitation and password recovery flwo.

ALTER TABLE utm_tenants 
ADD COLUMN IF NOT EXISTS email TEXT;

-- Index for searching users by email (useful for recovery)
CREATE INDEX IF NOT EXISTS idx_tenants_email ON utm_tenants(email);

COMMENT ON COLUMN utm_tenants.email IS 'User email for notifications and password recovery';

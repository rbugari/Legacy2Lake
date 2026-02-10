-- Add ADMIN role back to utm_users constraint for platform admin
-- Date: 2026-02-10

BEGIN;

-- Drop current constraint
ALTER TABLE utm_users DROP CONSTRAINT IF EXISTS utm_users_role_check;

-- Create new constraint with ADMIN included
ALTER TABLE utm_users ADD CONSTRAINT utm_users_role_check 
CHECK (role IN ('ADMIN', 'MANAGER', 'COLLABORATOR', 'VIEWER'));

-- Also update invitations table
ALTER TABLE utm_user_invitations DROP CONSTRAINT IF EXISTS utm_user_invitations_role_check;

ALTER TABLE utm_user_invitations ADD CONSTRAINT utm_user_invitations_role_check 
CHECK (role IN ('ADMIN', 'MANAGER', 'COLLABORATOR', 'VIEWER'));

COMMIT;

-- Verify
DO $$
BEGIN
    RAISE NOTICE 'ADMIN role added back to constraints successfully';
END $$;

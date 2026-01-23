-- Migration: Add Identity and Antigravity Columns
-- Created: 2026-01-23
-- Description: Adds tenant_id, client_id to core tables and is_active kill-switch.

-- 1. Update utm_projects
ALTER TABLE utm_projects 
ADD COLUMN IF NOT EXISTS tenant_id UUID,
ADD COLUMN IF NOT EXISTS client_id UUID,
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;

-- 2. Update utm_objects
ALTER TABLE utm_objects 
ADD COLUMN IF NOT EXISTS tenant_id UUID,
ADD COLUMN IF NOT EXISTS client_id UUID;

-- Note: Indices on tenant_id are recommended for performance but are not automatically created per user policy.

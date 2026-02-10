-- v3.9 Migration Script 023
-- Add Azure OpenAI deployment fields to utm_model_catalog
-- Author: Development Team
-- Date: 2026-02-10

-- Description:
-- Adds deployment_id and api_version columns to support Azure OpenAI
-- deployment configuration. These fields allow mapping model_id to
-- actual Azure deployment names.

BEGIN;

DO $$
BEGIN
    RAISE NOTICE 'Adding Azure deployment fields to utm_model_catalog...';
END $$;

-- Add deployment_id column
-- This stores the actual Azure deployment name (e.g., "gpt-4o", "gpt-35-turbo")
-- which may differ from model_id (e.g., "azure-gpt-4o")
ALTER TABLE utm_model_catalog 
ADD COLUMN IF NOT EXISTS deployment_id TEXT;

-- Add api_version column
-- Azure OpenAI requires specific API versions (e.g., "2024-02-15-preview")
ALTER TABLE utm_model_catalog 
ADD COLUMN IF NOT EXISTS api_version TEXT;

-- Add is_active column for enabling/disabling models
ALTER TABLE utm_model_catalog 
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;

-- Comments for documentation
COMMENT ON COLUMN utm_model_catalog.deployment_id IS 'v3.9: Azure deployment name (actual name in Azure Portal, may differ from model_id)';
COMMENT ON COLUMN utm_model_catalog.api_version IS 'v3.9: Azure OpenAI API version (e.g., 2024-02-15-preview)';
COMMENT ON COLUMN utm_model_catalog.is_active IS 'v3.9: Enable/disable model for selection';

-- Update existing Azure models with common deployment patterns
-- These are best guesses - verify against your Azure Portal
DO $$
BEGIN
    -- Azure GPT-4o deployments typically named "gpt-4o"
    UPDATE utm_model_catalog 
    SET 
        deployment_id = 'gpt-4o',
        api_version = '2024-02-15-preview',
        provider = 'azure'
    WHERE model_id = 'azure-gpt-4o' 
      AND deployment_id IS NULL;
    
    -- Azure GPT-3.5-turbo deployments typically named "gpt-35-turbo"
    UPDATE utm_model_catalog 
    SET 
        deployment_id = 'gpt-35-turbo',
        api_version = '2024-02-15-preview',
        provider = 'azure'
    WHERE model_id = 'azure-gpt-35-turbo' 
      AND deployment_id IS NULL;
    
    RAISE NOTICE 'Updated deployment_id for Azure models (verify against your Azure Portal)';
END $$;

-- Verify columns were added
DO $$
DECLARE
    has_deployment BOOLEAN;
    has_version BOOLEAN;
    has_active BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'utm_model_catalog' AND column_name = 'deployment_id'
    ) INTO has_deployment;
    
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'utm_model_catalog' AND column_name = 'api_version'
    ) INTO has_version;
    
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'utm_model_catalog' AND column_name = 'is_active'
    ) INTO has_active;
    
    IF has_deployment AND has_version AND has_active THEN
        RAISE NOTICE '✅ All columns added successfully';
        RAISE NOTICE 'deployment_id: %', has_deployment;
        RAISE NOTICE 'api_version: %', has_version;
        RAISE NOTICE 'is_active: %', has_active;
    ELSE
        RAISE EXCEPTION 'Failed to add required columns';
    END IF;
END $$;

COMMIT;

-- Post-migration notes:
-- ====================
-- 1. Verify deployment_id matches your Azure Portal deployment names
-- 2. Check that api_version is compatible with your deployments
-- 3. Update any model with incorrect deployment_id:
--    UPDATE utm_model_catalog 
--    SET deployment_id = 'your-actual-deployment-name'
--    WHERE model_id = 'azure-gpt-4o' AND tenant_id = 'your-tenant-id';

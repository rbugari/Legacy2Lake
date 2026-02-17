-- Migration: Sprint 13 - Add Visualization Columns to utm_objects
-- Created: 2026-02-11
-- Description: Adds columns needed for Code/Schema/Quality/Performance visualization

-- Add Sprint 13 visualization columns
ALTER TABLE utm_objects 
ADD COLUMN IF NOT EXISTS object_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS generated_code TEXT,
ADD COLUMN IF NOT EXISTS tech_id VARCHAR(50),
ADD COLUMN IF NOT EXISTS layer VARCHAR(50),
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS validation_result JSONB,
ADD COLUMN IF NOT EXISTS optimization_metadata JSONB,
ADD COLUMN IF NOT EXISTS schema_metadata JSONB,
ADD COLUMN IF NOT EXISTS row_count BIGINT,
ADD COLUMN IF NOT EXISTS column_count INTEGER,
ADD COLUMN IF NOT EXISTS quality_score NUMERIC(5,2),
ADD COLUMN IF NOT EXISTS quality_violations JSONB;

-- Create trigger to auto-update updated_at
CREATE OR REPLACE FUNCTION update_utm_objects_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS utm_objects_updated_at_trigger ON utm_objects;
CREATE TRIGGER utm_objects_updated_at_trigger
    BEFORE UPDATE ON utm_objects
    FOR EACH ROW
    EXECUTE FUNCTION update_utm_objects_updated_at();

-- Populate object_name from source_name for existing records
UPDATE utm_objects 
SET object_name = source_name 
WHERE object_name IS NULL;

-- Add comment for documentation
COMMENT ON COLUMN utm_objects.generated_code IS 'Sprint 8-12: Generated target code (Python, SQL, etc)';
COMMENT ON COLUMN utm_objects.tech_id IS 'Sprint 8: Target technology (pyspark, databricks, snowflake, etc)';
COMMENT ON COLUMN utm_objects.layer IS 'Sprint 8: Medallion layer (bronze, silver, gold)';
COMMENT ON COLUMN utm_objects.validation_result IS 'Sprint 11: Validation results from ValidationService';
COMMENT ON COLUMN utm_objects.optimization_metadata IS 'Sprint 12: Query optimization metadata';
COMMENT ON COLUMN utm_objects.schema_metadata IS 'Sprint 9-10: Schema extraction and versioning data';
COMMENT ON COLUMN utm_objects.quality_score IS 'Sprint 11: Overall quality score (0-100)';
COMMENT ON COLUMN utm_objects.quality_violations IS 'Sprint 11: Quality rule violations detected';

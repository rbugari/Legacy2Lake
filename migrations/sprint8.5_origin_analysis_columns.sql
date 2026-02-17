-- ================================================================
-- Sprint 8.5: Origin Analysis Dashboard - Schema Extension
-- ================================================================
-- Purpose:
--   Add columns to utm_objects to store SSIS origin analysis data
--   Extracted during code generation (Discovery/Triage phase)
--
-- Author: Legacy2Lake Engineering
-- Date: 2026-02-13 (Sprint 8.5)
-- Version: v1.0
-- ================================================================

-- Add origin analysis columns to utm_objects
ALTER TABLE utm_objects 
ADD COLUMN IF NOT EXISTS source_connection JSONB NULL,
ADD COLUMN IF NOT EXISTS source_type VARCHAR(100) NULL,
ADD COLUMN IF NOT EXISTS transformations JSONB NULL,
ADD COLUMN IF NOT EXISTS complexity_score INT NULL,
ADD COLUMN IF NOT EXISTS data_flow_analysis JSONB NULL,
ADD COLUMN IF NOT EXISTS source_query TEXT NULL;

-- Add comments for documentation
COMMENT ON COLUMN utm_objects.source_connection IS 'SSIS connections array (OLEDB, ODBC, etc.) - Sprint 8.5';
COMMENT ON COLUMN utm_objects.source_type IS 'Source system type (SQL Server, Oracle, File) - Sprint 8.5';
COMMENT ON COLUMN utm_objects.transformations IS 'SSIS transformations list with types and complexity - Sprint 8.5';
COMMENT ON COLUMN utm_objects.complexity_score IS 'Complexity score 0-100 based on transformation count/types - Sprint 8.5';
COMMENT ON COLUMN utm_objects.data_flow_analysis IS 'Full data flow analysis (origin, queries, stats) - Sprint 8.5';
COMMENT ON COLUMN utm_objects.source_query IS 'Primary source query extracted from SSIS - Sprint 8.5';

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_objects_source_type ON utm_objects(source_type);
CREATE INDEX IF NOT EXISTS idx_objects_complexity ON utm_objects(complexity_score);

-- Verification query (optional)
-- SELECT column_name, data_type, is_nullable 
-- FROM information_schema.columns 
-- WHERE table_name = 'utm_objects' 
-- AND column_name IN ('source_connection', 'source_type', 'transformations', 'complexity_score', 'data_flow_analysis', 'source_query');

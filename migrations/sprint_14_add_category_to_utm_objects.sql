-- ============================================
-- Sprint 14: Add category column to utm_objects
-- Date: 2026-02-16
-- ============================================
--
-- Problem: 
--   Support files (.sql DDLs, .csv, etc.) are being processed 
--   as migration tasks because utm_objects doesn't store file classification.
--
-- Solution: 
--   Add category column to distinguish:
--   - migrable: ETL packages (DTSX, DSX, KTR, etc.)
--   - soporte: Support files (SQL DDLs, CSV, XLSX, etc.) 
--   - documentacion: Documentation (MD, TXT, PDF, etc.)
--   - no_reconocido: Unrecognized files
--
-- ============================================

-- ============================================
-- 1. Add category column
-- ============================================

ALTER TABLE utm_objects 
ADD COLUMN IF NOT EXISTS category VARCHAR(50) 
CHECK (category IN ('migrable', 'soporte', 'documentacion', 'no_reconocido'));

-- ============================================
-- 2. Create index for performance
-- ============================================

CREATE INDEX IF NOT EXISTS idx_utm_objects_category 
ON utm_objects(category);

-- ============================================
-- 3. Backfill category from file extension
-- ============================================

-- Migrable files (ETL packages)
UPDATE utm_objects 
SET category = 'migrable'
WHERE category IS NULL 
AND (
    source_name ILIKE '%.dtsx' OR  -- SSIS
    source_name ILIKE '%.dsx' OR   -- DataStage
    source_name ILIKE '%.kjb' OR   -- Pentaho Job
    source_name ILIKE '%.ktr' OR   -- Pentaho Transformation
    source_name ILIKE '%.pmx' OR   -- Informatica
    source_name ILIKE '%.xml'      -- Informatica (needs signature)
);

-- Support files (DDL, data, config)
UPDATE utm_objects 
SET category = 'soporte'
WHERE category IS NULL 
AND (
    source_name ILIKE '%.sql' OR 
    source_name ILIKE '%.csv' OR 
    source_name ILIKE '%.xlsx' OR 
    source_name ILIKE '%.xls' OR 
    source_name ILIKE '%.json' OR 
    source_name ILIKE '%.yaml' OR 
    source_name ILIKE '%.yml'
);

-- Documentation
UPDATE utm_objects 
SET category = 'documentacion'
WHERE category IS NULL 
AND (
    source_name ILIKE '%.md' OR 
    source_name ILIKE '%.txt' OR 
    source_name ILIKE '%.pdf' OR 
    source_name ILIKE '%.docx' OR 
    source_name ILIKE '%.doc' OR 
    source_name ILIKE '%.rtf'
);

-- Unrecognized
UPDATE utm_objects 
SET category = 'no_reconocido'
WHERE category IS NULL;

-- ============================================
-- 4. Add comment
-- ============================================

COMMENT ON COLUMN utm_objects.category IS 
'File classification: migrable, soporte, documentacion, no_reconocido (Sprint 14)';

-- ============================================
-- 5. Verification queries
-- ============================================

-- Count by category
-- SELECT category, COUNT(*) 
-- FROM utm_objects 
-- GROUP BY category 
-- ORDER BY COUNT(*) DESC;

-- Show support files incorrectly migrated
-- SELECT object_id, source_name, category, status 
-- FROM utm_objects 
-- WHERE category = 'soporte' 
-- AND status IN ('processing', 'completed');

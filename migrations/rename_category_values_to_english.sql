-- Migration: Rename utm_objects.category values from Spanish to English
-- Date: 2026-04-06
-- Scope: utm_objects table, category column

-- 1. Drop existing check constraint (allows only old Spanish values)
ALTER TABLE utm_objects DROP CONSTRAINT IF EXISTS utm_objects_category_check;

-- 2. Update data
UPDATE utm_objects SET category = 'migratable'   WHERE category = 'migrable';
UPDATE utm_objects SET category = 'support'       WHERE category = 'soporte';
UPDATE utm_objects SET category = 'documentation' WHERE category = 'documentacion';
UPDATE utm_objects SET category = 'unrecognized'  WHERE category = 'no_reconocido';

-- 3. Recreate constraint with English values
ALTER TABLE utm_objects
    ADD CONSTRAINT utm_objects_category_check
    CHECK (category IN ('migratable', 'support', 'documentation', 'unrecognized'));

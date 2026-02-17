-- ================================================================
-- Update cartridge_databricks_bronze prompt to fix Agent F rejection
-- ================================================================
-- Purpose: Remove old auto-seeded prompt so it re-seeds with fixes:
--   1. Changed MERGE pattern to eliminate .mode("overwrite")
--   2. Now uses empty CTAS + MERGE INTO for initial loads
-- Expected Impact: Agent F score should improve from 6/10 to ≥8/10
-- ================================================================

DO $$
BEGIN
    -- Delete old cartridge prompt (will auto-reseed on next Agent C run)
    DELETE FROM utm_prompts 
    WHERE prompt_id = 'cartridge_databricks_bronze';
    
    RAISE NOTICE 'Deleted old cartridge_databricks_bronze prompt - will auto-reseed on next run';
    
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Error deleting cartridge prompt: %', SQLERRM;
END $$;

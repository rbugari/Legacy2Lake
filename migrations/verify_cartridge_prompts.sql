-- ================================================================
-- Verify Cartridge Prompts in Database (Bronze, Silver, Gold)
-- ================================================================
-- Purpose: Check if all three medallion layer cartridge prompts are loaded
-- Expected: 3 cartridges with proper character counts
-- ================================================================

-- Query all cartridge prompts
SELECT 
    prompt_id,
    tenant_id,
    LENGTH(content) as char_count,
    is_active,
    created_at,
    updated_at
FROM utm_prompts
WHERE prompt_id LIKE 'cartridge_databricks_%'
ORDER BY prompt_id;

-- Summary statistics
SELECT 
    COUNT(*) as total_cartridges,
    SUM(CASE WHEN prompt_id = 'cartridge_databricks_bronze' THEN 1 ELSE 0 END) as has_bronze,
    SUM(CASE WHEN prompt_id = 'cartridge_databricks_silver' THEN 1 ELSE 0 END) as has_silver,
    SUM(CASE WHEN prompt_id = 'cartridge_databricks_gold' THEN 1 ELSE 0 END) as has_gold
FROM utm_prompts
WHERE prompt_id LIKE 'cartridge_databricks_%';

-- Expected sizes from file system:
-- cartridge_databricks_bronze.md:  8,117 bytes (~8.1 KB)
-- cartridge_databricks_silver.md: 13,909 bytes (~13.9 KB)
-- cartridge_databricks_gold.md:   18,228 bytes (~18.2 KB)

-- If any are missing, they need to be auto-seeded by restarting the backend
-- Auto-seeding happens in PromptService.__init__() when the API starts

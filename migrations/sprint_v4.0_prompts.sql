-- ================================================================
-- v4.0: Zero-Hardcode Generation - Prompts System
-- ================================================================
-- Purpose: Create tables for dynamic prompt management with automatic versioning
-- Author: Legacy2Lake Engineering
-- Date: 2026-02-15
-- Version: v4.0
--
-- Features:
--   - Global prompts (no tenant_id - used by all tenants)
--   - Automatic versioning via trigger (safety net)
--   - History table for ADMIN analysis only
--   - No UI for rollback - trigger is automatic
--
-- Tables:
--   1. utm_prompts - Main prompts table (GLOBAL)
--   2. utm_prompts_history - Automatic version history (READ-ONLY for ADMIN)
--
-- ================================================================

-- ================================================================
-- 1. MAIN PROMPTS TABLE (GLOBAL)
-- ================================================================

CREATE TABLE IF NOT EXISTS utm_prompts (
    prompt_id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    tech_stack TEXT,              -- e.g., 'databricks', 'snowflake', 'pyspark', NULL for generic
    pattern_type TEXT,             -- e.g., 'direct', 'bronze', 'silver', 'gold', NULL for generic
    agent_id TEXT,                 -- e.g., 'agent-c', 'agent-f', 'agent-g', NULL for shared
    is_active BOOLEAN DEFAULT true,
    created_by UUID,               -- User who created (can be NULL for system prompts)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Constraints
    CONSTRAINT check_prompt_id_format CHECK (prompt_id ~ '^[a-z0-9_]+$')
);

-- Add comments
COMMENT ON TABLE utm_prompts IS 'v4.0: Global prompts for all agents and cartridges';
COMMENT ON COLUMN utm_prompts.prompt_id IS 'Unique identifier (e.g., agent_c_interpreter, cartridge_databricks_direct)';
COMMENT ON COLUMN utm_prompts.content IS 'Full prompt content in Markdown format';
COMMENT ON COLUMN utm_prompts.tech_stack IS 'Technology stack (databricks, snowflake, pyspark, etc.) or NULL for generic';
COMMENT ON COLUMN utm_prompts.pattern_type IS 'Pattern type (direct, bronze, silver, gold) or NULL for generic';
COMMENT ON COLUMN utm_prompts.agent_id IS 'Agent identifier (agent-c, agent-f, etc.) or NULL for shared prompts';
COMMENT ON COLUMN utm_prompts.is_active IS 'Whether prompt is active (for soft deletion)';
COMMENT ON COLUMN utm_prompts.metadata IS 'Additional metadata (version info, tags, etc.)';


-- ================================================================
-- 2. PROMPTS HISTORY TABLE (AUTOMATIC VERSIONING)
-- ================================================================

CREATE TABLE IF NOT EXISTS utm_prompts_history (
    history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_id TEXT NOT NULL,
    content TEXT NOT NULL,
    tech_stack TEXT,
    pattern_type TEXT,
    agent_id TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    changed_by UUID,               -- User who made the change (OLD.created_by)
    changed_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Foreign key (optional - allows orphaned history if prompt deleted)
    CONSTRAINT fk_history_prompt FOREIGN KEY (prompt_id) 
        REFERENCES utm_prompts(prompt_id) 
        ON DELETE CASCADE
);

-- Add comments
COMMENT ON TABLE utm_prompts_history IS 'v4.0: Automatic version history - READ-ONLY for ADMIN analysis';
COMMENT ON COLUMN utm_prompts_history.history_id IS 'Unique identifier for this history entry';
COMMENT ON COLUMN utm_prompts_history.changed_at IS 'Timestamp when this version was replaced';


-- ================================================================
-- 3. TRIGGER FUNCTION: Save Previous Version Before UPDATE
-- ================================================================

CREATE OR REPLACE FUNCTION save_prompt_version()
RETURNS TRIGGER AS $$
BEGIN
    -- Save the OLD version to history before updating
    INSERT INTO utm_prompts_history (
        prompt_id, 
        content, 
        tech_stack, 
        pattern_type,
        agent_id, 
        metadata, 
        changed_by, 
        changed_at
    )
    VALUES (
        OLD.prompt_id, 
        OLD.content, 
        OLD.tech_stack, 
        OLD.pattern_type,
        OLD.agent_id, 
        OLD.metadata, 
        OLD.created_by,  -- Who originally created (best we have)
        OLD.updated_at   -- When it was last updated
    );
    
    -- Update the updated_at timestamp
    NEW.updated_at := NOW();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION save_prompt_version() IS 'v4.0: Automatic trigger to save prompt versions before UPDATE';


-- ================================================================
-- 4. TRIGGER: Auto-save version on UPDATE
-- ================================================================

DROP TRIGGER IF EXISTS prompt_version_trigger ON utm_prompts;

CREATE TRIGGER prompt_version_trigger
    BEFORE UPDATE ON utm_prompts
    FOR EACH ROW
    WHEN (OLD.content IS DISTINCT FROM NEW.content)  -- Only when content changes
    EXECUTE FUNCTION save_prompt_version();

COMMENT ON TRIGGER prompt_version_trigger ON utm_prompts IS 'v4.0: Auto-save previous version when content changes';


-- ================================================================
-- 5. INDEXES
-- ================================================================

-- Primary lookup indexes
CREATE INDEX IF NOT EXISTS idx_utm_prompts_agent 
    ON utm_prompts(agent_id) 
    WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_utm_prompts_tech 
    ON utm_prompts(tech_stack) 
    WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_utm_prompts_pattern 
    ON utm_prompts(pattern_type) 
    WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_utm_prompts_active 
    ON utm_prompts(is_active);

-- History indexes for ADMIN queries
CREATE INDEX IF NOT EXISTS idx_utm_prompts_history_prompt 
    ON utm_prompts_history(prompt_id);

CREATE INDEX IF NOT EXISTS idx_utm_prompts_history_date 
    ON utm_prompts_history(changed_at DESC);


-- ================================================================
-- 6. PERMISSIONS (NO RLS - GLOBAL PROMPTS)
-- ================================================================

-- Prompts are GLOBAL - no tenant isolation needed
-- All authenticated users can READ prompts
-- Only service_role (backend) can WRITE

GRANT SELECT ON utm_prompts TO authenticated;
GRANT SELECT ON utm_prompts TO anon;
GRANT ALL ON utm_prompts TO service_role;
GRANT ALL ON utm_prompts TO postgres;

-- History is READ-ONLY for authenticated (ADMIN can query via backend)
GRANT SELECT ON utm_prompts_history TO authenticated;
GRANT SELECT ON utm_prompts_history TO anon;
GRANT ALL ON utm_prompts_history TO service_role;
GRANT ALL ON utm_prompts_history TO postgres;


-- ================================================================
-- 7. HELPER FUNCTIONS (OPTIONAL - FOR ADMIN)
-- ================================================================

-- Function to get prompt history for a specific prompt_id
CREATE OR REPLACE FUNCTION get_prompt_history(p_prompt_id TEXT, p_limit INT DEFAULT 10)
RETURNS TABLE (
    history_id UUID,
    content TEXT,
    changed_at TIMESTAMPTZ,
    char_count INT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        h.history_id,
        h.content,
        h.changed_at,
        LENGTH(h.content) as char_count
    FROM utm_prompts_history h
    WHERE h.prompt_id = p_prompt_id
    ORDER BY h.changed_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION get_prompt_history IS 'v4.0: Get version history for a prompt (ADMIN only via backend)';


-- ================================================================
-- 8. VALIDATION
-- ================================================================

DO $$
BEGIN
    -- Verify tables exist
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'utm_prompts') THEN
        RAISE EXCEPTION 'utm_prompts table was not created';
    END IF;
    
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'utm_prompts_history') THEN
        RAISE EXCEPTION 'utm_prompts_history table was not created';
    END IF;
    
    -- Verify trigger exists
    IF NOT EXISTS (
        SELECT FROM pg_trigger 
        WHERE tgname = 'prompt_version_trigger' 
        AND tgrelid = 'utm_prompts'::regclass
    ) THEN
        RAISE EXCEPTION 'prompt_version_trigger was not created';
    END IF;
    
    RAISE NOTICE '✅ v4.0 Prompts System: Migration successful';
    RAISE NOTICE '   - utm_prompts table created';
    RAISE NOTICE '   - utm_prompts_history table created';
    RAISE NOTICE '   - Automatic versioning trigger active';
    RAISE NOTICE '   - Indexes created';
    RAISE NOTICE '   - Permissions granted';
    RAISE NOTICE '';
    RAISE NOTICE '📋 Next Step: Run scripts/init_prompts_v4.py to load initial prompts';
END $$;


-- ================================================================
-- ROLLBACK (if needed)
-- ================================================================
-- DROP TRIGGER IF EXISTS prompt_version_trigger ON utm_prompts;
-- DROP FUNCTION IF EXISTS save_prompt_version();
-- DROP FUNCTION IF EXISTS get_prompt_history(TEXT, INT);
-- DROP TABLE IF EXISTS utm_prompts_history;
-- DROP TABLE IF EXISTS utm_prompts;

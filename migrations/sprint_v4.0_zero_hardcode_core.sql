-- ================================================================
-- v4.0: Zero-Hardcode Core - Database Schema
-- ================================================================
-- Purpose:
--   Create tables for v4.0 "Zero-Hardcode Core" features:
--   1. utm_prompts - Dynamic prompts from database (global)
--   2. utm_prompts_history - Automatic versioning (read-only for ADMIN)
--   3. utm_column_profiles - Field-level forensic analysis
--   4. utm_generation_outcomes - Generation analytics and learning
--
-- Author: Legacy2Lake Engineering
-- Date: February 14, 2026 (v4.0 Sprint)
-- Version: v4.0.0
-- Reference: docs/planning/RELEASE_PLAN_v4.0_SIMPLIFIED.md
-- ================================================================


-- ================================================================
-- 0. DROP EXISTING v4.0 TABLES (Clean Migration)
-- ================================================================

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS utm_generation_outcomes CASCADE;
DROP TABLE IF EXISTS utm_column_profiles CASCADE;
DROP TABLE IF EXISTS utm_prompts_history CASCADE;
DROP TABLE IF EXISTS utm_prompts CASCADE;

-- Drop trigger function if exists
DROP FUNCTION IF EXISTS save_prompt_version() CASCADE;


-- ================================================================
-- 1. CREATE utm_prompts TABLE (Global Prompts - No Tenant Override)
-- ================================================================

CREATE TABLE IF NOT EXISTS utm_prompts (
    -- Primary key
    prompt_id TEXT PRIMARY KEY,  -- e.g., 'agent_c_bronze_pyspark'
    
    -- Prompt content
    content TEXT NOT NULL,
    
    -- Classification
    tech_stack TEXT,           -- 'pyspark', 'databricks', 'fabric', 'snowflake', 'dbt', 'bigquery', etc.
    pattern_type TEXT,         -- 'bronze', 'silver', 'gold', 'incremental', 'scd', 'generic'
    agent_id TEXT,             -- 'agent-a', 'agent-c', 'agent-f', 'agent-g', 'agent-s', 'agent-d'
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Audit
    created_by UUID REFERENCES utm_users(user_id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID REFERENCES utm_users(user_id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Metadata (flexible for future extensions)
    metadata JSONB,
    /*
    Example metadata:
    {
        "description": "Bronze layer PySpark template",
        "version": "1.0",
        "variables": ["table_name", "source_path", "schema"],
        "tags": ["production", "tested"],
        "author": "data-engineering-team",
        "last_tested": "2026-02-14T10:00:00Z"
    }
    */
    
    -- Constraints
    CONSTRAINT check_prompt_id_format CHECK (prompt_id ~ '^[a-z0-9_]+$'),
    CONSTRAINT check_prompts_agent_id_format CHECK (agent_id IS NULL OR agent_id ~ '^agent-[asfgcd]$')
);

-- Indexes for prompts
CREATE INDEX IF NOT EXISTS idx_prompts_agent_tech ON utm_prompts(agent_id, tech_stack) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_prompts_pattern ON utm_prompts(pattern_type, tech_stack) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_prompts_active ON utm_prompts(is_active) WHERE is_active = true;

-- Comments
COMMENT ON TABLE utm_prompts IS 'v4.0: Global prompts for zero-hardcode generation (no tenant customization in v4.0)';
COMMENT ON COLUMN utm_prompts.prompt_id IS 'Unique identifier: agent_id_pattern_tech (e.g., agent_c_bronze_pyspark)';
COMMENT ON COLUMN utm_prompts.content IS 'The actual LLM prompt template with {{variable}} placeholders';
COMMENT ON COLUMN utm_prompts.tech_stack IS 'Target technology: pyspark, snowflake, fabric, dbt, bigquery, redshift';
COMMENT ON COLUMN utm_prompts.pattern_type IS 'Pattern type: bronze, silver, gold, incremental, scd, generic';
COMMENT ON COLUMN utm_prompts.agent_id IS 'Agent that uses this prompt: agent-a, agent-c, agent-f, agent-g, agent-s, agent-d';


-- ================================================================
-- 2. CREATE utm_prompts_history TABLE (Automatic Versioning)
-- ================================================================

CREATE TABLE IF NOT EXISTS utm_prompts_history (
    -- Primary key
    history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Reference to original prompt
    prompt_id TEXT NOT NULL,
    
    -- Snapshot of prompt at time of change
    content TEXT NOT NULL,
    tech_stack TEXT,
    pattern_type TEXT,
    agent_id TEXT,
    metadata JSONB,
    
    -- Change tracking
    changed_by UUID REFERENCES utm_users(user_id),
    changed_at TIMESTAMPTZ DEFAULT NOW(),
    change_reason TEXT,  -- Optional: reason for change
    
    -- Previous values (for delta tracking)
    previous_content_hash TEXT,  -- SHA256 of previous content
    
    -- Constraints
    CONSTRAINT fk_prompts_history_prompt FOREIGN KEY (prompt_id) REFERENCES utm_prompts(prompt_id) ON DELETE CASCADE
);

-- Indexes for history
CREATE INDEX IF NOT EXISTS idx_prompts_history_prompt ON utm_prompts_history(prompt_id, changed_at DESC);
CREATE INDEX IF NOT EXISTS idx_prompts_history_changed_at ON utm_prompts_history(changed_at DESC);
CREATE INDEX IF NOT EXISTS idx_prompts_history_changed_by ON utm_prompts_history(changed_by);

-- Comments
COMMENT ON TABLE utm_prompts_history IS 'v4.0: Automatic version history for prompts (read-only, ADMIN access only)';
COMMENT ON COLUMN utm_prompts_history.changed_by IS 'User who triggered the update (for audit trail)';
COMMENT ON COLUMN utm_prompts_history.change_reason IS 'Optional explanation for the change';


-- ================================================================
-- 3. CREATE TRIGGER FOR AUTOMATIC VERSIONING
-- ================================================================

-- Function to save prompt version before update
CREATE OR REPLACE FUNCTION save_prompt_version()
RETURNS TRIGGER AS $$
BEGIN
    -- Only save version if content actually changed
    IF OLD.content IS DISTINCT FROM NEW.content THEN
        INSERT INTO utm_prompts_history (
            prompt_id,
            content,
            tech_stack,
            pattern_type,
            agent_id,
            metadata,
            changed_by,
            previous_content_hash
        )
        VALUES (
            OLD.prompt_id,
            OLD.content,
            OLD.tech_stack,
            OLD.pattern_type,
            OLD.agent_id,
            OLD.metadata,
            NEW.updated_by,  -- Track who made the change
            encode(digest(OLD.content, 'sha256'), 'hex')
        );
    END IF;
    
    -- Update timestamp
    NEW.updated_at = NOW();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
DROP TRIGGER IF EXISTS prompt_version_trigger ON utm_prompts;
CREATE TRIGGER prompt_version_trigger
    BEFORE UPDATE ON utm_prompts
    FOR EACH ROW
    EXECUTE FUNCTION save_prompt_version();

COMMENT ON FUNCTION save_prompt_version() IS 'v4.0: Automatically saves prompt versions to history table before updates';


-- ================================================================
-- 4. CREATE utm_column_profiles TABLE (Deep Forensic Triage)
-- ================================================================

CREATE TABLE IF NOT EXISTS utm_column_profiles (
    -- Primary key
    profile_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Project reference
    project_id UUID NOT NULL REFERENCES utm_projects(project_id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES utm_tenants(tenant_id),  -- Multi-tenant isolation
    
    -- Object and column identification
    object_id UUID,  -- Link to source object/file (optional - may reference utm_file_storage)
    object_name TEXT NOT NULL,
    column_name TEXT NOT NULL,
    column_index INT,  -- Position in table (0-based)
    
    -- Type information
    inferred_type TEXT,        -- Auto-detected: STRING, INTEGER, DECIMAL, DATE, TIMESTAMP, BOOLEAN
    declared_type TEXT,        -- From source schema if available
    type_confidence FLOAT,     -- 0.0 to 1.0 confidence in type inference
    
    -- Nullability and cardinality
    nullability_score FLOAT,   -- Percentage of null values (0.0 = no nulls, 1.0 = all nulls)
    total_rows INT,            -- Total rows analyzed
    null_count INT,            -- Count of null values
    distinct_count INT,        -- Count of distinct values
    cardinality INT,           -- Distinct count (alias for clarity)
    distinct_ratio FLOAT,      -- distinct_count / total_rows
    
    -- Semantic tags (PII detection, etc.)
    semantic_tags TEXT[],      -- ['PII', 'EMAIL', 'PHONE', 'SSN', 'CREDIT_CARD', 'ADDRESS', etc.]
    pii_detected BOOLEAN DEFAULT false,
    pii_confidence FLOAT,      -- Confidence in PII detection (0.0 to 1.0)
    
    -- Quality scoring
    quality_score INTEGER CHECK (quality_score >= 0 AND quality_score <= 100),  -- 0-100
    quality_issues TEXT[],     -- ['HIGH_NULLABILITY', 'LOW_CARDINALITY', 'INCONSISTENT_FORMAT', etc.]
    
    -- Statistical profile (JSONB for flexibility)
    statistical_profile JSONB,
    /*
    Example for numeric columns:
    {
        "min": 0,
        "max": 100000,
        "mean": 45678.90,
        "median": 45000,
        "stddev": 15234.56,
        "percentiles": {
            "p25": 30000,
            "p50": 45000,
            "p75": 60000,
            "p95": 85000,
            "p99": 95000
        },
        "outliers_count": 123
    }
    
    Example for string columns:
    {
        "min_length": 0,
        "max_length": 255,
        "avg_length": 45.6,
        "patterns": ["EMAIL", "PHONE"],
        "common_prefixes": ["Mr.", "Ms.", "Dr."],
        "encoding": "UTF-8"
    }
    */
    
    -- Detected patterns
    detected_patterns TEXT[],  -- ['EMAIL_PATTERN', 'PHONE_US', 'DATE_YYYYMMDD', etc.]
    pattern_coverage FLOAT,    -- Percentage of values matching detected patterns
    
    -- Sample values (for preview)
    sample_values JSONB,       -- Array of sample values (anonymized if PII)
    /*
    Example:
    {
        "clean_samples": ["value1", "value2", "value3"],
        "null_samples": [null, null],
        "distinct_samples": ["unique1", "unique2"],
        "top_values": [
            {"value": "common1", "count": 1000},
            {"value": "common2", "count": 500}
        ]
    }
    */
    
    -- Recommendations
    recommendations JSONB,     -- Suggested transformations, constraints, etc.
    /*
    Example:
    {
        "suggested_type": "DECIMAL(10,2)",
        "add_not_null": true,
        "add_unique_constraint": false,
        "add_check_constraint": "value >= 0",
        "transformation": "CAST(column AS DECIMAL(10,2))",
        "pii_action": "MASK"
    }
    */
    
    -- Analysis metadata
    analyzed_at TIMESTAMPTZ DEFAULT NOW(),
    analysis_duration_ms INT,
    analyzer_version TEXT DEFAULT '4.0.0',
    
    -- Unique constraint
    UNIQUE(project_id, object_name, column_name)
);

-- Indexes for column profiles
CREATE INDEX IF NOT EXISTS idx_column_profiles_project ON utm_column_profiles(project_id);
CREATE INDEX IF NOT EXISTS idx_column_profiles_tenant ON utm_column_profiles(tenant_id);
CREATE INDEX IF NOT EXISTS idx_column_profiles_object ON utm_column_profiles(object_id);
CREATE INDEX IF NOT EXISTS idx_column_profiles_pii ON utm_column_profiles(pii_detected) WHERE pii_detected = true;
CREATE INDEX IF NOT EXISTS idx_column_profiles_quality ON utm_column_profiles(quality_score);
CREATE INDEX IF NOT EXISTS idx_column_profiles_semantic ON utm_column_profiles USING GIN(semantic_tags);

-- Comments
COMMENT ON TABLE utm_column_profiles IS 'v4.0: Field-level forensic analysis with PII detection and quality scoring';
COMMENT ON COLUMN utm_column_profiles.semantic_tags IS 'Array of semantic tags: PII, EMAIL, PHONE, SSN, etc.';
COMMENT ON COLUMN utm_column_profiles.quality_score IS 'Overall quality score (0-100) based on nullability, cardinality, patterns';
COMMENT ON COLUMN utm_column_profiles.statistical_profile IS 'JSONB with min/max/mean/stddev/percentiles for numeric, length stats for strings';


-- ================================================================
-- 5. CREATE utm_generation_outcomes TABLE (Learning & Analytics)
-- ================================================================

CREATE TABLE IF NOT EXISTS utm_generation_outcomes (
    -- Primary key
    outcome_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Project reference
    project_id UUID NOT NULL REFERENCES utm_projects(project_id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES utm_tenants(tenant_id),  -- Multi-tenant isolation
    
    -- Agent and task reference
    agent_id TEXT NOT NULL,
    task_id UUID,              -- Optional: specific task that triggered generation
    node_id UUID,              -- Optional: design registry node
    object_name TEXT,
    
    -- Context (input to generation)
    context_hash TEXT NOT NULL,         -- SHA256 hash of input context (for deduplication)
    context_summary JSONB,              -- Abbreviated context for analysis
    /*
    Example:
    {
        "source_tech": "ssis",
        "target_tech": "pyspark",
        "pattern_type": "bronze",
        "column_count": 15,
        "has_transformations": true
    }
    */
    
    -- Generated output
    generated_code TEXT,
    code_length INT,
    code_hash TEXT,            -- SHA256 hash of generated code
    
    -- Prompt used
    prompt_id TEXT,            -- Reference to utm_prompts.prompt_id
    prompt_version_hash TEXT,  -- Hash of prompt content at time of generation
    
    -- Validation results
    validation_passed BOOLEAN DEFAULT false,
    validation_errors JSONB,   -- Array of validation errors/warnings
    validation_attempts INT DEFAULT 1,  -- Number of attempts needed
    
    -- Execution results (if tested)
    execution_success BOOLEAN,
    execution_errors JSONB,
    test_results JSONB,        -- Results from smoke tests
    
    -- Quality metrics
    quality_score INTEGER CHECK (quality_score >= 0 AND quality_score <= 100),
    quality_metrics JSONB,     -- Detailed quality breakdown
    
    -- LLM metrics
    model_used TEXT,           -- e.g., 'gpt-4', 'claude-3-opus'
    tokens_used INTEGER,
    tokens_prompt INTEGER,
    tokens_completion INTEGER,
    estimated_cost DECIMAL(10, 6),  -- USD
    
    -- Performance metrics
    duration_ms INTEGER,
    generation_ms INTEGER,     -- Time for LLM generation
    validation_ms INTEGER,     -- Time for validation
    
    -- Outcome classification
    outcome_type TEXT,         -- 'SUCCESS', 'VALIDATION_FAILED', 'EXECUTION_FAILED', 'TIMEOUT', 'ERROR'
    error_category TEXT,       -- If failed: 'SYNTAX', 'SEMANTIC', 'RUNTIME', 'TIMEOUT', 'UNKNOWN'
    
    -- Learning signals
    feedback_score INTEGER,    -- User feedback (1-5 stars)
    requires_manual_fix BOOLEAN DEFAULT false,
    manual_changes JSONB,      -- What was changed manually
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT check_generation_outcomes_agent_id_format CHECK (agent_id ~ '^agent-[asfgcd]$'),
    CONSTRAINT check_outcome_type CHECK (outcome_type IN ('SUCCESS', 'VALIDATION_FAILED', 'EXECUTION_FAILED', 'TIMEOUT', 'ERROR'))
);

-- Indexes for generation outcomes
CREATE INDEX IF NOT EXISTS idx_generation_outcomes_project ON utm_generation_outcomes(project_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_generation_outcomes_tenant ON utm_generation_outcomes(tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_generation_outcomes_agent ON utm_generation_outcomes(agent_id, outcome_type);
CREATE INDEX IF NOT EXISTS idx_generation_outcomes_prompt ON utm_generation_outcomes(prompt_id);
CREATE INDEX IF NOT EXISTS idx_generation_outcomes_context_hash ON utm_generation_outcomes(context_hash);
CREATE INDEX IF NOT EXISTS idx_generation_outcomes_quality ON utm_generation_outcomes(quality_score);
CREATE INDEX IF NOT EXISTS idx_generation_outcomes_validation ON utm_generation_outcomes(validation_passed);

-- Comments
COMMENT ON TABLE utm_generation_outcomes IS 'v4.0: Track all generation attempts for analytics and self-learning';
COMMENT ON COLUMN utm_generation_outcomes.context_hash IS 'SHA256 hash of input context for deduplication';
COMMENT ON COLUMN utm_generation_outcomes.validation_attempts IS 'Number of attempts needed to pass validation (for auto-correction loop)';
COMMENT ON COLUMN utm_generation_outcomes.feedback_score IS 'User feedback (1-5 stars) for quality improvement';


-- ================================================================
-- 6. ENABLE ROW-LEVEL SECURITY (RLS)
-- ================================================================

-- Note: RLS policies commented out for initial migration
-- Uncomment and customize after tables are created and tested
-- These would need to be adapted based on your authentication system

/*
-- Enable RLS on new tables
ALTER TABLE utm_prompts ENABLE ROW LEVEL SECURITY;
ALTER TABLE utm_prompts_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE utm_column_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE utm_generation_outcomes ENABLE ROW LEVEL SECURITY;

-- RLS Policies for utm_prompts (global, but admin-only edit)
-- All authenticated users can read active prompts
CREATE POLICY "Allow read active prompts" ON utm_prompts
    FOR SELECT
    USING (is_active = true);

-- Only admins can insert/update/delete prompts
CREATE POLICY "Allow admin manage prompts" ON utm_prompts
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM utm_users
            WHERE id = auth.uid()
            AND role = 'admin'
        )
    );

-- RLS Policies for utm_prompts_history (admin-only read)
CREATE POLICY "Allow admin read prompt history" ON utm_prompts_history
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM utm_users
            WHERE id = auth.uid()
            AND role = 'admin'
        )
    );

-- RLS Policies for utm_column_profiles (multi-tenant)
CREATE POLICY "Column profiles multi-tenant read" ON utm_column_profiles
    FOR SELECT
    USING (
        tenant_id IN (
            SELECT tenant_id FROM utm_users WHERE id = auth.uid()
        )
    );

CREATE POLICY "Column profiles multi-tenant write" ON utm_column_profiles
    FOR ALL
    USING (
        tenant_id IN (
            SELECT tenant_id FROM utm_users WHERE id = auth.uid()
        )
    );

-- RLS Policies for utm_generation_outcomes (multi-tenant)
CREATE POLICY "Generation outcomes multi-tenant read" ON utm_generation_outcomes
    FOR SELECT
    USING (
        tenant_id IN (
            SELECT tenant_id FROM utm_users WHERE id = auth.uid()
        )
    );

CREATE POLICY "Generation outcomes multi-tenant write" ON utm_generation_outcomes
    FOR ALL
    USING (
        tenant_id IN (
            SELECT tenant_id FROM utm_users WHERE id = auth.uid()
        )
    );
*/


-- ================================================================
-- 7. GRANT PERMISSIONS
-- ================================================================

-- Grant permissions to application role (adjust role name as needed)
-- GRANT SELECT, INSERT, UPDATE ON utm_prompts TO authenticated;
-- GRANT SELECT ON utm_prompts_history TO authenticated;
-- GRANT ALL ON utm_column_profiles TO authenticated;
-- GRANT ALL ON utm_generation_outcomes TO authenticated;


-- ================================================================
-- 8. SEED DATA - INITIAL PROMPTS (Example)
-- ================================================================

-- Note: Actual prompt templates should be migrated from existing hardcoded templates
-- This is just a placeholder structure

INSERT INTO utm_prompts (prompt_id, content, tech_stack, pattern_type, agent_id, metadata) VALUES
(
    'agent_c_bronze_pyspark_generic',
    'Generate a PySpark bronze layer ingestion script for the following source table...',
    'pyspark',
    'bronze',
    'agent-c',
    '{"description": "Generic bronze layer PySpark template", "version": "4.0.0", "tags": ["production"]}'
) ON CONFLICT (prompt_id) DO NOTHING;

-- More seed prompts will be added during migration from hardcoded templates


-- ================================================================
-- 9. MIGRATION NOTES
-- ================================================================

/*
MIGRATION CHECKLIST:

1. ✅ Create new tables:
   - utm_prompts (global prompts)
   - utm_prompts_history (automatic versioning)
   - utm_column_profiles (field-level analysis)
   - utm_generation_outcomes (learning data)

2. ⏳ Migrate existing hardcoded templates:
   - Extract templates from Agent C code
   - Convert to database records in utm_prompts
   - Test generation with DB-based prompts
   - Remove hardcoded templates from code

3. ⏳ Update application code:
   - Create PromptService for DB access
   - Create PromptAssembler for context injection
   - Refactor Agent C to use dynamic prompts
   - Add caching layer for prompts

4. ⏳ Testing:
   - Verify prompt loading
   - Test versioning trigger
   - Validate multi-tenant isolation
   - Performance testing

5. ⏳ Documentation:
   - Update API documentation
   - Create prompt authoring guide
   - Document versioning behavior
   - Create migration runbook

ROLLBACK PLAN:
- Keep this migration in a transaction
- To rollback: DROP TABLE utm_generation_outcomes, utm_column_profiles, utm_prompts_history, utm_prompts CASCADE;
- Revert application code to use hardcoded templates
*/

-- ================================================================
-- END OF MIGRATION
-- ================================================================

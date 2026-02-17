-- ============================================
-- Phase A: Quick Assessment Service
-- Sprint 14 - v4.0
-- Date: 2026-02-15
-- ============================================

-- ============================================
-- 1. Add Agent QA to Agent Catalog
-- ============================================

INSERT INTO utm_agent_catalog (agent_id, name, display_name, description, role_description, is_active)
VALUES (
    'agent-qa',
    'Agent QA (Quick Assessment)',
    'Quick Assessment Agent',
    'Provides fast hybrid evaluation (deterministic + LLM) of project viability before running full Triage pipeline. Classifies files, calculates viability score, and identifies blockers.',
    'Pre-Migration Viability Assessor',
    TRUE
)
ON CONFLICT (agent_id) DO UPDATE SET
    name = EXCLUDED.name,
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    role_description = EXCLUDED.role_description,
    is_active = EXCLUDED.is_active;

-- ============================================
-- 2. Add quick_assessment column to projects
-- ============================================

-- Add JSONB column to store quick assessment results
ALTER TABLE utm_projects 
ADD COLUMN IF NOT EXISTS quick_assessment JSONB DEFAULT NULL;

-- Add index for querying by semaphore status
CREATE INDEX IF NOT EXISTS idx_projects_qa_semaphore 
ON utm_projects ((quick_assessment->>'semaforo'));

-- Add index for querying by score
CREATE INDEX IF NOT EXISTS idx_projects_qa_score 
ON utm_projects (((quick_assessment->>'score')::integer));

-- ============================================
-- 3. Add helper function to get QA summary
-- ============================================

CREATE OR REPLACE FUNCTION get_qa_summary(p_project_id UUID)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'project_id', project_id,
        'project_name', name,
        'score', (quick_assessment->>'score')::integer,
        'semaforo', quick_assessment->>'semaforo',
        'total_files', (quick_assessment->>'total_files')::integer,
        'detected_techs', quick_assessment->'detected_techs',
        'assessed_at', quick_assessment->>'assessed_at'
    )
    INTO result
    FROM utm_projects
    WHERE project_id = p_project_id;
    
    RETURN result;
END;
$$;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION get_qa_summary(UUID) TO authenticated, service_role;

-- ============================================
-- 4. Verification queries
-- ============================================

-- Verify agent-qa was added
SELECT 
    agent_id,
    display_name,
    LEFT(description, 80) as description_preview,
    is_active
FROM utm_agent_catalog
WHERE agent_id = 'agent-qa';

-- Verify column was added
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'utm_projects' 
AND column_name = 'quick_assessment';

-- Show sample QA data structure (if any projects have it)
SELECT 
    project_id,
    name,
    jsonb_pretty(quick_assessment) as qa_result
FROM utm_projects
WHERE quick_assessment IS NOT NULL
LIMIT 1;

-- ============================================
-- Comments
-- ============================================

COMMENT ON COLUMN utm_projects.quick_assessment IS 
'Quick Assessment result (JSONB): score, semaforo, file_breakdown, detected_techs, blockers, llm_opinion, assessed_at';

COMMENT ON FUNCTION get_qa_summary(UUID) IS 
'Returns a compact summary of the Quick Assessment for a project';

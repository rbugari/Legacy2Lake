-- Migration: Add solution context table for user-specific prompt customization
-- This allows users to inject custom context per solution without modifying base prompts

CREATE TABLE utm_solution_context (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES utm_projects(project_id) ON DELETE CASCADE,
    context_type VARCHAR(50) NOT NULL, -- 'agent_a', 'agent_c', 'agent_f', 'agent_g', 'global'
    user_context TEXT, -- User-editable context injected into agent prompts
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure unique context type per project
    CONSTRAINT unique_context_per_project UNIQUE (project_id, context_type)
);

-- Index for fast lookups
CREATE INDEX idx_solution_context_project ON utm_solution_context(project_id);

-- RLS policies (following existing pattern)
ALTER TABLE utm_solution_context ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to manage their own project contexts
CREATE POLICY solution_context_select ON utm_solution_context
    FOR SELECT USING (true);

CREATE POLICY solution_context_insert ON utm_solution_context
    FOR INSERT WITH CHECK (true);

CREATE POLICY solution_context_update ON utm_solution_context
    FOR UPDATE USING (true);

CREATE POLICY solution_context_delete ON utm_solution_context
    FOR DELETE USING (true);

-- Add comment for documentation
COMMENT ON TABLE utm_solution_context IS 'Stores user-specific context injected into agent prompts per solution';
COMMENT ON COLUMN utm_solution_context.context_type IS 'Type of agent or global context';
COMMENT ON COLUMN utm_solution_context.user_context IS 'User-editable markdown/text injected into system prompts';

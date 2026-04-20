-- ================================================================
-- Sprint 2: Post-Drafting Mode Branching
-- ================================================================
-- Purpose:
--   Add project-level field to persist user's post-Drafting choice.
--   Allows Drafting to be a terminal path or branch to Refinement.
--
-- Date: April 10, 2026
-- Version: Sprint 2
-- Reference: docs/planning/V4_3_SPRINT_2_DRAFTING_BRANCHING_AND_TERMINAL_PATH.md
-- ================================================================

-- 1. Add post_drafting_mode column to utm_projects
-- Valid values: 'drafting_delivery', 'structured_refinement', 'intelligent_reengineering'
-- Nullable initially (means not yet decided)
ALTER TABLE utm_projects
  ADD COLUMN IF NOT EXISTS post_drafting_mode VARCHAR(50) 
    CHECK (post_drafting_mode IN ('drafting_delivery', 'structured_refinement', 'intelligent_reengineering'));

-- 2. Add timestamp to track when decision was made
ALTER TABLE utm_projects
  ADD COLUMN IF NOT EXISTS post_drafting_mode_set_at TIMESTAMPTZ;

-- 3. Index for querying projects by mode
CREATE INDEX IF NOT EXISTS idx_utm_projects_post_drafting_mode
  ON utm_projects (post_drafting_mode)
  WHERE post_drafting_mode IS NOT NULL;

-- 4. Comment for clarity
COMMENT ON COLUMN utm_projects.post_drafting_mode IS 
  'User choice after Drafting completes: drafting_delivery (terminal), structured_refinement (continue refinement), or intelligent_reengineering (advanced paths)';

COMMENT ON COLUMN utm_projects.post_drafting_mode_set_at IS 
  'Timestamp when user selected the post-Drafting mode';

-- 5. Grant permissions
GRANT SELECT, UPDATE ON utm_projects TO service_role;

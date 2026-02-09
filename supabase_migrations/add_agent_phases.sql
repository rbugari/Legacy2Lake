-- Migration: Add phases column to utm_agent_catalog
-- Track which project phases each agent participates in
-- Date: 2026-02-09

-- Add phases column (array of text for multiple phases)
ALTER TABLE utm_agent_catalog 
ADD COLUMN phases TEXT[] DEFAULT '{}';

-- Update agents with their respective phases
-- Based on STAGE_MAP and system architecture

-- Phase 1: Discovery/Ingest
UPDATE utm_agent_catalog 
SET phases = ARRAY['discovery']
WHERE agent_id = 'agent-s';

-- Phase 2: Triage
UPDATE utm_agent_catalog 
SET phases = ARRAY['triage']
WHERE agent_id IN ('agent-s', 'agent-a');

-- agent-s works in both discovery and triage
UPDATE utm_agent_catalog 
SET phases = ARRAY['discovery', 'triage']
WHERE agent_id = 'agent-s';

-- Phase 3: Drafting
UPDATE utm_agent_catalog 
SET phases = ARRAY['drafting']
WHERE agent_id IN ('agent-b', 'agent-c');

-- Phase 4: Refinement
UPDATE utm_agent_catalog 
SET phases = ARRAY['refinement']
WHERE agent_id IN ('agent-p', 'agent-r', 'agent-o');

-- agent-f works in both drafting and refinement
UPDATE utm_agent_catalog 
SET phases = ARRAY['drafting', 'refinement']
WHERE agent_id = 'agent-f';

-- Phase 5: Certification/Governance (Cross-cutting)
UPDATE utm_agent_catalog 
SET phases = ARRAY['certification', 'governance']
WHERE agent_id = 'agent-g';

-- agent-d (Architectural Auditor) works in certification
UPDATE utm_agent_catalog 
SET phases = ARRAY['certification']
WHERE agent_id = 'agent-d';

-- Verify updates
SELECT 
    agent_id,
    display_name,
    phases,
    array_length(phases, 1) as phase_count,
    is_active
FROM utm_agent_catalog
ORDER BY agent_id;

-- Show agents grouped by phase
SELECT 
    phase,
    array_agg(agent_id ORDER BY agent_id) as agents,
    count(*) as agent_count
FROM (
    SELECT agent_id, unnest(phases) as phase
    FROM utm_agent_catalog
    WHERE is_active = TRUE
) sub
GROUP BY phase
ORDER BY 
    CASE phase
        WHEN 'discovery' THEN 1
        WHEN 'triage' THEN 2
        WHEN 'drafting' THEN 3
        WHEN 'refinement' THEN 4
        WHEN 'certification' THEN 5
        WHEN 'governance' THEN 6
        ELSE 99
    END;

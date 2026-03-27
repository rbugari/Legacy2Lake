-- Sprint 0: Knowledge Model Foundation
-- This migration creates the core tables for the v5 knowledge model to support tech-agnostic data structures.

-- 1. utm_solutions: Grouping multiple projects under one solution
CREATE TABLE IF NOT EXISTS utm_solutions (
  solution_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES utm_tenants(tenant_id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Note: RLS policies for utm_solutions
ALTER TABLE utm_solutions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view solutions in their tenant" ON utm_solutions
  FOR SELECT USING (tenant_id IN (SELECT tenant_id FROM utm_users WHERE user_id = auth.uid()));
CREATE POLICY "Users can insert solutions in their tenant" ON utm_solutions
  FOR INSERT WITH CHECK (tenant_id IN (SELECT tenant_id FROM utm_users WHERE user_id = auth.uid() AND role IN ('admin', 'editor')));
CREATE POLICY "Users can update solutions in their tenant" ON utm_solutions
  FOR UPDATE USING (tenant_id IN (SELECT tenant_id FROM utm_users WHERE user_id = auth.uid() AND role IN ('admin', 'editor')));
CREATE POLICY "Users can delete solutions in their tenant" ON utm_solutions
  FOR DELETE USING (tenant_id IN (SELECT tenant_id FROM utm_users WHERE user_id = auth.uid() AND role = 'admin'));

-- 2. Modify utm_projects to link to solutions and declare the intent
ALTER TABLE utm_projects 
  ADD COLUMN IF NOT EXISTS solution_id UUID REFERENCES utm_solutions(solution_id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS intent TEXT DEFAULT 'migration' CHECK (intent IN ('analysis', 'migration', 'governance', 'mixed'));

-- 3. utm_evidence_items: Traceability
CREATE TABLE IF NOT EXISTS utm_evidence_items (
  evidence_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES utm_projects(project_id) ON DELETE CASCADE,
  solution_id UUID REFERENCES utm_solutions(solution_id) ON DELETE CASCADE,
  tenant_id UUID NOT NULL REFERENCES utm_tenants(tenant_id) ON DELETE CASCADE,
  asset_id UUID REFERENCES utm_objects(object_id) ON DELETE SET NULL,
  source_path TEXT NOT NULL,
  source_block_type TEXT, -- e.g., 'function', 'query', 'control_flow_step', 'config_block'
  snippet TEXT,
  line_start INT,
  line_end INT,
  parser_name TEXT, -- e.g., 'SSISCartridge', 'LibrarianService', 'SparkCartridge'
  extraction_method TEXT NOT NULL CHECK (extraction_method IN ('parser_deterministic', 'llm_inference', 'heuristic', 'human_override')),
  confidence FLOAT CHECK (confidence BETWEEN 0.0 AND 1.0),
  rationale TEXT, -- Required if llm_inference
  run_id UUID, -- Triage run ID
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_evidence_project ON utm_evidence_items(project_id);
CREATE INDEX IF NOT EXISTS idx_evidence_asset ON utm_evidence_items(asset_id);
ALTER TABLE utm_evidence_items ENABLE ROW LEVEL SECURITY;

-- 4. utm_processes: High-level logical boundaries
CREATE TABLE IF NOT EXISTS utm_processes (
  process_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES utm_projects(project_id) ON DELETE CASCADE,
  solution_id UUID REFERENCES utm_solutions(solution_id) ON DELETE CASCADE,
  tenant_id UUID NOT NULL REFERENCES utm_tenants(tenant_id) ON DELETE CASCADE,
  asset_id UUID REFERENCES utm_objects(object_id) ON DELETE SET NULL,
  process_type TEXT, -- e.g., 'ingestion', 'transform', 'publish', 'orchestration', 'control', 'validation'
  name TEXT NOT NULL,
  logical_name TEXT,
  description TEXT,
  trigger_type TEXT, -- e.g., 'scheduled', 'event', 'manual', 'dependency'
  schedule_hint TEXT,
  error_handling_hint TEXT,
  operational_importance TEXT, -- e.g., 'critical', 'high', 'medium', 'low'
  extraction_method TEXT,
  confidence FLOAT,
  evidence_refs UUID[], -- Array of evidence_ids references
  run_id UUID,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_processes_project ON utm_processes(project_id);
CREATE INDEX IF NOT EXISTS idx_processes_asset ON utm_processes(asset_id);
ALTER TABLE utm_processes ENABLE ROW LEVEL SECURITY;

-- 5. utm_orchestration_steps: Detailed execution flow
CREATE TABLE IF NOT EXISTS utm_orchestration_steps (
  step_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  process_id UUID NOT NULL REFERENCES utm_processes(process_id) ON DELETE CASCADE,
  project_id UUID NOT NULL REFERENCES utm_projects(project_id) ON DELETE CASCADE,
  tenant_id UUID NOT NULL REFERENCES utm_tenants(tenant_id) ON DELETE CASCADE,
  step_type TEXT, -- e.g., 'execute_package', 'sql_task', 'script_task', 'data_flow'
  name TEXT,
  order_hint INT,
  depends_on_steps UUID[], -- Array of other step_ids
  input_refs TEXT[],
  output_refs TEXT[],
  branching_hint TEXT,
  retry_policy_hint TEXT,
  timeout_hint TEXT,
  extraction_method TEXT,
  confidence FLOAT,
  evidence_refs UUID[],
  run_id UUID,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_orch_steps_process ON utm_orchestration_steps(process_id);
ALTER TABLE utm_orchestration_steps ENABLE ROW LEVEL SECURITY;

-- 6. utm_operational_constraints: Schedules, retry policies, data rules
CREATE TABLE IF NOT EXISTS utm_operational_constraints (
  constraint_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  process_id UUID REFERENCES utm_processes(process_id) ON DELETE CASCADE,
  step_id UUID REFERENCES utm_orchestration_steps(step_id) ON DELETE CASCADE,
  project_id UUID NOT NULL REFERENCES utm_projects(project_id) ON DELETE CASCADE,
  tenant_id UUID NOT NULL REFERENCES utm_tenants(tenant_id) ON DELETE CASCADE,
  constraint_type TEXT NOT NULL CHECK (constraint_type IN ('schedule', 'trigger', 'retry', 'timeout', 'watermark', 'incremental_boundary', 'dependency_gate')),
  value_hint TEXT,
  severity TEXT, -- 'critical', 'warning', 'info'
  extraction_method TEXT,
  confidence FLOAT,
  evidence_refs UUID[],
  run_id UUID,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_constraints_process ON utm_operational_constraints(process_id);
ALTER TABLE utm_operational_constraints ENABLE ROW LEVEL SECURITY;

-- 7. utm_rule_signals: Reusable intelligence
CREATE TABLE IF NOT EXISTS utm_rule_signals (
  signal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES utm_projects(project_id) ON DELETE CASCADE,
  solution_id UUID REFERENCES utm_solutions(solution_id) ON DELETE CASCADE,
  tenant_id UUID NOT NULL REFERENCES utm_tenants(tenant_id) ON DELETE CASCADE,
  signal_type TEXT NOT NULL CHECK (signal_type IN ('mapping', 'grouping', 'parameter', 'default', 'exception')),
  probable_scope TEXT, -- 'local', 'cross_asset', 'cross_project'
  probable_reusability TEXT, -- 'high', 'medium', 'low', 'not_reusable'
  source_field TEXT,
  target_field TEXT,
  literals_detected TEXT[],
  rationale TEXT,
  confidence FLOAT,
  status TEXT DEFAULT 'candidate' CHECK (status IN ('candidate', 'accepted', 'rejected', 'promoted')),
  evidence_refs UUID[],
  run_id UUID,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_signals_project ON utm_rule_signals(project_id);
ALTER TABLE utm_rule_signals ENABLE ROW LEVEL SECURITY;

-- 8. utm_knowledge_snapshots: Frozen states of triage runs
CREATE TABLE IF NOT EXISTS utm_knowledge_snapshots (
  snapshot_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES utm_projects(project_id) ON DELETE CASCADE,
  tenant_id UUID NOT NULL REFERENCES utm_tenants(tenant_id) ON DELETE CASCADE,
  run_id UUID NOT NULL,
  snapshot_type TEXT, -- 'triage', 'analysis', 'post_review'
  storage_key TEXT, -- Path in R2/storage to the JSON file
  stats JSONB, -- {process_count, step_count, evidence_count, confidence_avg}
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_snapshots_project ON utm_knowledge_snapshots(project_id);
ALTER TABLE utm_knowledge_snapshots ENABLE ROW LEVEL SECURITY;

-- Shared RLS Policies for the new knowledge model tables (simplified view-all-in-tenant approach)
-- In production, you might restrict this further by project membership
DO $$
DECLARE
  table_name TEXT;
BEGIN
  FOR table_name IN SELECT UNNEST(ARRAY[
    'utm_evidence_items', 'utm_processes', 'utm_orchestration_steps', 
    'utm_operational_constraints', 'utm_rule_signals', 'utm_knowledge_snapshots'
  ])
  LOOP
    EXECUTE format('CREATE POLICY "Users can view %I in their tenant" ON %I FOR SELECT USING (tenant_id IN (SELECT tenant_id FROM utm_users WHERE user_id = auth.uid()))', table_name, table_name);
    EXECUTE format('CREATE POLICY "Users can insert %I in their tenant" ON %I FOR INSERT WITH CHECK (tenant_id IN (SELECT tenant_id FROM utm_users WHERE user_id = auth.uid() AND role IN (''admin'', ''editor'')))', table_name, table_name);
    EXECUTE format('CREATE POLICY "Users can update %I in their tenant" ON %I FOR UPDATE USING (tenant_id IN (SELECT tenant_id FROM utm_users WHERE user_id = auth.uid() AND role IN (''admin'', ''editor'')))', table_name, table_name);
    EXECUTE format('CREATE POLICY "Users can delete %I in their tenant" ON %I FOR DELETE USING (tenant_id IN (SELECT tenant_id FROM utm_users WHERE user_id = auth.uid() AND role = ''admin''))', table_name, table_name);
  END LOOP;
END
$$;

-- Migration Script: Release 3.5 Schema Standardization
-- 1. Standardize Table Names (utm_ prefix)
-- 2. Create Persistence Tables (execution_logs, file_inventory)

DO $$
BEGIN
  -- Rename 'transformations' -> 'utm_transformations'
  IF EXISTS(SELECT * FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'transformations') THEN
    ALTER TABLE public.transformations RENAME TO utm_transformations;
  END IF;

  -- Rename 'asset_context' -> 'utm_asset_context'
  IF EXISTS(SELECT * FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'asset_context') THEN
    ALTER TABLE public.asset_context RENAME TO utm_asset_context;
  END IF;

  -- Rename 'design_registry' -> 'utm_design_registry'
  IF EXISTS(SELECT * FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'design_registry') THEN
    ALTER TABLE public.design_registry RENAME TO utm_design_registry;
  END IF;
END $$;

-- Create utm_execution_logs
CREATE TABLE IF NOT EXISTS public.utm_execution_logs (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  project_id uuid REFERENCES public.utm_projects(project_id) ON DELETE CASCADE,
  phase text NOT NULL, -- 'TRIAGE', 'MIGRATION', 'REFINEMENT'
  step text, -- 'PROFILER', 'ARCHITECT', etc.
  message text NOT NULL,
  level text DEFAULT 'INFO',
  created_at timestamptz DEFAULT now()
);

-- Enable RLS for logs (Optional, but good practice if using Auth)
ALTER TABLE public.utm_execution_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow Service Role" ON public.utm_execution_logs USING (true) WITH CHECK (true);


-- Create utm_file_inventory
CREATE TABLE IF NOT EXISTS public.utm_file_inventory (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  project_id uuid REFERENCES public.utm_projects(project_id) ON DELETE CASCADE,
  file_path text NOT NULL,
  file_hash text,
  size_bytes bigint,
  last_modified timestamptz,
  is_directory boolean DEFAULT false,
  UNIQUE(project_id, file_path)
);

-- Enable RLS for inventory
ALTER TABLE public.utm_file_inventory ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow Service Role" ON public.utm_file_inventory USING (true) WITH CHECK (true);

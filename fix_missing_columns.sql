-- Run this in the Supabase SQL Editor to support Release 1.2/1.3 metadata
ALTER TABLE public.assets ADD COLUMN IF NOT EXISTS frequency text DEFAULT 'DAILY';
ALTER TABLE public.assets ADD COLUMN IF NOT EXISTS load_strategy text DEFAULT 'FULL_OVERWRITE';
ALTER TABLE public.assets ADD COLUMN IF NOT EXISTS criticality text DEFAULT 'P3';
ALTER TABLE public.assets ADD COLUMN IF NOT EXISTS is_pii boolean DEFAULT false;
ALTER TABLE public.assets ADD COLUMN IF NOT EXISTS masking_rule text;
ALTER TABLE public.assets ADD COLUMN IF NOT EXISTS business_entity text;
ALTER TABLE public.assets ADD COLUMN IF NOT EXISTS target_name text;

-- Force config reload
NOTIFY pgrst, 'reload config';

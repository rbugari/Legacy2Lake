-- Sprint 14: Understanding columns on utm_projects
-- Adds dedicated JSONB/timestamp/text columns so the Understanding service
-- can persist its payload without using the settings fallback.
--
-- Before applying, verify the utm_projects table exists:
--   SELECT column_name FROM information_schema.columns
--   WHERE table_name = 'utm_projects';
--
-- Apply once per environment (idempotent via IF NOT EXISTS guards).

-- 1. Payload column (stores the full understanding object built by UnderstandingService)
ALTER TABLE utm_projects
  ADD COLUMN IF NOT EXISTS understanding_payload JSONB;

-- 2. Generation timestamp (ISO-8601 string captured at build time)
ALTER TABLE utm_projects
  ADD COLUMN IF NOT EXISTS understanding_generated_at TIMESTAMPTZ;

-- 3. Schema version (e.g. "v1" — allows future migrations to detect stale payloads)
ALTER TABLE utm_projects
  ADD COLUMN IF NOT EXISTS understanding_version TEXT;

-- 4. Index for efficiently fetching projects with an understanding snapshot
CREATE INDEX IF NOT EXISTS idx_utm_projects_understanding_generated_at
  ON utm_projects (understanding_generated_at)
  WHERE understanding_generated_at IS NOT NULL;

-- 5. Grant read/write to the service role used by Supabase PostgREST
-- (adjust role name to match your Supabase project if different from 'service_role')
GRANT SELECT, UPDATE ON utm_projects TO service_role;

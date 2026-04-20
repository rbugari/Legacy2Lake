-- v4.5 Migration: Chat History + Traceability tables
-- Run against Supabase production project

-- ============================================================
-- Table: utm_project_chat_threads
-- ============================================================
CREATE TABLE IF NOT EXISTS utm_project_chat_threads (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id     UUID NOT NULL,
    project_id    UUID NOT NULL,
    thread_version INTEGER NOT NULL DEFAULT 1,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_threads_project
    ON utm_project_chat_threads (tenant_id, project_id);

-- ============================================================
-- Table: utm_project_chat_messages
-- ============================================================
CREATE TABLE IF NOT EXISTS utm_project_chat_messages (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id     UUID NOT NULL,
    project_id    UUID NOT NULL,
    thread_id     UUID NOT NULL REFERENCES utm_project_chat_threads(id) ON DELETE CASCADE,
    role          TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    intent        TEXT,
    question      TEXT,
    answer        TEXT,
    evidence_refs JSONB,
    confidence    TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_thread
    ON utm_project_chat_messages (thread_id, created_at);

CREATE INDEX IF NOT EXISTS idx_chat_messages_project
    ON utm_project_chat_messages (tenant_id, project_id, created_at);

-- ============================================================
-- RLS
-- ============================================================
ALTER TABLE utm_project_chat_threads ENABLE ROW LEVEL SECURITY;
ALTER TABLE utm_project_chat_messages ENABLE ROW LEVEL SECURITY;

-- Authenticated users see only their tenant's data
CREATE POLICY "tenant_chat_threads" ON utm_project_chat_threads
    FOR ALL USING (tenant_id = (auth.jwt() ->> 'tenant_id')::UUID);

CREATE POLICY "tenant_chat_messages" ON utm_project_chat_messages
    FOR ALL USING (tenant_id = (auth.jwt() ->> 'tenant_id')::UUID);

-- Service role bypass
GRANT ALL ON utm_project_chat_threads TO service_role;
GRANT ALL ON utm_project_chat_messages TO service_role;
GRANT ALL ON utm_project_chat_threads TO authenticated;
GRANT ALL ON utm_project_chat_messages TO authenticated;

-- ============================================================
-- Table: utm_asset_traceability
-- Stores per-asset legacy-to-target traceability map
-- ============================================================
CREATE TABLE IF NOT EXISTS utm_asset_traceability (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id     UUID NOT NULL,
    project_id    UUID NOT NULL,
    asset_id      UUID NOT NULL,
    asset_name    TEXT,
    entries       JSONB NOT NULL DEFAULT '[]',
    computed_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (project_id, asset_id)
);

CREATE INDEX IF NOT EXISTS idx_traceability_project
    ON utm_asset_traceability (tenant_id, project_id);

ALTER TABLE utm_asset_traceability ENABLE ROW LEVEL SECURITY;

CREATE POLICY "tenant_traceability" ON utm_asset_traceability
    FOR ALL USING (tenant_id = (auth.jwt() ->> 'tenant_id')::UUID);

GRANT ALL ON utm_asset_traceability TO service_role;
GRANT ALL ON utm_asset_traceability TO authenticated;

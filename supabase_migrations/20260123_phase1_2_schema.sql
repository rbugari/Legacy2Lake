-- Migration: Phase 1.2 Provider Vault & Simple Auth
-- Created: 2026-01-23
-- Description: Adds clients, tenants (simple auth), and provider vault.

-- 1. Identity Tables (Simple Auth for MVP)
CREATE TABLE IF NOT EXISTS utm_clients (
    client_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS utm_tenants (
    tenant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES utm_clients(client_id),
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL, -- Simple hash for MVP or bcrypt
    role TEXT DEFAULT 'USER',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- 2. Provider Vault (Encrypted Storage Conceptual - storing plain with warning for MVP/Proto)
-- In prod, use pgcrypto. For now, we store as text but application layer should handle encryption hooks if needed.
CREATE TABLE IF NOT EXISTS utm_provider_vault (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES utm_tenants(tenant_id),
    provider_name TEXT NOT NULL, -- 'azure', 'anthropic', 'groq'
    api_key TEXT NOT NULL,       -- Storing plaintext for this prototypes stage, move to Vault later
    base_url TEXT,
    model_name TEXT,             -- Default model for this provider context
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(tenant_id, provider_name)
);

-- 3. Model Catalog (Technical Registry)
CREATE TABLE IF NOT EXISTS utm_model_catalog (
    model_id TEXT PRIMARY KEY, -- 'gpt-4o', 'claude-3-5-sonnet'
    provider TEXT NOT NULL,
    context_window INT,
    input_price_1k NUMERIC,
    output_price_1k NUMERIC,
    description TEXT
);

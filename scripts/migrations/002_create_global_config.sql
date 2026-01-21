CREATE TABLE IF NOT EXISTS utm_global_config (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Seed defaults
INSERT INTO utm_global_config (key, value) VALUES
('cartridges', '{"pyspark": {"enabled": true}, "dbt": {"enabled": true}, "sql": {"enabled": false}}'::jsonb),
('provider_settings', '{"azure": {"enabled": true, "model": "gpt-4"}, "anthropic": {"enabled": false}}'::jsonb),
('organization', '{"name": "My Company", "region": "us-east-1"}'::jsonb)
ON CONFLICT (key) DO NOTHING;

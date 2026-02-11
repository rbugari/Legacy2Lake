-- Sprint 6: Audit Log Table Migration
-- Creates utm_audit_log table for security and compliance logging

-- Drop existing table if it exists (clean slate)
DROP TABLE IF EXISTS utm_audit_log CASCADE;

-- Create audit log table
CREATE TABLE utm_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('info', 'warning', 'error', 'critical')),
    message TEXT NOT NULL,
    tenant_id UUID REFERENCES utm_tenants(tenant_id) ON DELETE SET NULL,
    user_id UUID,
    ip_address VARCHAR(50),
    endpoint VARCHAR(500),
    method VARCHAR(10),
    status_code INTEGER,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON utm_audit_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_event_type ON utm_audit_log(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_log_severity ON utm_audit_log(severity);
CREATE INDEX IF NOT EXISTS idx_audit_log_tenant_id ON utm_audit_log(tenant_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_ip_address ON utm_audit_log(ip_address);

-- Index for attack pattern detection
CREATE INDEX IF NOT EXISTS idx_audit_log_attacks ON utm_audit_log(timestamp DESC, event_type) 
WHERE event_type IN ('sql_injection_attempt', 'xss_attempt', 'path_traversal_attempt', 'auth_failure');

-- Enable Row Level Security
ALTER TABLE utm_audit_log ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Service role can see all logs
CREATE POLICY audit_log_service_role 
ON utm_audit_log 
FOR ALL 
TO service_role 
USING (true);

-- RLS Policy: Authenticated users can only see their tenant's logs
CREATE POLICY audit_log_tenant_isolation 
ON utm_audit_log 
FOR SELECT 
TO authenticated 
USING (tenant_id = (auth.jwt() ->> 'tenant_id')::uuid);

-- RLS Policy: Admins can see all logs
CREATE POLICY audit_log_admin_access 
ON utm_audit_log 
FOR SELECT 
TO authenticated 
USING (
    EXISTS (
        SELECT 1 FROM utm_users 
        WHERE utm_users.user_id::text = auth.jwt() ->> 'user_id' 
        AND utm_users.role = 'ADMIN'
    )
);

-- Grant permissions
GRANT SELECT ON utm_audit_log TO authenticated;
GRANT ALL ON utm_audit_log TO service_role;

-- Comment table
COMMENT ON TABLE utm_audit_log IS 'Sprint 6: Audit log for security events, compliance, and forensics. Tracks auth attempts, API requests, and security violations.';

-- Comment columns
COMMENT ON COLUMN utm_audit_log.event_type IS 'Type of event: auth_success, auth_failure, sql_injection_attempt, rate_limit_exceeded, etc.';
COMMENT ON COLUMN utm_audit_log.severity IS 'Severity level: info, warning, error, critical';
COMMENT ON COLUMN utm_audit_log.metadata IS 'Additional context as JSON (attack details, request info, etc.)';
COMMENT ON COLUMN utm_audit_log.ip_address IS 'Masked client IP (first 2 octets or hashed)';

-- Verify table creation
SELECT 
    'utm_audit_log' AS table_name,
    COUNT(*) AS initial_row_count,
    pg_size_pretty(pg_total_relation_size('utm_audit_log')) AS table_size
FROM utm_audit_log;

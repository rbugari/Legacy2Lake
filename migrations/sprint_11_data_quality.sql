-- ================================================================
-- Sprint 11: Data Quality Framework - Database Migration
-- ================================================================
-- Purpose: Create tables for quality rules, reports, metrics, and anomalies
-- Author: UTM Platform Team
-- Created: February 11, 2026
-- Dependencies: utm_tenants, utm_projects, utm_objects
-- ================================================================

-- ================================================================
-- Table 1: utm_quality_rules
-- Purpose: Store data quality rule definitions
-- ================================================================
CREATE TABLE IF NOT EXISTS utm_quality_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    project_id UUID NOT NULL,
    
    rule_id VARCHAR(255) NOT NULL,
    rule_type VARCHAR(50) NOT NULL CHECK (rule_type IN ('nullability', 'range', 'format', 'length', 'uniqueness', 'reference', 'enum', 'custom')),
    table_name VARCHAR(255) NOT NULL,
    column_name VARCHAR(255),
    
    condition JSONB NOT NULL DEFAULT '{}'::JSONB,
    severity VARCHAR(20) NOT NULL DEFAULT 'medium' CHECK (severity IN ('critical', 'high', 'medium', 'low', 'info')),
    description TEXT,
    enabled BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_by UUID,
    
    UNIQUE(tenant_id, project_id, rule_id)
);

-- Indexes for utm_quality_rules
CREATE INDEX idx_utm_quality_rules_tenant_project ON utm_quality_rules(tenant_id, project_id);
CREATE INDEX idx_utm_quality_rules_table ON utm_quality_rules(table_name);
CREATE INDEX idx_utm_quality_rules_type ON utm_quality_rules(rule_type);
CREATE INDEX idx_utm_quality_rules_enabled ON utm_quality_rules(enabled) WHERE enabled = TRUE;
CREATE INDEX idx_utm_quality_rules_condition ON utm_quality_rules USING GIN (condition);

-- RLS Policies for utm_quality_rules
ALTER TABLE utm_quality_rules ENABLE ROW LEVEL SECURITY;

CREATE POLICY utm_quality_rules_tenant_isolation
    ON utm_quality_rules
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

CREATE POLICY utm_quality_rules_service_role
    ON utm_quality_rules
    FOR ALL
    USING (current_setting('request.jwt.claims')::json->>'role' = 'service_role');

-- ================================================================
-- Table 2: utm_quality_reports
-- Purpose: Store quality evaluation reports
-- ================================================================
CREATE TABLE IF NOT EXISTS utm_quality_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    project_id UUID NOT NULL,
    
    table_name VARCHAR(255) NOT NULL,
    total_rows BIGINT DEFAULT 0,
    
    rules_evaluated INTEGER DEFAULT 0,
    rules_passed INTEGER DEFAULT 0,
    rules_failed INTEGER DEFAULT 0,
    
    quality_score NUMERIC(5,2) DEFAULT 0 CHECK (quality_score >= 0 AND quality_score <= 100),
    violations JSONB DEFAULT '[]'::JSONB,
    
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for utm_quality_reports
CREATE INDEX idx_utm_quality_reports_tenant_project ON utm_quality_reports(tenant_id, project_id);
CREATE INDEX idx_utm_quality_reports_table ON utm_quality_reports(table_name);
CREATE INDEX idx_utm_quality_reports_timestamp ON utm_quality_reports(timestamp DESC);
CREATE INDEX idx_utm_quality_reports_score ON utm_quality_reports(quality_score);
CREATE INDEX idx_utm_quality_reports_violations ON utm_quality_reports USING GIN (violations);

-- Partitioning by timestamp (monthly partitions for performance)
-- Note: Uncomment if using PostgreSQL 10+ with partitioning support
-- ALTER TABLE utm_quality_reports PARTITION BY RANGE (timestamp);

-- RLS Policies for utm_quality_reports
ALTER TABLE utm_quality_reports ENABLE ROW LEVEL SECURITY;

CREATE POLICY utm_quality_reports_tenant_isolation
    ON utm_quality_reports
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

CREATE POLICY utm_quality_reports_service_role
    ON utm_quality_reports
    FOR ALL
    USING (current_setting('request.jwt.claims')::json->>'role' = 'service_role');

-- ================================================================
-- Table 3: utm_quality_metrics
-- Purpose: Store detailed quality metrics by table/column
-- ================================================================
CREATE TABLE IF NOT EXISTS utm_quality_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    project_id UUID NOT NULL,
    
    table_name VARCHAR(255) NOT NULL,
    
    -- Aggregated scores
    overall_score NUMERIC(5,2) DEFAULT 0 CHECK (overall_score >= 0 AND overall_score <= 100),
    completeness_score NUMERIC(5,2) DEFAULT 0 CHECK (completeness_score >= 0 AND completeness_score <= 100),
    accuracy_score NUMERIC(5,2) DEFAULT 0 CHECK (accuracy_score >= 0 AND accuracy_score <= 100),
    consistency_score NUMERIC(5,2) DEFAULT 0 CHECK (consistency_score >= 0 AND consistency_score <= 100),
    timeliness_score NUMERIC(5,2) DEFAULT 0 CHECK (timeliness_score >= 0 AND timeliness_score <= 100),
    validity_score NUMERIC(5,2) DEFAULT 0 CHECK (validity_score >= 0 AND validity_score <= 100),
    uniqueness_score NUMERIC(5,2) DEFAULT 0 CHECK (uniqueness_score >= 0 AND uniqueness_score <= 100),
    
    -- Detailed metrics per column
    metrics JSONB DEFAULT '[]'::JSONB,
    
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for utm_quality_metrics
CREATE INDEX idx_utm_quality_metrics_tenant_project ON utm_quality_metrics(tenant_id, project_id);
CREATE INDEX idx_utm_quality_metrics_table ON utm_quality_metrics(table_name);
CREATE INDEX idx_utm_quality_metrics_timestamp ON utm_quality_metrics(timestamp DESC);
CREATE INDEX idx_utm_quality_metrics_overall_score ON utm_quality_metrics(overall_score);
CREATE INDEX idx_utm_quality_metrics_metrics ON utm_quality_metrics USING GIN (metrics);

-- RLS Policies for utm_quality_metrics
ALTER TABLE utm_quality_metrics ENABLE ROW LEVEL SECURITY;

CREATE POLICY utm_quality_metrics_tenant_isolation
    ON utm_quality_metrics
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

CREATE POLICY utm_quality_metrics_service_role
    ON utm_quality_metrics
    FOR ALL
    USING (current_setting('request.jwt.claims')::json->>'role' = 'service_role');

-- ================================================================
-- Table 4: utm_anomaly_reports
-- Purpose: Store anomaly detection reports
-- ================================================================
CREATE TABLE IF NOT EXISTS utm_anomaly_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    project_id UUID NOT NULL,
    
    table_name VARCHAR(255) NOT NULL,
    
    -- Counters by severity
    anomalies_detected INTEGER DEFAULT 0,
    critical_count INTEGER DEFAULT 0,
    high_count INTEGER DEFAULT 0,
    medium_count INTEGER DEFAULT 0,
    low_count INTEGER DEFAULT 0,
    
    -- Detailed anomalies
    anomalies JSONB DEFAULT '[]'::JSONB,
    
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for utm_anomaly_reports
CREATE INDEX idx_utm_anomaly_reports_tenant_project ON utm_anomaly_reports(tenant_id, project_id);
CREATE INDEX idx_utm_anomaly_reports_table ON utm_anomaly_reports(table_name);
CREATE INDEX idx_utm_anomaly_reports_timestamp ON utm_anomaly_reports(timestamp DESC);
CREATE INDEX idx_utm_anomaly_reports_critical ON utm_anomaly_reports(critical_count) WHERE critical_count > 0;
CREATE INDEX idx_utm_anomaly_reports_high ON utm_anomaly_reports(high_count) WHERE high_count > 0;
CREATE INDEX idx_utm_anomaly_reports_anomalies ON utm_anomaly_reports USING GIN (anomalies);

-- RLS Policies for utm_anomaly_reports
ALTER TABLE utm_anomaly_reports ENABLE ROW LEVEL SECURITY;

CREATE POLICY utm_anomaly_reports_tenant_isolation
    ON utm_anomaly_reports
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

CREATE POLICY utm_anomaly_reports_service_role
    ON utm_anomaly_reports
    FOR ALL
    USING (current_setting('request.jwt.claims')::json->>'role' = 'service_role');

-- ================================================================
-- View 1: utm_quality_rules_summary
-- Purpose: Quick overview of rules by table
-- ================================================================
CREATE OR REPLACE VIEW utm_quality_rules_summary AS
SELECT 
    tenant_id,
    project_id,
    table_name,
    COUNT(*) as total_rules,
    SUM(CASE WHEN enabled = TRUE THEN 1 ELSE 0 END) as enabled_rules,
    SUM(CASE WHEN enabled = FALSE THEN 1 ELSE 0 END) as disabled_rules,
    COUNT(DISTINCT rule_type) as rule_types_count,
    MAX(updated_at) as last_updated
FROM utm_quality_rules
GROUP BY tenant_id, project_id, table_name;

-- ================================================================
-- View 2: utm_quality_latest_reports
-- Purpose: Latest quality report per table
-- ================================================================
CREATE OR REPLACE VIEW utm_quality_latest_reports AS
SELECT DISTINCT ON (tenant_id, project_id, table_name)
    id,
    tenant_id,
    project_id,
    table_name,
    total_rows,
    rules_evaluated,
    rules_passed,
    rules_failed,
    quality_score,
    violations,
    timestamp
FROM utm_quality_reports
ORDER BY tenant_id, project_id, table_name, timestamp DESC;

-- ================================================================
-- View 3: utm_quality_trends
-- Purpose: Quality score trends over time (last 30 days)
-- ================================================================
CREATE OR REPLACE VIEW utm_quality_trends AS
SELECT 
    tenant_id,
    project_id,
    table_name,
    DATE(timestamp) as date,
    AVG(overall_score) as avg_overall_score,
    AVG(completeness_score) as avg_completeness_score,
    AVG(accuracy_score) as avg_accuracy_score,
    COUNT(*) as measurements
FROM utm_quality_metrics
WHERE timestamp >= NOW() - INTERVAL '30 days'
GROUP BY tenant_id, project_id, table_name, DATE(timestamp)
ORDER BY tenant_id, project_id, table_name, DATE(timestamp) DESC;

-- ================================================================
-- View 4: utm_anomaly_summary
-- Purpose: Anomaly summary by table
-- ================================================================
CREATE OR REPLACE VIEW utm_anomaly_summary AS
SELECT 
    tenant_id,
    project_id,
    table_name,
    SUM(anomalies_detected) as total_anomalies,
    SUM(critical_count) as total_critical,
    SUM(high_count) as total_high,
    SUM(medium_count) as total_medium,
    SUM(low_count) as total_low,
    MAX(timestamp) as latest_check
FROM utm_anomaly_reports
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY tenant_id, project_id, table_name;

-- ================================================================
-- Trigger: update_utm_quality_rules_timestamp
-- Purpose: Auto-update updated_at timestamp
-- ================================================================
CREATE OR REPLACE FUNCTION update_utm_quality_rules_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER utm_quality_rules_updated_at
    BEFORE UPDATE ON utm_quality_rules
    FOR EACH ROW
    EXECUTE FUNCTION update_utm_quality_rules_timestamp();

-- ================================================================
-- Comments for Documentation
-- ================================================================
COMMENT ON TABLE utm_quality_rules IS 'Data quality rule definitions (Sprint 11)';
COMMENT ON TABLE utm_quality_reports IS 'Quality evaluation reports (Sprint 11)';
COMMENT ON TABLE utm_quality_metrics IS 'Detailed quality metrics by table/column (Sprint 11)';
COMMENT ON TABLE utm_anomaly_reports IS 'Anomaly detection reports (Sprint 11)';

COMMENT ON COLUMN utm_quality_rules.rule_type IS 'Type: nullability, range, format, length, uniqueness, reference, enum, custom';
COMMENT ON COLUMN utm_quality_rules.condition IS 'JSONB configuration for rule (e.g., {min: 0, max: 100})';
COMMENT ON COLUMN utm_quality_reports.quality_score IS 'Overall quality score (0-100%)';
COMMENT ON COLUMN utm_quality_metrics.overall_score IS 'Weighted average of all metric dimensions';
COMMENT ON COLUMN utm_anomaly_reports.anomalies IS 'Array of detected anomalies with details';

-- ================================================================
-- Grants
-- ================================================================
GRANT SELECT, INSERT, UPDATE, DELETE ON utm_quality_rules TO authenticated;
GRANT SELECT, INSERT ON utm_quality_reports TO authenticated;
GRANT SELECT, INSERT ON utm_quality_metrics TO authenticated;
GRANT SELECT, INSERT ON utm_anomaly_reports TO authenticated;

GRANT SELECT ON utm_quality_rules_summary TO authenticated;
GRANT SELECT ON utm_quality_latest_reports TO authenticated;
GRANT SELECT ON utm_quality_trends TO authenticated;
GRANT SELECT ON utm_anomaly_summary TO authenticated;

-- ================================================================
-- Foreign Key Constraints (Add after tables exist)
-- ================================================================
-- Note: Uncomment these if utm_tenants and utm_projects tables exist with 'id' column
-- If they use different primary key column names, adjust accordingly

-- ALTER TABLE utm_quality_rules 
--     DROP CONSTRAINT IF EXISTS utm_quality_rules_tenant_id_fkey,
--     ADD CONSTRAINT utm_quality_rules_tenant_id_fkey 
--         FOREIGN KEY (tenant_id) REFERENCES utm_tenants(id) ON DELETE CASCADE;

-- ALTER TABLE utm_quality_rules 
--     DROP CONSTRAINT IF EXISTS utm_quality_rules_project_id_fkey,
--     ADD CONSTRAINT utm_quality_rules_project_id_fkey 
--         FOREIGN KEY (project_id) REFERENCES utm_projects(id) ON DELETE CASCADE;

-- Similar for other tables...

-- ================================================================
-- Sample Data (for testing)
-- ================================================================
-- Uncomment to insert sample rules:
/*
INSERT INTO utm_quality_rules (tenant_id, project_id, rule_id, rule_type, table_name, column_name, condition, severity, description) VALUES
    ('00000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001', 'customers_email_not_null', 'nullability', 'customers', 'email', '{"allow_null": false}'::JSONB, 'high', 'Email must not be null'),
    ('00000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001', 'orders_amount_range', 'range', 'orders', 'total_amount', '{"min": 0, "max": 1000000}'::JSONB, 'medium', 'Order amount must be between 0 and 1M'),
    ('00000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001', 'products_sku_format', 'format', 'products', 'sku', '{"pattern": "^[A-Z]{3}-\\d{6}$"}'::JSONB, 'medium', 'SKU format: ABC-123456');
*/

-- ================================================================
-- END OF MIGRATION
-- ================================================================

-- Create UTM_Supported_Techs table
CREATE TABLE IF NOT EXISTS public.utm_supported_techs (
    tech_id VARCHAR(50) PRIMARY KEY, -- e.g., 'SSIS', 'DATABRICKS'
    role VARCHAR(20) CHECK (role IN ('SOURCE', 'TARGET', 'BOTH')),
    label VARCHAR(100) NOT NULL,
    description TEXT,
    logo_url TEXT, -- Optional: for UI display
    is_active BOOLEAN DEFAULT TRUE,
    config_schema JSONB DEFAULT '{}'::JSONB, -- For UI form generation
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE public.utm_supported_techs ENABLE ROW LEVEL SECURITY;

-- Grant permissions (Service Role full, Anon read-only)
GRANT ALL ON public.utm_supported_techs TO service_role;
GRANT SELECT ON public.utm_supported_techs TO anon;
GRANT SELECT ON public.utm_supported_techs TO authenticated;

-- Policies
CREATE POLICY "Enable all for service role" ON public.utm_supported_techs TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Enable read for anon" ON public.utm_supported_techs FOR SELECT TO anon USING (true);
CREATE POLICY "Enable read for authenticated" ON public.utm_supported_techs FOR SELECT TO authenticated USING (true);

-- Seed Data
INSERT INTO public.utm_supported_techs (tech_id, role, label, description, is_active)
VALUES 
(
    'SSIS', 
    'SOURCE', 
    'Microsoft SSIS', 
    'Legacy SQL Server Integration Services packages (.dtsx).', 
    TRUE
),
(
    'DATABRICKS', 
    'TARGET', 
    'Databricks (PySpark)', 
    'Modern Lakehouse architecture using PySpark on Databricks.', 
    TRUE
),
(
    'SNOWFLAKE', 
    'TARGET', 
    'Snowflake', 
    'Cloud Data Warehouse. (Coming Soon)', 
    FALSE
)
ON CONFLICT (tech_id) DO UPDATE 
SET label = EXCLUDED.label, 
    description = EXCLUDED.description,
    is_active = EXCLUDED.is_active;

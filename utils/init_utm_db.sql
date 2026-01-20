-- UTM Metadata Store Schema (v1.0)
-- Based on 02_Modelo_de_Datos_UTM.md

-- 1. UTM_Project
CREATE TABLE IF NOT EXISTS public.utm_projects (
    project_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    settings JSONB DEFAULT '{}'::JSONB
);

-- 2. UTM_Object (Ingestion Layer)
CREATE TABLE IF NOT EXISTS public.utm_objects (
    object_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES public.utm_projects(project_id) ON DELETE CASCADE,
    source_name VARCHAR(255) NOT NULL,
    source_tech VARCHAR(50) CHECK (source_tech IN ('SSIS', 'INFORMATICA', 'DATASTAGE', 'SQL_PROC')),
    raw_content TEXT,
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. UTM_Logical_Step (Kernel/IR Layer)
CREATE TABLE IF NOT EXISTS public.utm_logical_steps (
    step_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    object_id UUID REFERENCES public.utm_objects(object_id) ON DELETE CASCADE,
    step_order INT NOT NULL,
    step_type VARCHAR(50) CHECK (step_type IN ('READ', 'TRANSFORM', 'JOIN', 'FILTER', 'AGGREGATE', 'WRITE')),
    ir_payload JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'DRAFT' CHECK (status IN ('DRAFT', 'VALIDATED', 'OVERRIDDEN', 'ERROR')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. UTM_User_Override (Human-in-the-Loop)
CREATE TABLE IF NOT EXISTS public.utm_user_overrides (
    override_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    step_id UUID REFERENCES public.utm_logical_steps(step_id) ON DELETE CASCADE,
    field_path VARCHAR(255) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    comment TEXT,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. UTM_Function_Registry (Canonical Mapping)
CREATE TABLE IF NOT EXISTS public.utm_function_registry (
    func_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    canonical_name VARCHAR(100) NOT NULL UNIQUE,
    module VARCHAR(50) NOT NULL,
    implementation_templates JSONB NOT NULL, -- Key: Tech (e.g., 'databricks'), Value: Template
    requires_manual_mapping BOOLEAN DEFAULT FALSE,
    description TEXT
);

-- Migration: Add display_name and description to utm_agent_catalog
-- Backlog v3.8 - Task #3: Agent Management UX
-- Date: 2026-02-07

-- Step 1: Add new columns
ALTER TABLE utm_agent_catalog
  ADD COLUMN display_name VARCHAR(100),
  ADD COLUMN description TEXT;

-- Step 2: Update existing agents with professional names and descriptions
-- Based on Backlog v3.8 specifications

UPDATE utm_agent_catalog 
SET 
    display_name = 'Discovery Agent',
    description = 'Analyzes legacy code manifests and builds comprehensive knowledge base from source files. Extracts metadata, identifies dependencies, and catalogs all assets for downstream processing.'
WHERE agent_id = 'agent-a';

UPDATE utm_agent_catalog 
SET 
    display_name = 'Code Generator',
    description = 'Transpiles legacy logic into modern target patterns (PySpark, SQL, dbt). Produces production-ready code with proper error handling, logging, and best practices.'
WHERE agent_id = 'agent-c';

UPDATE utm_agent_catalog 
SET 
    display_name = 'Compliance Auditor',
    description = 'Reviews generated code for optimization opportunities and compliance violations. Validates adherence to platform standards and security policies.'
WHERE agent_id = 'agent-f';

UPDATE utm_agent_catalog 
SET 
    display_name = 'Governance Agent',
    description = 'Enforces security policies and naming conventions. Generates documentation, runbooks, and ensures alignment with enterprise governance rules.'
WHERE agent_id = 'agent-g';

UPDATE utm_agent_catalog 
SET 
    display_name = 'Operations Auditor',
    description = 'Validates operational readiness of generated artifacts. Generates DevOps manifests (Airflow DAGs, Databricks Workflows) and validates orchestration patterns.'
WHERE agent_id = 'agent-o';

UPDATE utm_agent_catalog 
SET 
    display_name = 'Profiling Agent',
    description = 'Analyzes codebase patterns, identifies primary keys, and detects data dependencies. Performs deep forensic analysis of transformation logic and business rules.'
WHERE agent_id = 'agent-p';

UPDATE utm_agent_catalog 
SET 
    display_name = 'Refactoring Agent',
    description = 'Optimizes Spark code for performance and scalability. Applies security best practices, PII masking, and modern data engineering patterns.'
WHERE agent_id = 'agent-r';

UPDATE utm_agent_catalog 
SET 
    display_name = 'Technology Scout',
    description = 'Performs forensic analysis of file inventories to detect source platform technology. Identifies SQL dialects, ETL tools (Informatica, DataStage, SSIS), and framework patterns.'
WHERE agent_id = 'agent-s';

-- Step 3: Verify the migration
SELECT 
    agent_id,
    name,
    display_name,
    LEFT(description, 80) || '...' as description_preview,
    is_active
FROM utm_agent_catalog
ORDER BY agent_id;

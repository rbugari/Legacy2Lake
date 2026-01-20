-- Seed Data for UTM_Function_Registry
-- Based on 05_Registro_de_Funciones.md

INSERT INTO public.utm_function_registry (canonical_name, module, implementation_templates, description)
VALUES 
(
    'COALESCE', 
    'NULL_HANDLING', 
    '{"databricks": "F.coalesce({{args}})", "snowflake": "NVL({{args}})", "sqlserver": "ISNULL({{args}})"}'::JSONB,
    'Returns the first non-null value in a list.'
),
(
    'CURRENT_TIMESTAMP', 
    'DATE_TIME', 
    '{"databricks": "F.current_timestamp()", "snowflake": "CURRENT_TIMESTAMP()", "sqlserver": "GETDATE()"}'::JSONB,
    'Returns the current date and time.'
),
(
    'DATE_ADD', 
    'DATE_TIME', 
    '{"databricks": "F.date_add({{date}}, {{days}})", "snowflake": "DATEADD(day, {{days}}, {{date}})", "sqlserver": "DATEADD(day, {{days}}, {{date}})"}'::JSONB,
    'Adds a specified number of days to a date.'
),
(
    'SUBSTRING', 
    'STRING', 
    '{"databricks": "F.substring({{str}}, {{pos}}, {{len}})", "snowflake": "SUBSTR({{str}}, {{pos}}, {{len}})", "sqlserver": "SUBSTRING({{str}}, {{pos}}, {{len}})"}'::JSONB,
    'Extracts a substring from a string.'
),
(
    'TO_UPPER', 
    'STRING', 
    '{"databricks": "F.upper({{str}})", "snowflake": "UPPER({{str}})", "sqlserver": "UPPER({{str}})"}'::JSONB,
    'Converts a string to uppercase.'
),
(
    'IF_THEN_ELSE', 
    'LOGIC', 
    '{"databricks": "F.when({{condition}}, {{then_val}}).otherwise({{else_val}})", "snowflake": "CASE WHEN {{condition}} THEN {{then_val}} ELSE {{else_val}} END", "sqlserver": "CASE WHEN {{condition}} THEN {{then_val}} ELSE {{else_val}} END"}'::JSONB,
    'Conditional logic.'
)
ON CONFLICT (canonical_name) DO UPDATE 
SET implementation_templates = EXCLUDED.implementation_templates;

-- Migration: 019 Remove Public Models Concept
-- Description: Elimina is_public, todos los modelos son del tenant que paga

-- 1. Eliminar modelos públicos huérfanos (sin tenant)
DELETE FROM utm_model_catalog WHERE tenant_id IS NULL;

-- 2. Eliminar columna is_public
ALTER TABLE utm_model_catalog
DROP COLUMN IF EXISTS is_public;

-- 3. Hacer tenant_id obligatorio
ALTER TABLE utm_model_catalog
ALTER COLUMN tenant_id SET NOT NULL;

-- 4. Actualizar comentarios
COMMENT ON TABLE utm_model_catalog IS 'Catálogo de modelos LLM por tenant - cada tenant tiene sus propios modelos porque paga por ellos';
COMMENT ON COLUMN utm_model_catalog.tenant_id IS 'Tenant propietario del modelo - obligatorio porque el tenant paga';

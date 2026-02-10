#!/usr/bin/env python3
"""
Mostrar SQL final para ejecutar en Supabase SQL Editor
La columna is_public debe eliminarse completamente
"""

print("="*70)
print("MIGRACIÓN 019 - EJECUTAR EN SUPABASE SQL EDITOR")
print("="*70)
print("\nLa columna 'is_public' debe eliminarse porque:")
print("- ❌ No tiene sentido tener modelos 'públicos'")
print("- ✅ Cada tenant PAGA por su proveedor y sus modelos")
print("- ✅ Los modelos son EXCLUSIVOS de cada tenant")
print("\n" + "="*70)
print("SQL A EJECUTAR:")
print("="*70)
print("""
-- Eliminar columna is_public (ya no se usa)
ALTER TABLE utm_model_catalog
DROP COLUMN IF EXISTS is_public;

-- TODAS las filas ya tienen tenant_id válido, ahora hacerlo obligatorio
ALTER TABLE utm_model_catalog
ALTER COLUMN tenant_id SET NOT NULL;

-- Índice mejorado (si no existe)
CREATE INDEX IF NOT EXISTS idx_model_tenant_provider 
ON utm_model_catalog(tenant_id, provider);

-- Comentarios actualizados
COMMENT ON TABLE utm_model_catalog IS 'Catálogo de modelos LLM por tenant - cada tenant paga por sus modelos';
COMMENT ON COLUMN utm_model_catalog.tenant_id IS 'Tenant propietario (obligatorio - el tenant paga)';
COMMENT ON COLUMN utm_model_catalog.provider IS 'Proveedor LLM (openai, groq, azure, etc.)';
""")
print("="*70)
print("\n✅ Después de ejecutar este SQL:")
print("   - is_public: ELIMINADA")
print("   - tenant_id: NOT NULL (obligatorio)")
print("   - Todos los modelos pertenecen a un tenant específico")
print("\n" + "="*70)

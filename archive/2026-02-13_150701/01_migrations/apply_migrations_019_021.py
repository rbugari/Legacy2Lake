#!/usr/bin/env python3
"""
Aplicar migraciones 019-021: Modelo de roles correcto
"""
import asyncio
from supabase import create_client
import ssl
import httpcore

# Bypass SSL certificate verification
_original_start_tls = httpcore._backends.sync.SyncStream.start_tls

def _patched_start_tls(self, *args, **kwargs):
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    kwargs['ssl_context'] = ssl_context
    return _original_start_tls(self, *args, **kwargs)

httpcore._backends.sync.SyncStream.start_tls = _patched_start_tls

# Configuración de DEV
DEV_URL = "https://qdsdfityyxmalyipqbfm.supabase.co"
DEV_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFkc2RmaXR5eXhtYWx5aXBxYmZtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODg2NTczOSwiZXhwIjoyMDg0NDQxNzM5fQ.f4Ge4MPpeDoFLgLSD9e79V2N-ND-aU9YqwNp2VrOgC0"


async def apply_migrations():
    client = create_client(DEV_URL, DEV_KEY)
    
    print("="*70)
    print("APLICANDO MIGRACIONES 019-021")
    print("="*70)
    
    migrations = [
        {
            "number": "019",
            "file": "supabase_migrations/019_v3.9_remove_public_models.sql",
            "description": "Eliminar columna is_public de utm_model_catalog"
        },
        {
            "number": "020",
            "file": "supabase_migrations/020_v3.9_project_level_invitations.sql",
            "description": "Agregar project_id a utm_user_invitations"
        },
        {
            "number": "021",
            "file": "supabase_migrations/021_v3.9_project_members_table.sql",
            "description": "Crear tabla utm_project_members"
        }
    ]
    
    for migration in migrations:
        print(f"\n{'='*70}")
        print(f"MIGRACIÓN {migration['number']}: {migration['description']}")
        print('='*70)
        
        try:
            with open(migration['file'], 'r', encoding='utf-8') as f:
                sql = f.read()
            
            print(f"📄 Archivo: {migration['file']}")
            print(f"📝 SQL:\n{sql[:200]}...")
            
            print("\n⚠️  Esta migración debe ejecutarse manualmente en Supabase SQL Editor")
            print("   Razón: Alteraciones de esquema (ALTER TABLE, CREATE TABLE)")
            print(f"\n   👉 Copiar contenido de: {migration['file']}")
            print("   👉 Pegar en: https://supabase.com/dashboard → SQL Editor")
            print("   👉 Ejecutar")
            
        except Exception as e:
            print(f"❌ Error leyendo archivo: {e}")
    
    print(f"\n{'='*70}")
    print("VERIFICACIÓN POST-MIGRACIÓN")
    print('='*70)
    
    print("\nDespués de ejecutar las 3 migraciones, verificar:")
    print("1. ✅ utm_model_catalog NO tiene columna is_public")
    print("2. ✅ utm_model_catalog.tenant_id es NOT NULL")
    print("3. ✅ utm_user_invitations tiene columna project_id")
    print("4. ✅ utm_project_members existe")
    print("5. ✅ Todos los modelos tienen tenant_id válido")
    
    # Verificar estado actual (pre-migración)
    print(f"\n📊 Estado ACTUAL (antes de migraciones):")
    
    try:
        res = client.table("utm_model_catalog").select("*", count="exact").execute()
        print(f"   - utm_model_catalog: {res.count} modelos")
        
        res_orphan = client.table("utm_model_catalog").select("*", count="exact").is_("tenant_id", "null").execute()
        print(f"   - Modelos sin tenant: {res_orphan.count}")
        
        # Ver si is_public existe
        if res.data and "is_public" in res.data[0]:
            res_public = client.table("utm_model_catalog").select("*", count="exact").eq("is_public", True).execute()
            print(f"   - Modelos con is_public=True: {res_public.count}")
        else:
            print(f"   - is_public: ✅ Ya eliminada")
        
    except Exception as e:
        print(f"   ⚠️  Error verificando: {e}")


if __name__ == "__main__":
    asyncio.run(apply_migrations())

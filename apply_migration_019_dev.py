#!/usr/bin/env python3
"""
Aplicar migración 019: Eliminar concepto de modelos públicos
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


async def apply_migration_019():
    client = create_client(DEV_URL, DEV_KEY)
    
    print("="*70)
    print("MIGRACIÓN 019: ELIMINAR MODELOS PÚBLICOS")
    print("="*70)
    
    # 1. Ver estado actual
    print("\n📊 Estado antes de migración:")
    res_all = client.table("utm_model_catalog").select("*", count="exact").execute()
    print(f"   Total modelos: {res_all.count}")
    
    res_public = client.table("utm_model_catalog").select("*", count="exact").eq("is_public", True).execute()
    print(f"   Modelos públicos: {res_public.count}")
    
    res_orphan = client.table("utm_model_catalog").select("*", count="exact").is_("tenant_id", "null").execute()
    print(f"   Modelos huérfanos (sin tenant): {res_orphan.count}")
    
    # 2. Leer migración
    with open("supabase_migrations/019_v3.9_remove_public_models.sql", "r", encoding="utf-8") as f:
        sql = f.read()
    
    print("\n🔄 Aplicando migración...")
    print(f"Script: 019_v3.9_remove_public_models.sql")
    
    try:
        # Ejecutar SQL via RPC
        result = client.rpc("exec_sql", {"sql": sql}).execute()
        print("   ✅ Migración aplicada")
    except Exception as e:
        # Si no existe la función, ejecutar directamente
        print(f"   ⚠️  Ejecutando con postgrest-py (sin RPC): {e}")
        
        # Ejecutar manualmente cada comando
        # 1. Eliminar modelos públicos huérfanos
        res_delete = client.table("utm_model_catalog").delete().is_("tenant_id", "null").execute()
        print(f"   ✅ Eliminados {len(res_delete.data)} modelos huérfanos")
        
        # Las alteraciones de columnas no se pueden hacer via postgrest
        print("   ⚠️  Las alteraciones de esquema deben ejecutarse via SQL directo")
        print("\n📝 SQL pendiente de ejecutar en Supabase SQL Editor:")
        print(sql)
    
    # 3. Verificar estado final
    print("\n📊 Estado después de migración:")
    try:
        res_final = client.table("utm_model_catalog").select("*", count="exact").execute()
        print(f"   Total modelos: {res_final.count}")
        
        # Agrupar por tenant
        by_tenant = {}
        for model in res_final.data:
            tenant_id = model.get("tenant_id")
            if tenant_id:
                if tenant_id not in by_tenant:
                    by_tenant[tenant_id] = []
                by_tenant[tenant_id].append(model.get("model_id"))
        
        print(f"\n📦 Modelos por tenant:")
        for tenant_id, models in by_tenant.items():
            # Obtener nombre del client
            res_t = client.table("utm_tenants").select("client_id").eq("tenant_id", tenant_id).execute()
            client_name = res_t.data[0]["client_id"] if res_t.data else "UNKNOWN"
            print(f"   {client_name}: {len(models)} modelos")
    except Exception as e:
        print(f"   ℹ️  Verificación manual necesaria: {e}")


if __name__ == "__main__":
    asyncio.run(apply_migration_019())

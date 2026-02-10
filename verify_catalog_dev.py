#!/usr/bin/env python3
"""
Verificar estado del catálogo en DEV
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


async def verify_catalog():
    client = create_client(DEV_URL, DEV_KEY)
    
    print("="*70)
    print("VERIFICACIÓN CATÁLOGO DE MODELOS - DEV")
    print("="*70)
    
    # Ver todos los modelos
    res_all = client.table("utm_model_catalog").select("*").execute()
    
    print(f"\n📊 Total modelos: {len(res_all.data)}\n")
    
    # Agrupar por tenant_id
    by_tenant = {"public": [], "private": {}}
    
    for model in res_all.data:
        tenant_id = model.get("tenant_id")
        is_public = model.get("is_public")
        
        if is_public or tenant_id is None:
            by_tenant["public"].append(model)
        else:
            if tenant_id not in by_tenant["private"]:
                by_tenant["private"][tenant_id] = []
            by_tenant["private"][tenant_id].append(model)
    
    # Mostrar públicos
    print("🌐 MODELOS PÚBLICOS:")
    print(f"   Total: {len(by_tenant['public'])}")
    for m in by_tenant["public"][:10]:  # Primeros 10
        print(f"   - {m.get('model_id')} ({m.get('provider')})")
    if len(by_tenant["public"]) > 10:
        print(f"   ... y {len(by_tenant['public']) - 10} más")
    
    # Mostrar privados por tenant
    print("\n🔒 MODELOS PRIVADOS POR TENANT:")
    for tenant_id, models in by_tenant["private"].items():
        # Obtener nombre del tenant
        res_tenant = client.table("utm_tenants").select("client_id").eq("tenant_id", tenant_id).execute()
        client_id = res_tenant.data[0]["client_id"] if res_tenant.data else "UNKNOWN"
        
        print(f"\n   {client_id} ({tenant_id}):")
        print(f"   Total: {len(models)}")
        for m in models:
            print(f"   - {m.get('model_id')} ({m.get('provider')})")


if __name__ == "__main__":
    asyncio.run(verify_catalog())

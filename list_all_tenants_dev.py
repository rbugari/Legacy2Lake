#!/usr/bin/env python3
"""
Listar todos los tenants en DEV con sus configuraciones
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


async def list_tenants():
    client = create_client(DEV_URL, DEV_KEY)
    
    print("="*70)
    print("TODOS LOS TENANTS EN DEV")
    print("="*70)
    
    # Listar tenants
    res_tenants = client.table("utm_tenants").select("*").execute()
    
    print(f"\n📊 Total tenants: {len(res_tenants.data)}\n")
    
    for tenant in res_tenants.data:
        tenant_id = tenant.get("tenant_id")
        client_id = tenant.get("client_id")
        
        print(f"{'='*70}")
        print(f"Client ID: {client_id}")
        print(f"Tenant ID: {tenant_id}")
        print(f"Activo: {tenant.get('is_active')}")
        
        # Contar usuarios
        res_users = client.table("utm_users").select("username, role", count="exact").eq("tenant_id", tenant_id).execute()
        print(f"👥 Usuarios: {res_users.count}")
        for u in res_users.data:
            print(f"   - {u.get('username')} ({u.get('role')})")
        
        # Contar proveedores
        res_prov = client.table("utm_provider_vault").select("provider_name, is_active", count="exact").eq("tenant_id", tenant_id).execute()
        print(f"🔌 Proveedores: {res_prov.count}")
        for p in res_prov.data:
            status = "✓" if p.get("is_active") else "✗"
            print(f"   {status} {p.get('provider_name')}")
        
        # Contar modelos privados
        res_models = client.table("utm_model_catalog").select("model_id", count="exact").eq("tenant_id", tenant_id).eq("is_public", False).execute()
        print(f"📦 Modelos privados: {res_models.count}")
        for m in res_models.data[:5]:
            print(f"   - {m.get('model_id')}")
        if res_models.count > 5:
            print(f"   ... y {res_models.count - 5} más")
        
        # Contar proyectos
        res_proj = client.table("utm_projects").select("project_id", count="exact").eq("tenant_id", tenant_id).execute()
        print(f"📊 Proyectos: {res_proj.count}")


if __name__ == "__main__":
    asyncio.run(list_tenants())

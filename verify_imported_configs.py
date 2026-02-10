#!/usr/bin/env python3
"""
Verifica las configuraciones importadas en DEV
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


async def verify_configs():
    client = create_client(DEV_URL, DEV_KEY)
    
    print("="*70)
    print("VERIFICACIÓN DE CONFIGURACIONES DEV")
    print("="*70)
    
    TARGET_CLIENTS = ["DEMO1", "DEMO2", "CUSTOMER3"]
    
    for client_id in TARGET_CLIENTS:
        print(f"\n{'='*70}")
        print(f"CLIENT: {client_id}")
        print('='*70)
        
        # Obtener tenant_id
        res_tenant = client.table("utm_tenants").select("tenant_id, is_active").eq("client_id", client_id).execute()
        
        if not res_tenant.data:
            print(f"❌ No se encontró tenant {client_id}")
            continue
        
        tenant_id = res_tenant.data[0]["tenant_id"]
        active = "✓" if res_tenant.data[0].get("is_active") else "✗"
        
        print(f"Tenant ID: {tenant_id}")
        print(f"Activo: {active}")
        
        # Provider vault
        print(f"\n📦 PROVEEDORES:")
        res_prov = client.table("utm_provider_vault").select("*").eq("tenant_id", tenant_id).execute()
        
        if res_prov.data:
            for prov in res_prov.data:
                status = "✓ ACTIVO" if prov.get("is_active") else "✗ inactivo"
                print(f"   {status} {prov.get('provider_name')}")
                print(f"      Base URL: {prov.get('base_url')}")
                print(f"      API Key: {prov.get('api_key')[:30]}...")
        else:
            print(f"   (sin proveedores)")
        
        # Usuarios
        print(f"\n👥 USUARIOS:")
        res_users = client.table("utm_users").select("username, email, role, is_active").eq("tenant_id", tenant_id).execute()
        
        if res_users.data:
            for user in res_users.data:
                status = "✓" if user.get("is_active") else "✗"
                print(f"   {status} {user.get('username')} ({user.get('role')})")
                if user.get('email'):
                    print(f"      Email: {user.get('email')}")
        else:
            print(f"   (sin usuarios)")
        
        # Proyectos
        res_proj = client.table("utm_projects").select("project_id", count="exact").eq("tenant_id", tenant_id).execute()
        print(f"\n📊 PROYECTOS: {res_proj.count}")
    
    print("\n" + "="*70)
    print("VERIFICACIÓN COMPLETADA")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(verify_configs())

#!/usr/bin/env python3
"""
Identificar qué tenants corresponden a DEMO1, DEMO2, DEMO3
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

# Configuración de producción
PROD_URL = "https://wdmlnvppkhjjeuiutnjl.supabase.co"
PROD_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndkbWxudnBwa2hqamV1aXV0bmpsIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDA4MjM2NiwiZXhwIjoyMDg1NjU4MzY2fQ.ptqq5JugnDa2FcuTeSl28PfbfKfW5Qz4tDuMggH9eeg"


async def map_tenants_to_demos():
    client = create_client(PROD_URL, PROD_KEY)
    
    print("="*70)
    print("MAPEANDO TENANTS A USUARIOS DEMO")
    print("="*70)
    
    # Ver usuarios
    try:
        res = client.table("utm_users").select("*").execute()
        print(f"\n✅ utm_users: {len(res.data)} usuarios\n")
        
        tenant_map = {}
        
        for user in res.data:
            username = user.get('username', 'N/A')
            email = user.get('email', 'N/A')
            tenant_id = user.get('tenant_id')
            role = user.get('role', 'N/A')
            
            print(f"Username: {username}")
            print(f"Email: {email}")
            print(f"Tenant ID: {tenant_id}")
            print(f"Role: {role}")
            
            # Mapear si es usuario DEMO
            if username.upper().startswith('DEMO'):
                tenant_map[username.upper()] = tenant_id
            
            print("-" * 70)
        
        # Ver qué proveedores tiene cada tenant DEMO
        print("\n" + "="*70)
        print("CONFIGURACIONES POR TENANT DEMO")
        print("="*70)
        
        for demo_user, tenant_id in tenant_map.items():
            print(f"\n{demo_user} (Tenant: {tenant_id})")
            
            # Buscar provider_vault
            res_prov = client.table("utm_provider_vault").select("*").eq("tenant_id", tenant_id).execute()
            
            if res_prov.data:
                for prov in res_prov.data:
                    status = "✓" if prov.get('is_active') else "✗"
                    models = prov.get('model_ids_json', '[]')
                    print(f"  {status} {prov.get('provider_name')}: {models}")
            else:
                print(f"  (sin proveedores configurados)")
            
            # Contar proyectos
            res_proj = client.table("utm_projects").select("project_id", count="exact").eq("tenant_id", tenant_id).execute()
            print(f"  📊 Proyectos: {res_proj.count}")
            
            print("-" * 70)
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(map_tenants_to_demos())

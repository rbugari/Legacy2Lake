#!/usr/bin/env python3
"""
Explorar relación entre clients y tenants en producción
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


async def explore_structure():
    client = create_client(PROD_URL, PROD_KEY)
    
    print("="*70)
    print("EXPLORANDO ESTRUCTURA DE PROJECTS")
    print("="*70)
    
    # Ver proyectos para identificar patrón de client_id
    try:
        res = client.table("utm_projects").select("*").limit(3).execute()
        print(f"\n✅ utm_projects (muestra): {len(res.data)} registros\n")
        
        for proj in res.data:
            print(f"Project ID: {proj.get('project_id')}")
            print(f"Name: {proj.get('name')}")
            print(f"Client ID: {proj.get('client_id')}")
            print(f"Tenant ID: {proj.get('tenant_id')}")
            print(f"Created: {proj.get('created_at')}")
            print("-" * 70)
            
    except Exception as e:
        print(f"❌ Error leyendo utm_projects: {e}")
    
    # Ver provider vault
    print("\n" + "="*70)
    print("EXPLORANDO PROVIDER VAULT")
    print("="*70)
    
    try:
        res = client.table("utm_provider_vault").select("*").execute()
        print(f"\n✅ utm_provider_vault: {len(res.data)} registros\n")
        
        for prov in res.data:
            print(f"ID: {prov.get('id')}")
            print(f"Client ID: {prov.get('client_id')}")
            print(f"Tenant ID: {prov.get('tenant_id')}")
            print(f"Provider: {prov.get('provider_name')}")
            print(f"Active: {prov.get('is_active')}")
            print("-" * 70)
            
    except Exception as e:
        print(f"❌ Error leyendo utm_provider_vault: {e}")
    
    # Ver utm_vault
    print("\n" + "="*70)
    print("EXPLORANDO VAULT")
    print("="*70)
    
    try:
        res = client.table("utm_vault").select("*").execute()
        print(f"\n✅ utm_vault: {len(res.data)} registros\n")
        
        for vault in res.data:
            print(f"Key Name: {vault.get('key_name')}")
            print(f"Client ID: {vault.get('client_id')}")
            print(f"Tenant ID: {vault.get('tenant_id')}")
            print(f"Encrypted: {vault.get('encrypted_value')[:50] if vault.get('encrypted_value') else 'None'}...")
            print("-" * 70)
            
    except Exception as e:
        print(f"❌ Error leyendo utm_vault: {e}")


if __name__ == "__main__":
    asyncio.run(explore_structure())

#!/usr/bin/env python3
"""
Explorar estructura de tenants en producción
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


async def explore_tenants():
    client = create_client(PROD_URL, PROD_KEY)
    
    print("="*70)
    print("EXPLORANDO TENANTS EN PRODUCCIÓN")
    print("="*70)
    
    # Verificar si existe utm_tenants
    try:
        res = client.table("utm_tenants").select("*").execute()
        print(f"\n✅ utm_tenants: {len(res.data)} registros\n")
        
        for tenant in res.data:
            print(f"Tenant ID: {tenant.get('tenant_id')}")
            print(f"Client ID: {tenant.get('client_id')}")
            print(f"Plan: {tenant.get('plan_type')}")
            print(f"Activo: {tenant.get('is_active')}")
            print("-" * 70)
            
    except Exception as e:
        print(f"❌ Error leyendo utm_tenants: {e}")
    
    # Si no existe utm_tenants, buscar en utm_clients
    print("\n" + "="*70)
    print("EXPLORANDO CLIENTS (LEGACY)")
    print("="*70)
    
    try:
        res = client.table("utm_clients").select("*").execute()
        print(f"\n✅ utm_clients: {len(res.data)} registros\n")
        
        for client_rec in res.data:
            print(f"ID: {client_rec.get('id')}")
            print(f"Name: {client_rec.get('name')}")
            print("-" * 70)
            
    except Exception as e:
        print(f"❌ Error leyendo utm_clients: {e}")


if __name__ == "__main__":
    asyncio.run(explore_tenants())

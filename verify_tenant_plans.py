#!/usr/bin/env python3
"""
Verificar y actualizar tier de tenants en DEV
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


async def check_tenant_tiers():
    client = create_client(DEV_URL, DEV_KEY)
    
    print("="*70)
    print("VERIFICACIÓN DE PLANES/TIER DE TENANTS")
    print("="*70)
    
    # Ver tenants actuales
    res = client.table("utm_tenants").select("*").execute()
    
    print(f"\n📊 Tenants: {len(res.data)}\n")
    
    for tenant in res.data:
        client_id = tenant.get("client_id")
        tier = tenant.get("tier")
        org_name = tenant.get("org_name")
        is_active = tenant.get("is_active")
        
        print(f"{'='*70}")
        print(f"Client: {client_id}")
        print(f"Organización: {org_name}")
        print(f"Plan/Tier: {tier or 'NULL ❌'}")
        print(f"Activo: {'✓' if is_active else '✗'}")
        
        # Si no tiene tier, asignar STANDARD
        if not tier:
            print(f"⚠️  Asignando STANDARD por defecto...")
            try:
                client.table("utm_tenants").update({"tier": "STANDARD"}).eq("client_id", client_id).execute()
                print(f"✅ Actualizado a STANDARD")
            except Exception as e:
                print(f"❌ Error: {e}")
    
    print(f"\n{'='*70}")
    print("EXPLICACIÓN DE PLANES")
    print('='*70)
    print("""
📋 PLANES DISPONIBLES:

- STANDARD: Plan básico (mayoría de clientes)
- PREMIUM: Plan con features adicionales
- ENTERPRISE: Plan corporativo con soporte dedicado

⚠️ IMPORTANTE - RESPONSABILIDAD DE GASTO:
- El MANAGER es responsable del consumo del tenant
- Cada tenant PAGA por su uso (API calls, tokens consumidos)
- Si el MANAGER invita usuarios que gastan mucho → responsabilidad del MANAGER
- La plataforma NO es responsable del gasto individual de cada tenant
- El ADMIN asigna el plan, pero el control de gasto es del MANAGER
""")


if __name__ == "__main__":
    asyncio.run(check_tenant_tiers())

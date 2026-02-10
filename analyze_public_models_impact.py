#!/usr/bin/env python3
"""
Análisis de impacto: Eliminar modelos públicos
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


async def analyze_impact():
    client = create_client(DEV_URL, DEV_KEY)
    
    print("="*70)
    print("ANÁLISIS DE IMPACTO - ELIMINAR MODELOS PÚBLICOS")
    print("="*70)
    
    # Obtener modelos sin tenant (huérfanos)
    res_orphan = client.table("utm_model_catalog").select("*").is_("tenant_id", "null").execute()
    
    print(f"\n❌ MODELOS A ELIMINAR (sin tenant_id): {len(res_orphan.data)}")
    print("-" * 70)
    
    by_provider = {}
    for model in res_orphan.data:
        provider = model.get("provider", "unknown")
        if provider not in by_provider:
            by_provider[provider] = []
        by_provider[provider].append(model.get("model_id"))
    
    for provider, models in by_provider.items():
        print(f"\n{provider} ({len(models)} modelos):")
        for m in models:
            print(f"   - {m}")
    
    # Obtener modelos con tenant
    res_with_tenant = client.table("utm_model_catalog").select("*").not_.is_("tenant_id", "null").execute()
    
    print(f"\n✅ MODELOS A CONSERVAR (con tenant_id): {len(res_with_tenant.data)}")
    print("-" * 70)
    
    by_tenant = {}
    for model in res_with_tenant.data:
        tenant_id = model.get("tenant_id")
        if tenant_id not in by_tenant:
            by_tenant[tenant_id] = []
        by_tenant[tenant_id].append(model.get("model_id"))
    
    for tenant_id, models in by_tenant.items():
        # Obtener nombre del tenant
        res_t = client.table("utm_tenants").select("client_id").eq("tenant_id", tenant_id).execute()
        client_name = res_t.data[0]["client_id"] if res_t.data else "UNKNOWN"
        
        print(f"\n{client_name}:")
        for m in models:
            print(f"   - {m}")
    
    print("\n" + "="*70)
    print("RESUMEN")
    print("="*70)
    print(f"Modelos a ELIMINAR: {len(res_orphan.data)}")
    print(f"Modelos a CONSERVAR: {len(res_with_tenant.data)}")
    print(f"\nEsto es correcto: cada tenant solo debe ver SUS modelos")
    print("Los modelos sin tenant (públicos) no tienen sentido si cada tenant paga.")


if __name__ == "__main__":
    asyncio.run(analyze_impact())

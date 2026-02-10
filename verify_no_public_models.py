#!/usr/bin/env python3
"""
Verificar estado limpio - sin modelos públicos
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


async def verify_clean_state():
    client = create_client(DEV_URL, DEV_KEY)
    
    print("="*70)
    print("VERIFICACIÓN FINAL - TODOS LOS MODELOS SON DE TENANTS")
    print("="*70)
    
    # Todos los modelos
    res_all = client.table("utm_model_catalog").select("*").execute()
    
    print(f"\n📊 Total modelos: {len(res_all.data)}\n")
    
    tenants = {
        "fb3be2a1-2685-4583-aed2-143f3eb9239c": "DEMO1",
        "6edf26ab-bbb0-480d-98f6-414347563b0e": "DEMO2",
        "daac0ee6-3b28-412d-8acd-43ec51149188": "CUSTOMER3"
    }
    
    for tenant_id, name in tenants.items():
        print(f"{'='*70}")
        print(f"{name}")
        print('='*70)
        
        res_models = client.table("utm_model_catalog").select("*").eq("tenant_id", tenant_id).execute()
        
        print(f"📦 Modelos: {len(res_models.data)}")
        for m in res_models.data:
            is_public = m.get("is_public")
            model_id = m.get("model_id")
            provider = m.get("provider")
            
            # Mostrar si todavía tiene is_public
            if is_public is not None:
                pub_flag = f" [is_public={is_public}]" if is_public else " [is_public=False]"
            else:
                pub_flag = ""
            
            print(f"   - {model_id} ({provider}){pub_flag}")
        
        # Verificar proveedor
        res_prov = client.table("utm_provider_vault").select("provider_name, api_key").eq("tenant_id", tenant_id).execute()
        if res_prov.data:
            prov = res_prov.data[0]
            print(f"\n🔌 Proveedor: {prov.get('provider_name')}")
            print(f"   API Key: {prov.get('api_key')[:30]}...")
        
        print()
    
    # Verificar si hay modelos huérfanos
    res_orphans = client.table("utm_model_catalog").select("*").is_("tenant_id", "null").execute()
    
    if res_orphans.data:
        print(f"⚠️  MODELOS HUÉRFANOS (sin tenant): {len(res_orphans.data)}")
        for m in res_orphans.data:
            print(f"   - {m.get('model_id')} ({m.get('provider')})")
    else:
        print("✅ NO HAY MODELOS HUÉRFANOS")
    
    # Verificar si hay modelos marcados como públicos
    if any(m.get("is_public") for m in res_all.data):
        res_public = client.table("utm_model_catalog").select("*").eq("is_public", True).execute()
        print(f"\n⚠️  MODELOS MARCADOS COMO PÚBLICOS: {len(res_public.data)}")
        for m in res_public.data:
            print(f"   - {m.get('model_id')} (tenant: {m.get('tenant_id')})")
    else:
        print("\n✅ NO HAY MODELOS MARCADOS COMO PÚBLICOS")
    
    print("\n" + "="*70)
    print("CONCEPTO CORRECTO:")
    print("- Cada tenant tiene SUS PROPIOS modelos")
    print("- Los tenants PAGAN por sus proveedores")
    print("- NO hay modelos compartidos/públicos")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(verify_clean_state())

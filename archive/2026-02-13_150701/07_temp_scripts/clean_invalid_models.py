#!/usr/bin/env python3
"""
Limpiar modelos: solo conservar los de DEMO1, DEMO2, CUSTOMER3
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

# Tenants válidos en DEV
VALID_TENANTS = {
    "fb3be2a1-2685-4583-aed2-143f3eb9239c": "DEMO1",
    "6edf26ab-bbb0-480d-98f6-414347563b0e": "DEMO2",
    "daac0ee6-3b28-412d-8acd-43ec51149188": "CUSTOMER3"
}


async def clean_models():
    client = create_client(DEV_URL, DEV_KEY)
    
    print("="*70)
    print("LIMPIEZA DE MODELOS - SOLO TENANTS DE DEV")
    print("="*70)
    
    # 1. Ver estado actual
    res_all = client.table("utm_model_catalog").select("*").execute()
    print(f"\n📊 Total modelos antes: {len(res_all.data)}")
    
    # 2. Identificar modelos a eliminar
    to_delete = []
    to_keep = []
    
    for model in res_all.data:
        tenant_id = model.get("tenant_id")
        model_id = model.get("model_id")
        
        if tenant_id in VALID_TENANTS:
            to_keep.append((model_id, VALID_TENANTS[tenant_id]))
        else:
            tenant_name = "sin tenant" if not tenant_id else tenant_id[:8]
            to_delete.append((model_id, tenant_name))
    
    print(f"\n❌ Modelos a ELIMINAR: {len(to_delete)}")
    for model_id, tenant in to_delete[:10]:
        print(f"   - {model_id} ({tenant})")
    if len(to_delete) > 10:
        print(f"   ... y {len(to_delete) - 10} más")
    
    print(f"\n✅ Modelos a CONSERVAR: {len(to_keep)}")
    by_tenant = {}
    for model_id, tenant_name in to_keep:
        if tenant_name not in by_tenant:
            by_tenant[tenant_name] = []
        by_tenant[tenant_name].append(model_id)
    
    for tenant_name, models in by_tenant.items():
        print(f"\n{tenant_name} ({len(models)} modelos):")
        for m in models:
            print(f"   - {m}")
    
    # 3. Eliminar modelos inválidos
    print(f"\n{'='*70}")
    print("EJECUTANDO LIMPIEZA")
    print('='*70)
    
    deleted_count = 0
    
    for model_id, tenant_name in to_delete:
        try:
            client.table("utm_model_catalog").delete().eq("model_id", model_id).execute()
            deleted_count += 1
            print(f"   ✅ Eliminado: {model_id}")
        except Exception as e:
            print(f"   ❌ Error eliminando {model_id}: {e}")
    
    print(f"\n✅ Eliminados {deleted_count} modelos")
    
    # 4. Verificar estado final
    res_final = client.table("utm_model_catalog").select("*", count="exact").execute()
    print(f"\n📊 Total modelos después: {res_final.count}")
    
    # Mostrar resumen por tenant
    print(f"\n{'='*70}")
    print("RESUMEN FINAL")
    print('='*70)
    
    for tenant_id, client_name in VALID_TENANTS.items():
        res_models = client.table("utm_model_catalog").select("model_id", count="exact").eq("tenant_id", tenant_id).execute()
        print(f"{client_name}: {res_models.count} modelos")


if __name__ == "__main__":
    asyncio.run(clean_models())

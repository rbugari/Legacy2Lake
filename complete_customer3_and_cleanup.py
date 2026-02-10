#!/usr/bin/env python3
"""
1. Agregar modelos de Azure a CUSTOMER3
2. Limpiar agent_matrix con modelos huérfanos
3. Eliminar modelos finales sin tenant válido
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

CUSTOMER3_TENANT_ID = "daac0ee6-3b28-412d-8acd-43ec51149188"

# Modelos de Azure para CUSTOMER3 (de PROD)
CUSTOMER3_MODELS = [
    {"model_id": "azure-gpt-35-turbo", "provider": "azure"},
    {"model_id": "gpt-4.1", "provider": "azure"},
    {"model_id": "azure-gpt-4o", "provider": "azure"}
]


async def complete_customer3_setup():
    client = create_client(DEV_URL, DEV_KEY)
    
    print("="*70)
    print("PASO 1: AGREGAR MODELOS AZURE A CUSTOMER3")
    print("="*70)
    
    for model in CUSTOMER3_MODELS:
        model_id = model["model_id"]
        provider = model["provider"]
        
        # Verificar si existe
        res_existing = client.table("utm_model_catalog").select("*").eq("model_id", model_id).execute()
        
        if res_existing.data:
            existing = res_existing.data[0]
            current_tenant = existing.get("tenant_id")
            
            if current_tenant == CUSTOMER3_TENANT_ID:
                print(f"   ✅ {model_id} ya pertenece a CUSTOMER3")
            else:
                # Actualizar tenant_id
                try:
                    client.table("utm_model_catalog").update({"tenant_id": CUSTOMER3_TENANT_ID}).eq("model_id", model_id).execute()
                    print(f"   ✅ {model_id} transferido a CUSTOMER3")
                except Exception as e:
                    print(f"   ❌ Error: {e}")
        else:
            # Crear nuevo
            try:
                client.table("utm_model_catalog").insert({
                    "model_id": model_id,
                    "provider": provider,
                    "tenant_id": CUSTOMER3_TENANT_ID
                }).execute()
                print(f"   ✅ {model_id} creado para CUSTOMER3")
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    print(f"\n{'='*70}")
    print("PASO 2: VERIFICAR REFERENCIAS EN AGENT_MATRIX")
    print('='*70)
    
    # Ver agent_matrix
    res_matrix = client.table("utm_agent_matrix").select("*").execute()
    print(f"\n📊 Total entradas en agent_matrix: {len(res_matrix.data)}")
    
    # Agrupar por modelo
    by_model = {}
    for entry in res_matrix.data:
        model_id = entry.get("model_id")
        if model_id:
            if model_id not in by_model:
                by_model[model_id] = 0
            by_model[model_id] += 1
    
    print(f"\nModelos referenciados:")
    for model_id, count in sorted(by_model.items()):
        print(f"   - {model_id}: {count} referencias")
    
    # Verificar si esos modelos existen en catalog
    print(f"\n{'='*70}")
    print("PASO 3: LIMPIAR REFERENCIAS HUÉRFANAS")
    print('='*70)
    
    orphan_count = 0
    for model_id in by_model.keys():
        res_model = client.table("utm_model_catalog").select("tenant_id").eq("model_id", model_id).execute()
        
        if not res_model.data:
            print(f"   ⚠️  {model_id} no existe en catalog - limpiando referencias...")
            try:
                client.table("utm_agent_matrix").delete().eq("model_id", model_id).execute()
                orphan_count += 1
                print(f"      ✅ Eliminadas referencias a {model_id}")
            except Exception as e:
                print(f"      ❌ Error: {e}")
        else:
            tenant_id = res_model.data[0].get("tenant_id")
            if not tenant_id or tenant_id not in ["fb3be2a1-2685-4583-aed2-143f3eb9239c", "6edf26ab-bbb0-480d-98f6-414347563b0e", CUSTOMER3_TENANT_ID]:
                print(f"   ⚠️  {model_id} tiene tenant inválido - limpiando referencias...")
                try:
                    client.table("utm_agent_matrix").delete().eq("model_id", model_id).execute()
                    orphan_count += 1
                    print(f"      ✅ Eliminadas referencias a {model_id}")
                except Exception as e:
                    print(f"      ❌ Error: {e}")
    
    print(f"\n✅ Limpiadas {orphan_count} referencias huérfanas")
    
    # Resumen final
    print(f"\n{'='*70}")
    print("RESUMEN FINAL")
    print('='*70)
    
    tenants = {
        "fb3be2a1-2685-4583-aed2-143f3eb9239c": "DEMO1",
        "6edf26ab-bbb0-480d-98f6-414347563b0e": "DEMO2",
        CUSTOMER3_TENANT_ID: "CUSTOMER3"
    }
    
    for tenant_id, name in tenants.items():
        res_models = client.table("utm_model_catalog").select("model_id", count="exact").eq("tenant_id", tenant_id).execute()
        print(f"{name}: {res_models.count} modelos")
        for m in res_models.data:
            print(f"   - {m.get('model_id')}")


if __name__ == "__main__":
    asyncio.run(complete_customer3_setup())

#!/usr/bin/env python3
"""
Importa catálogo de modelos de PROD a DEV
"""
import asyncio
from supabase import create_client
import json
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

# Mapeo PROD tenant_id → DEV client_id → Provider
MAPPING = {
    "461b0d87-57a4-4ce5-b990-977bec9603eb": {"client": "DEMO1", "provider": "openai"},      # OpenAI - 11 modelos
    "bb579c64-c8c1-4602-bd8e-4f7c1e228419": {"client": "DEMO2", "provider": "groq"},        # Groq - 9 modelos
    "f98edb5e-4165-4c49-9fce-18894e8a818c": {"client": "CUSTOMER3", "provider": "azure"}    # Azure - 3 modelos
}


async def import_model_catalog():
    dev_client = create_client(DEV_URL, DEV_KEY)
    
    # Cargar catálogo de PROD
    with open("prod_model_catalog.json", "r", encoding="utf-8") as f:
        prod_models = json.load(f)
    
    print("="*70)
    print("IMPORTACIÓN DE CATÁLOGO DE MODELOS PROD → DEV")
    print("="*70)
    
    # 1. Obtener tenant_ids de DEV
    dev_tenant_map = {}
    
    for prod_tenant_id, config in MAPPING.items():
        dev_client_id = config["client"]
        res_tenant = dev_client.table("utm_tenants").select("tenant_id").eq("client_id", dev_client_id).execute()
        
        if res_tenant.data:
            dev_tenant_id = res_tenant.data[0]["tenant_id"]
            dev_tenant_map[prod_tenant_id] = {
                "tenant_id": dev_tenant_id,
                "client_id": dev_client_id,
                "provider": config["provider"]
            }
            print(f"✅ {dev_client_id} ({config['provider']}): {dev_tenant_id}")
        else:
            print(f"❌ No se encontró tenant en DEV para {dev_client_id}")
    
    print("\n" + "="*70)
    print("IMPORTANDO MODELOS")
    print("="*70)
    
    # 2. Importar modelos
    imported_count = 0
    skipped_count = 0
    
    for model in prod_models:
        prod_tenant_id = model.get("tenant_id")
        
        # Solo importar modelos de los tenants mapeados
        if prod_tenant_id not in dev_tenant_map:
            skipped_count += 1
            continue
        
        tenant_info = dev_tenant_map[prod_tenant_id]
        dev_tenant_id = tenant_info["tenant_id"]
        dev_client_id = tenant_info["client_id"]
        provider = tenant_info["provider"]
        model_id = model.get("model_id")
        
        # Verificar si ya existe
        res_existing = dev_client.table("utm_model_catalog").select("*").eq("tenant_id", dev_tenant_id).eq("model_id", model_id).execute()
        
        if res_existing.data:
            skipped_count += 1
            continue
        
        # Insertar modelo
        new_model = {
            "tenant_id": dev_tenant_id,
            "model_id": model_id,
            "provider": provider,
            "is_public": False  # Modelos privados del tenant
        }
        
        try:
            dev_client.table("utm_model_catalog").insert(new_model).execute()
            imported_count += 1
            print(f"   ✅ {dev_client_id}: {model_id}")
        except Exception as e:
            print(f"   ❌ Error importando {model_id}: {e}")
    
    print("\n" + "="*70)
    print("RESUMEN DE IMPORTACIÓN")
    print("="*70)
    print(f"Modelos importados: {imported_count}")
    print(f"Modelos omitidos: {skipped_count}")
    
    # Mostrar resumen por tenant
    print("\n" + "="*70)
    print("MODELOS POR TENANT EN DEV")
    print("="*70)
    
    for prod_tenant_id, config in MAPPING.items():
        if prod_tenant_id in dev_tenant_map:
            tenant_info = dev_tenant_map[prod_tenant_id]
            dev_tenant_id = tenant_info["tenant_id"]
            dev_client_id = tenant_info["client_id"]
            res_count = dev_client.table("utm_model_catalog").select("model_id", count="exact").eq("tenant_id", dev_tenant_id).execute()
            
            print(f"\n{dev_client_id}: {res_count.count} modelos")
            
            # Listar modelos
            res_models = dev_client.table("utm_model_catalog").select("model_id, is_public").eq("tenant_id", dev_tenant_id).execute()
            for m in res_models.data:
                visibility = "🌐 public" if m.get("is_public") else "🔒 private"
                print(f"  {visibility} {m.get('model_id')}")


if __name__ == "__main__":
    asyncio.run(import_model_catalog())

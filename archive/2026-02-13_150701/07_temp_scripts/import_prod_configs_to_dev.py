#!/usr/bin/env python3
"""
Importa configuraciones de proveedores de PROD a DEV
Mapea:
- DEMO1 (OpenAI) → DEV DEMO1  
- DEMO2 (Groq) → DEV DEMO2
- DEMO3 (Azure) → DEV CUSTOMER3
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

# Mapeo de configuraciones PROD → DEV
# PROD tenant_id → DEV client_id
MAPPING = {
    "461b0d87-57a4-4ce5-b990-977bec9603eb": "DEMO1",   # OpenAI
    "bb579c64-c8c1-4602-bd8e-4f7c1e228419": "DEMO2",   # Groq
    "f98edb5e-4165-4c49-9fce-18894e8a818c": "CUSTOMER3"  # Azure (renombrado)
}


async def import_configs():
    dev_client = create_client(DEV_URL, DEV_KEY)
    
    # Cargar datos exportados de PROD
    with open("prod_legacy_export.json", "r", encoding="utf-8") as f:
        prod_data = json.load(f)
    
    print("="*70)
    print("IMPORTACIÓN DE CONFIGURACIONES PROD → DEV")
    print("="*70)
    
    # 1. Obtener tenant_ids de DEV
    dev_tenant_map = {}
    
    for prod_tenant_id, dev_client_id in MAPPING.items():
        res_tenant = dev_client.table("utm_tenants").select("tenant_id").eq("client_id", dev_client_id).execute()
        
        if res_tenant.data:
            dev_tenant_id = res_tenant.data[0]["tenant_id"]
            dev_tenant_map[prod_tenant_id] = dev_tenant_id
            print(f"✅ {dev_client_id}: {dev_tenant_id}")
        else:
            print(f"❌ No se encontró tenant en DEV para {dev_client_id}")
    
    print("\n" + "="*70)
    print("IMPORTANDO PROVEEDORES")
    print("="*70)
    
    # 2. Importar configuraciones de provider_vault
    for prov in prod_data["provider_vault"]:
        prod_tenant_id = prov["tenant_id"]
        
        if prod_tenant_id not in dev_tenant_map:
            continue
        
        dev_tenant_id = dev_tenant_map[prod_tenant_id]
        dev_client_id = MAPPING[prod_tenant_id]
        
        print(f"\n📦 Importando {prov['provider_name']} para {dev_client_id}...")
        
        # Verificar si ya existe
        res_existing = dev_client.table("utm_provider_vault").select("*").eq("tenant_id", dev_tenant_id).eq("provider_name", prov["provider_name"]).execute()
        
        if res_existing.data:
            print(f"   ⚠️  Ya existe configuración de {prov['provider_name']} para {dev_client_id}")
            print(f"   ¿Actualizar? (y/n)")
            # Por ahora skip
            continue
        
        # Insertar nueva configuración
        new_prov = {
            "tenant_id": dev_tenant_id,
            "provider_name": prov["provider_name"],
            "api_key": prov["api_key"],
            "base_url": prov["base_url"],
            "is_active": prov["is_active"]
        }
        
        try:
            res_insert = dev_client.table("utm_provider_vault").insert(new_prov).execute()
            print(f"   ✅ {prov['provider_name']} importado")
            print(f"      Base URL: {prov['base_url']}")
            print(f"      API Key: {prov['api_key'][:20]}...")
        except Exception as e:
            print(f"   ❌ Error importando: {e}")
    
    print("\n" + "="*70)
    print("IMPORTACIÓN COMPLETADA")
    print("="*70)
    
    # Mostrar resumen
    for prod_tenant_id, dev_client_id in MAPPING.items():
        if prod_tenant_id in dev_tenant_map:
            dev_tenant_id = dev_tenant_map[prod_tenant_id]
            res_count = dev_client.table("utm_provider_vault").select("id", count="exact").eq("tenant_id", dev_tenant_id).execute()
            print(f"✅ {dev_client_id}: {res_count.count} proveedores configurados")


if __name__ == "__main__":
    asyncio.run(import_configs())

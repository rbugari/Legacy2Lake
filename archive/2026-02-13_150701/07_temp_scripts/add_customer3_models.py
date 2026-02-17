#!/usr/bin/env python3
"""
Agregar modelos faltantes de CUSTOMER3
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

# Tenant CUSTOMER3
CUSTOMER3_TENANT_ID = "daac0ee6-3b28-412d-8acd-43ec51149188"

# Modelos de PROD para CUSTOMER3  
CUSTOMER3_MODELS = [
    "azure-gpt-35-turbo",  # Ya existe como público
    "gpt-4.1",             # Falta
    "azure-gpt-4o"         # Ya existe como público
]


async def add_missing_models():
    client = create_client(DEV_URL, DEV_KEY)
    
    print("="*70)
    print("AGREGANDO MODELOS FALTANTES PARA CUSTOMER3")
    print("="*70)
    
    for model_id in CUSTOMER3_MODELS:
        print(f"\n📦 Verificando {model_id}...")
        
        # Verificar si existe
        res_existing = client.table("utm_model_catalog").select("*").eq("model_id", model_id).execute()
        
        if res_existing.data:
            existing = res_existing.data[0]
            is_public = existing.get("is_public")
            owner_tenant = existing.get("tenant_id")
            
            if is_public:
                print(f"   ℹ️  Ya existe como PÚBLICO - todos los tenants pueden usarlo")
            elif owner_tenant == CUSTOMER3_TENANT_ID:
                print(f"   ✅ Ya existe como PRIVADO de CUSTOMER3")
            else:
                print(f"   ⚠️  Ya existe como PRIVADO de otro tenant: {owner_tenant}")
        else:
            # No existe - crearlo para CUSTOMER3
            new_model = {
                "model_id": model_id,
                "provider": "azure",
                "tenant_id": CUSTOMER3_TENANT_ID,
                "is_public": False
            }
            
            try:
                client.table("utm_model_catalog").insert(new_model).execute()
                print(f"   ✅ Creado como PRIVADO para CUSTOMER3")
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    # Resumen final
    print("\n" + "="*70)
    print("RESUMEN CUSTOMER3")
    print("="*70)
    
    res_models = client.table("utm_model_catalog").select("model_id, is_public").eq("tenant_id", CUSTOMER3_TENANT_ID).execute()
    print(f"\n📦 Modelos privados: {len(res_models.data)}")
    for m in res_models.data:
        print(f"   - {m.get('model_id')}")
    
    # Mostrar modelos públicos disponibles (Azure)
    res_public = client.table("utm_model_catalog").select("model_id").eq("provider", "azure").eq("is_public", True).execute()
    print(f"\n🌐 Modelos Azure públicos disponibles: {len(res_public.data)}")
    for m in res_public.data:
        print(f"   - {m.get('model_id')}")


if __name__ == "__main__":
    asyncio.run(add_missing_models())

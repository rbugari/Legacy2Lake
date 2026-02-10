#!/usr/bin/env python3
"""
Actualizar gpt-4.1 a is_public=False
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


async def fix_public_flag():
    client = create_client(DEV_URL, DEV_KEY)
    
    print("="*70)
    print("ACTUALIZAR is_public=False PARA TODOS LOS MODELOS")
    print("="*70)
    
    # Actualizar todos los modelos a is_public=False
    try:
        res = client.table("utm_model_catalog").update({"is_public": False}).eq("is_public", True).execute()
        print(f"✅ Actualizados {len(res.data)} modelos a is_public=False")
        for m in res.data:
            print(f"   - {m.get('model_id')}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Verificar
    res_public = client.table("utm_model_catalog").select("*").eq("is_public", True).execute()
    print(f"\n📊 Modelos con is_public=True: {len(res_public.data)}")
    
    if res_public.data:
        for m in res_public.data:
            print(f"   - {m.get('model_id')}")
    else:
        print("   ✅ NINGUNO - todos son privados de sus tenants")


if __name__ == "__main__":
    asyncio.run(fix_public_flag())

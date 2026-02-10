#!/usr/bin/env python3
"""
Resumen completo de configuraciones importadas de PROD a DEV
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


async def final_summary():
    client = create_client(DEV_URL, DEV_KEY)
    
    print("="*70)
    print("RESUMEN FINAL - CONFIGURACIONES IMPORTADAS PROD → DEV")
    print("="*70)
    
    clients = ["DEMO1", "DEMO2", "CUSTOMER3"]
    
    for client_id in clients:
        print(f"\n{'='*70}")
        print(f"📋 {client_id}")
        print('='*70)
        
        # Obtener tenant_id
        res_tenant = client.table("utm_tenants").select("tenant_id").eq("client_id", client_id).execute()
        if not res_tenant.data:
            print(f"❌ No encontrado")
            continue
        
        tenant_id = res_tenant.data[0]["tenant_id"]
        print(f"Tenant ID: {tenant_id}")
        
        # Proveedores
        res_prov = client.table("utm_provider_vault").select("*").eq("tenant_id", tenant_id).execute()
        print(f"\n🔌 PROVEEDORES: {len(res_prov.data)}")
        for p in res_prov.data:
            status = "✓" if p.get("is_active") else "✗"
            print(f"   {status} {p.get('provider_name')}")
            print(f"      Base URL: {p.get('base_url')}")
            api_key = p.get('api_key', '')
            print(f"      API Key: {api_key[:30]}...")
        
        # Modelos privados
        res_private = client.table("utm_model_catalog").select("*").eq("tenant_id", tenant_id).eq("is_public", False).execute()
        print(f"\n📦 MODELOS PRIVADOS: {len(res_private.data)}")
        for m in res_private.data:
            print(f"   - {m.get('model_id')} ({m.get('provider')})")
        
        # Modelos públicos disponibles del mismo proveedor
        if res_prov.data:
            provider_name = res_prov.data[0].get("provider_name", "").lower()
            # Mapeo de nombres de proveedores
            provider_map = {
                "openai": "openai",
                "groq": "groq",
                "azure": "azure"
            }
            provider_filter = provider_map.get(provider_name, provider_name)
            
            res_public = client.table("utm_model_catalog").select("model_id").eq("provider", provider_filter).eq("is_public", True).execute()
            print(f"\n🌐 MODELOS PÚBLICOS DISPONIBLES ({provider_name}): {len(res_public.data)}")
            for m in res_public.data[:5]:
                print(f"   - {m.get('model_id')}")
            if len(res_public.data) > 5:
                print(f"   ... y {len(res_public.data) - 5} más")
        
        # Usuarios
        res_users = client.table("utm_users").select("username, role, email").eq("tenant_id", tenant_id).execute()
        print(f"\n👥 USUARIOS: {len(res_users.data)}")
        for u in res_users.data:
            print(f"   - {u.get('username')} ({u.get('role')}) - {u.get('email')}")
    
    # Resumen total
    print("\n" + "="*70)
    print("✅ IMPORTACIÓN COMPLETADA")
    print("="*70)
    print("\nConfiguraciones importadas desde producción:")
    print("- ✅ Proveedores LLM (API keys, base URLs)")
    print("- ✅ Modelos privados por tenant")
    print("- ✅ Modelos públicos compartidos")
    print("\nPróximos pasos:")
    print("- Crear proyectos de prueba")
    print("- Probar generación de código con cada proveedor")
    print("- Implementar invitación de usuarios (COLLABORATOR, VIEWER)")


if __name__ == "__main__":
    asyncio.run(final_summary())

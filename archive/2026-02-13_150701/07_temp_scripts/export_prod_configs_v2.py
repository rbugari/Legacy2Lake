#!/usr/bin/env python3
"""
Extrae configuraciones de DEMO1, DEMO2, DEMO3 de PRODUCCIÓN
Usa Supabase API con service_role key
"""
import asyncio
from supabase import create_client
import json
from datetime import datetime
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
print("✅ SSL verification disabled")

# Configuración de producción
PROD_URL = "https://wdmlnvppkhjjeuiutnjl.supabase.co"
PROD_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndkbWxudnBwa2hqamV1aXV0bmpsIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDA4MjM2NiwiZXhwIjoyMDg1NjU4MzY2fQ.ptqq5JugnDa2FcuTeSl28PfbfKfW5Qz4tDuMggH9eeg"

# Client IDs a exportar
TARGET_CLIENTS = ["DEMO1", "DEMO2", "DEMO3"]


async def get_tenant_configs(client_ids):
    """Extrae todas las configuraciones de los tenants especificados"""
    
    client = create_client(PROD_URL, PROD_KEY)
    configs = {}
    
    for client_id in client_ids:
        print(f"\n{'='*70}")
        print(f"EXTRAYENDO: {client_id}")
        print('='*70)
        
        try:
            # 1. Obtener tenant_id desde utm_tenants
            res_tenant = client.table("utm_tenants").select("tenant_id, client_id").eq("client_id", client_id).execute()
            
            if not res_tenant.data:
                print(f"❌ No se encontró tenant con client_id={client_id}")
                continue
            
            tenant_id = res_tenant.data[0]["tenant_id"]
            print(f"✅ Tenant ID: {tenant_id}")
            
            # 2. Extraer utm_vault
            res_vault = client.table("utm_vault").select("*").eq("tenant_id", tenant_id).execute()
            vault_entries = res_vault.data or []
            print(f"📦 utm_vault: {len(vault_entries)} entradas")
            
            # 3. Extraer utm_provider_vault
            res_provider = client.table("utm_provider_vault").select("*").eq("tenant_id", tenant_id).execute()
            provider_entries = res_provider.data or []
            print(f"🔌 utm_provider_vault: {len(provider_entries)} proveedores")
            
            # Mostrar detalles de proveedores
            for prov in provider_entries:
                status = "✓ ACTIVO" if prov.get("is_active") else "✗ inactivo"
                print(f"   - {prov.get('provider_name')}: {prov.get('model_ids_json', '[]')} {status}")
            
            # 4. Contar proyectos
            res_projects = client.table("utm_projects").select("project_id", count="exact").eq("tenant_id", tenant_id).execute()
            project_count = res_projects.count or 0
            print(f"📊 Proyectos: {project_count}")
            
            # Guardar en configs
            configs[client_id] = {
                "tenant_id": tenant_id,
                "client_id": client_id,
                "vault": vault_entries,
                "provider_vault": provider_entries,
                "project_count": project_count,
                "extracted_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error extrayendo {client_id}: {e}")
            configs[client_id] = {"error": str(e)}
    
    return configs


async def main():
    print("="*70)
    print("EXTRACCIÓN DE CONFIGURACIONES - PRODUCCIÓN")
    print("="*70)
    
    configs = await get_tenant_configs(TARGET_CLIENTS)
    
    # Guardar a JSON
    output_file = "prod_configs_export.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(configs, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*70}")
    print(f"✅ Configuraciones exportadas a: {output_file}")
    print('='*70)
    
    # Resumen
    print("\nRESUMEN:")
    for client_id, data in configs.items():
        if "error" in data:
            print(f"❌ {client_id}: ERROR - {data['error']}")
        else:
            print(f"✅ {client_id}: {len(data['vault'])} vault + {len(data['provider_vault'])} providers + {data['project_count']} projects")


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Extraer utm_model_catalog de producción
"""
import asyncio
from supabase import create_client
import ssl
import httpcore
import json

# Bypass SSL certificate verification
_original_start_tls = httpcore._backends.sync.SyncStream.start_tls

def _patched_start_tls(self, *args, **kwargs):
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    kwargs['ssl_context'] = ssl_context
    return _original_start_tls(self, *args, **kwargs)

httpcore._backends.sync.SyncStream.start_tls = _patched_start_tls

# Configuración de producción
PROD_URL = "https://wdmlnvppkhjjeuiutnjl.supabase.co"
PROD_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndkbWxudnBwa2hqamV1aXV0bmpsIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDA4MjM2NiwiZXhwIjoyMDg1NjU4MzY2fQ.ptqq5JugnDa2FcuTeSl28PfbfKfW5Qz4tDuMggH9eeg"


async def extract_model_catalog():
    client = create_client(PROD_URL, PROD_KEY)
    
    print("="*70)
    print("EXTRAYENDO utm_model_catalog DE PRODUCCIÓN")
    print("="*70)
    
    # Extraer catálogo de modelos
    try:
        res_models = client.table("utm_model_catalog").select("*").execute()
        
        print(f"\n✅ Modelos encontrados: {len(res_models.data)}\n")
        
        # Agrupar por tenant
        by_tenant = {}
        
        for model in res_models.data:
            tenant_id = model.get("tenant_id")
            
            if tenant_id not in by_tenant:
                by_tenant[tenant_id] = []
            
            by_tenant[tenant_id].append(model)
            
            print(f"Model ID: {model.get('model_id')}")
            print(f"Tenant ID: {tenant_id}")
            print(f"Display Name: {model.get('display_name')}")
            print(f"Provider: {model.get('provider_name')}")
            print(f"Active: {model.get('is_active')}")
            print("-" * 70)
        
        # Resumen por tenant
        print("\n" + "="*70)
        print("RESUMEN POR TENANT")
        print("="*70)
        
        for tenant_id, models in by_tenant.items():
            print(f"\nTenant: {tenant_id}")
            print(f"Modelos: {len(models)}")
            for m in models:
                status = "✓" if m.get("is_active") else "✗"
                print(f"  {status} {m.get('model_id')} ({m.get('provider_name')})")
        
        # Exportar
        output_file = "prod_model_catalog.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(res_models.data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Catálogo exportado a: {output_file}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(extract_model_catalog())

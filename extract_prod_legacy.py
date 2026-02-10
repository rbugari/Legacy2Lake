#!/usr/bin/env python3
"""
Extraer configuraciones de DEMO1, DEMO2, DEMO3 usando estructura LEGACY
Producción NO ha migrado a v3.9 todavía
"""
import asyncio
from supabase import create_client
import ssl
import httpcore
import json
from datetime import datetime

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


async def extract_legacy_configs():
    client = create_client(PROD_URL, PROD_KEY)
    
    print("="*70)
    print("EXTRAYENDO CONFIGURACIONES LEGACY - PRODUCCIÓN")
    print("(Producción todavía NO está en v3.9)")
    print("="*70)
    
    # 1. Obtener lista completa de clients con toda su info
    res_clients = client.table("utm_clients").select("*").execute()
    
    print(f"\n✅ Clients encontrados: {len(res_clients.data)}\n")
    
    # Mostrar estructura completa
    for c in res_clients.data:
        print(f"Client: {c}")
        print("-" * 70)
    
    # 2. Buscar tenants
    res_tenants = client.table("utm_tenants").select("*").execute()
    
    print(f"\n✅ Tenants encontrados: {len(res_tenants.data)}\n")
    
    for t in res_tenants.data:
        print(f"Tenant: {t}")
        print("-" * 70)
    
    # 3. Ver provider_vault
    res_prov = client.table("utm_provider_vault").select("*").execute()
    
    print(f"\n✅ Provider Vault: {len(res_prov.data)} configuraciones\n")
    
    for p in res_prov.data:
        print(f"Provider: {p}")
        print("-" * 70)
    
    # Exportar todo
    export_data = {
        "clients": res_clients.data,
        "tenants": res_tenants.data,
        "provider_vault": res_prov.data,
        "extracted_at": datetime.now().isoformat()
    }
    
    output_file = "prod_legacy_export.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Datos exportados a: {output_file}")


if __name__ == "__main__":
    asyncio.run(extract_legacy_configs())

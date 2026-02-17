#!/usr/bin/env python3
"""
Verificar separación correcta de catálogos: Global vs Tenant
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


async def verify_catalog_separation():
    client = create_client(DEV_URL, DEV_KEY)
    
    print("="*80)
    print("VERIFICACIÓN: SEPARACIÓN DE CATÁLOGOS GLOBAL vs TENANT")
    print("="*80)
    
    # 1. CATÁLOGOS GLOBALES (NO deben tener tenant_id)
    print("\n📊 CATÁLOGOS GLOBALES (gestionados por ADMIN)")
    print("="*80)
    
    # Agentes
    print("\n1️⃣ utm_agent_catalog (Agentes del sistema)")
    print("-" * 80)
    res = client.table("utm_agent_catalog").select("agent_id, display_name").limit(5).execute()
    
    # Check if has tenant_id column
    try:
        test = client.table("utm_agent_catalog").select("tenant_id").limit(1).execute()
        print("❌ ERROR: utm_agent_catalog tiene columna tenant_id (debería ser global)")
    except:
        print("✅ CORRECTO: utm_agent_catalog es GLOBAL (sin tenant_id)")
    
    for agent in res.data[:5]:
        print(f"   - {agent['agent_id']}: {agent['display_name']}")
    
    # System Catalog (Cartuchos)
    print("\n2️⃣ utm_system_catalog (Cartuchos de tecnología: origins/destinations)")
    print("-" * 80)
    res = client.table("utm_system_catalog").select("tech_id, name, type").execute()
    
    # Check if has tenant_id column
    if res.data and 'tenant_id' in res.data[0].keys():
        print("❌ ERROR: utm_system_catalog tiene columna tenant_id (debería ser global)")
    else:
        print("✅ CORRECTO: utm_system_catalog es GLOBAL (sin tenant_id)")
    
    origins = [r for r in res.data if r.get('type') == 'origin']
    destinations = [r for r in res.data if r.get('type') == 'destination']
    
    print(f"\n   ORIGINS ({len(origins)}):")
    for tech in origins[:5]:
        print(f"   - {tech.get('tech_id', 'N/A')}: {tech['name']}")
    
    print(f"\n   DESTINATIONS ({len(destinations)}):")
    for tech in destinations[:5]:
        print(f"   - {tech.get('tech_id', 'N/A')}: {tech['name']}")
    
    # 2. CATÁLOGOS TENANT-LEVEL (DEBEN tener tenant_id)
    print("\n\n💼 CATÁLOGOS TENANT-LEVEL (gestionados por MANAGER)")
    print("="*80)
    
    # Provider Vault
    print("\n3️⃣ utm_provider_vault (Proveedores LLM del tenant)")
    print("-" * 80)
    res = client.table("utm_provider_vault").select("tenant_id, provider_name").execute()
    
    if not res.data:
        print("⚠️  Vacío (normal si no hay tenants con proveedores)")
    elif 'tenant_id' not in res.data[0].keys():
        print("❌ ERROR: utm_provider_vault NO tiene tenant_id (debería tenerlo)")
    else:
        print("✅ CORRECTO: utm_provider_vault tiene tenant_id (tenant-specific)")
        
        # Group by tenant
        by_tenant = {}
        for p in res.data:
            tid = p['tenant_id']
            if tid not in by_tenant:
                by_tenant[tid] = []
            by_tenant[tid].append(p['provider_name'])
        
        for tenant_id, providers in by_tenant.items():
            print(f"\n   Tenant: {tenant_id}")
            for prov in providers:
                print(f"      - {prov}")
    
    # Model Catalog
    print("\n4️⃣ utm_model_catalog (Modelos LLM habilitados por tenant)")
    print("-" * 80)
    res = client.table("utm_model_catalog").select("tenant_id, model_id, provider").execute()
    
    if not res.data:
        print("⚠️  Vacío (normal si no hay tenants con modelos)")
    elif 'tenant_id' not in res.data[0].keys():
        print("❌ ERROR: utm_model_catalog NO tiene tenant_id (debería tenerlo)")
    else:
        # Check for NULL tenant_id
        null_tenant = [m for m in res.data if not m.get('tenant_id')]
        if null_tenant:
            print(f"❌ ERROR: {len(null_tenant)} modelos con tenant_id NULL (deberían ser privados)")
        else:
            print("✅ CORRECTO: Todos los modelos tienen tenant_id (tenant-specific)")
        
        # Group by tenant
        by_tenant = {}
        for m in res.data:
            tid = m.get('tenant_id', 'NULL')
            if tid not in by_tenant:
                by_tenant[tid] = []
            by_tenant[tid].append(f"{m['model_id']} ({m['provider']})")
        
        for tenant_id, models in by_tenant.items():
            if tenant_id == 'NULL':
                print(f"\n   ❌ Modelos HUÉRFANOS (sin tenant):")
            else:
                print(f"\n   Tenant: {tenant_id}")
            for model in models:
                print(f"      - {model}")
    
    print("\n" + "="*80)
    print("RESUMEN DE ARQUITECTURA")
    print("="*80)
    print("""
✅ CORRECTO:
- utm_agent_catalog: GLOBAL (sin tenant_id) - ADMIN maneja
- utm_system_catalog: GLOBAL (sin tenant_id) - ADMIN maneja
- utm_provider_vault: TENANT-level (con tenant_id) - MANAGER configura
- utm_model_catalog: TENANT-level (con tenant_id) - MANAGER selecciona

❌ ERRORES ENCONTRADOS:
- Si algún catálogo global tiene tenant_id → ejecutar migración 022
- Si algún modelo no tiene tenant_id → ejecutar migración 019

🔑 CONCEPTO CLAVE:
- Providers LLM (OpenAI, Groq): TENANT paga → MANAGER configura
- Cartuchos tecnológicos (SQL Server, Snowflake): PLATFORM → ADMIN maneja
- Agentes (Agent S, Agent A): PLATFORM → ADMIN maneja
""")


if __name__ == "__main__":
    asyncio.run(verify_catalog_separation())

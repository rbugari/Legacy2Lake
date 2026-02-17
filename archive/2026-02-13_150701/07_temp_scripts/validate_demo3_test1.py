"""
Validate demo3 tenant configuration for Sprint 0 Day 4 Agent C testing
"""
import os
import sys
from dotenv import load_dotenv
from supabase import create_client

sys.path.append(os.path.join(os.path.dirname(__file__), 'apps', 'api'))
load_dotenv()

def main():
    client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
    
    print("="*80)
    print("🔍 VALIDACIÓN TENANT DEMO3 + PROYECTO TEST1 - Sprint 0 Day 4")
    print("="*80)
    
    # 1. Find demo3 user (might be in utm_users, not utm_tenants)
    print("\n1️⃣  Buscando usuario demo3...")
    user_res = client.table("utm_users").select("user_id, username, email, tenant_id, role").eq("username", "demo3").execute()
    
    if not user_res.data:
        print("   ❌ Usuario demo3 NO encontrado")
        print("\n   Usuarios disponibles con 'demo' en el nombre:")
        all_demos = client.table("utm_users").select("username, email, role, tenant_id").ilike("username", "%demo%").execute()
        for u in all_demos.data[:10]:
            print(f"      - {u.get('username')} ({u.get('email')}) - Role: {u.get('role')}")
        return
    
    demo3_user = user_res.data[0]
    tenant_id = demo3_user["tenant_id"]
    
    print(f"   ✅ Usuario demo3 encontrado")
    print(f"      User ID: {demo3_user['user_id']}")
    print(f"      Email: {demo3_user['email']}")
    print(f"      Role: {demo3_user['role']}")
    print(f"      Tenant ID: {tenant_id}")
    
    # 2. Get tenant details
    print(f"\n2️⃣  Información del tenant...")
    tenant_res = client.table("utm_tenants").select("*").eq("tenant_id", tenant_id).execute()
    
    if tenant_res.data:
        tenant = tenant_res.data[0]
        print(f"   ✅ Tenant encontrado")
        print(f"      Client ID: {tenant.get('client_id')}")
        print(f"      Plan: {tenant.get('tier', 'N/A')}")
    else:
        print(f"   ⚠️  Tenant {tenant_id} no encontrado en utm_tenants")
    
    # 3. Find TEST1 project
    print(f"\n3️⃣  Buscando proyecto TEST1...")
    proj_res = client.table("utm_projects").select(
        "project_id, name, tenant_id, stage, status, settings, config, created_at"
    ).eq("tenant_id", tenant_id).eq("name", "TEST1").execute()
    
    if not proj_res.data:
        print("   ❌ Proyecto TEST1 NO encontrado para este tenant")
        print("\n   Proyectos existentes para este tenant:")
        all_projs = client.table("utm_projects").select("name, stage, status, settings").eq("tenant_id", tenant_id).execute()
        if all_projs.data:
            for p in all_projs.data:
                settings = p.get('settings', {})
                source = settings.get('source_tech') if isinstance(settings, dict) else 'N/A'
                target = settings.get('target_tech') if isinstance(settings, dict) else 'N/A'
                print(f"      - {p.get('name')} (Stage: {p.get('stage')}, Source: {source}, Target: {target})")
        else:
            print("      (ninguno)")
        return
    
    project = proj_res.data[0]
    settings = project.get('settings', {})
    config = project.get('config', {})
    
    print(f"   ✅ Proyecto TEST1 encontrado")
    print(f"      Project ID: {project['project_id']}")
    print(f"      Stage: {project.get('stage', 'N/A')}")
    print(f"      Status: {project.get('status', 'N/A')}")
    
    if isinstance(settings, dict):
        print(f"      Source: {settings.get('source_tech', 'N/A')}")
        print(f"      Target: {settings.get('target_tech', 'N/A')}")
    
    print(f"      Created: {project.get('created_at', 'N/A')}")
    
    # 4. Check Azure provider configuration
    print(f"\n4️⃣  Validating Azure provider configuration...")
    vault_res = client.table("utm_provider_vault").select(
        "provider_name, is_active, base_url"
    ).eq("tenant_id", tenant_id).execute()
    
    if not vault_res.data:
        print("   ❌ NO hay providers configurados en vault")
    else:
        print(f"   ✅ {len(vault_res.data)} provider(s) encontrado(s):")
        azure_found = False
        for prov in vault_res.data:
            status = "✅ ACTIVO" if prov.get('is_active') else "❌ INACTIVO"
            print(f"      - {prov.get('provider_name')}: {status}")
            if prov.get('base_url'):
                print(f"        Base URL: {prov.get('base_url')}")
            if 'azure' in prov.get('provider_name', '').lower():
                azure_found = True
        
        if not azure_found:
            print("\n   ⚠️  WARNING: No se encontró provider 'azure' configurado")
    
    # 5. Check models in catalog
    print(f"\n5️⃣  Validating Azure models in catalog...")
    models_res = client.table("utm_model_catalog").select(
        "model_id, provider, deployment_id, api_version, is_active"
    ).eq("tenant_id", tenant_id).execute()
    
    if not models_res.data:
        print("   ❌ NO hay modelos en el catálogo para este tenant")
    else:
        active_models = [m for m in models_res.data if m.get('is_active', True)]
        print(f"   ✅ {len(active_models)} modelo(s) activo(s) de {len(models_res.data)} total(es):")
        
        for model in active_models:
            print(f"\n      📦 {model.get('model_id')}")
            print(f"         Provider: {model.get('provider')}")
            print(f"         Deployment ID: {model.get('deployment_id', 'N/A')}")
            print(f"         API Version: {model.get('api_version', 'N/A')}")
        
        azure_models = [m for m in active_models if m.get('provider') == 'azure']
        if not azure_models:
            print("\n   ⚠️  WARNING: No hay modelos Azure activos")
    
    # 6. Check agent matrix configuration
    print(f"\n6️⃣  Validating agent matrix configuration...")
    matrix_res = client.table("utm_agent_matrix").select(
        "agent_id, model_id, provider, is_active"
    ).eq("tenant_id", tenant_id).eq("is_active", True).execute()
    
    if not matrix_res.data:
        print("   ❌ NO hay agentes configurados en matrix")
    else:
        print(f"   ✅ {len(matrix_res.data)} agente(s) configurado(s):")
        for agent in matrix_res.data:
            print(f"      - {agent.get('agent_id')} → {agent.get('model_id')} ({agent.get('provider')})")
    
    # 7. Final diagnosis
    print("\n" + "="*80)
    print("📊 DIAGNÓSTICO FINAL")
    print("="*80)
    
    checks = {
        "Usuario demo3": user_res.data,
        "Proyecto TEST1": proj_res.data,
        "Provider vault": vault_res.data,
        "Modelos en catálogo": models_res.data if 'models_res' in locals() else None,
        "Agent matrix": matrix_res.data if 'matrix_res' in locals() else None
    }
    
    all_ok = all(checks.values())
    
    for check_name, check_result in checks.items():
        status = "✅" if check_result else "❌"
        print(f"{status} {check_name}")
    
    print("\n" + "="*80)
    
    if all_ok:
        print("✅ ¡CONFIGURACIÓN COMPLETA! Listo para Agent C testing")
        print("\nPuedes usar este proyecto TEST1 para testear todas las fases:")
        print("  - Bronze Layer ingestion")
        print("  - Silver Layer transformations")
        print("  - Gold Layer aggregations")
        print(f"\nTenant ID: {tenant_id}")
        print(f"Project ID: {project['project_id']}")
    else:
        print("❌ CONFIGURACIÓN INCOMPLETA - Faltan componentes")
        print("\nAcciones requeridas:")
        if not vault_res.data:
            print("  1. Configurar Azure provider en vault")
        if not models_res.data:
            print("  2. Agregar modelos Azure al catálogo")
        if not matrix_res.data:
            print("  3. Configurar agent matrix")

if __name__ == "__main__":
    main()

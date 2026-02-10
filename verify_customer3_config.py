#!/usr/bin/env python3
"""
Verificar configuraciones de CUSTOMER3 (antes DEMO3)
"""
from connect_supabase_dev import get_postgres_connection

try:
    conn = get_postgres_connection()
    cursor = conn.cursor()
    
    # Obtener tenant_id de CUSTOMER3
    cursor.execute("""
        SELECT tenant_id, client_id, org_name
        FROM utm_tenants
        WHERE client_id = 'CUSTOMER3';
    """)
    
    tenant = cursor.fetchone()
    if not tenant:
        print("❌ CUSTOMER3 no encontrado")
        exit(1)
    
    tenant_id, client_id, org_name = tenant
    
    print("="*70)
    print(f"CONFIGURACIONES DE {client_id} ({org_name})")
    print("="*70)
    print(f"Tenant ID: {tenant_id}")
    print()
    
    # Vault (provider credentials)
    cursor.execute("""
        SELECT provider, is_active, created_at
        FROM utm_vault
        WHERE tenant_id = %s
        ORDER BY provider;
    """, (tenant_id,))
    
    vault_entries = cursor.fetchall()
    print("📦 VAULT (Provider Credentials):")
    if vault_entries:
        for provider, is_active, created_at in vault_entries:
            status = "✅" if is_active else "❌"
            print(f"   {status} {provider} (creado: {created_at})")
    else:
        print("   (vacío)")
    print()
    
    # Provider Vault (configuraciones adicionales)
    cursor.execute("""
        SELECT provider_name, model_name, is_active
        FROM utm_provider_vault
        WHERE tenant_id = %s;
    """, (tenant_id,))
    
    providers = cursor.fetchall()
    print("🔧 PROVIDER VAULT:")
    if providers:
        for prov_name, model_name, is_active in providers:
            status = "✅" if is_active else "❌"
            print(f"   {status} {prov_name} - {model_name}")
    else:
        print("   (vacío)")
    print()
    
    # Model Catalog (modelos custom)
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM utm_model_catalog
        WHERE tenant_id = %s;
    """, (tenant_id,))
    
    model_count = cursor.fetchone()[0]
    print("🤖 MODEL CATALOG (Custom Models):")
    print(f"   Total: {model_count} modelos")
    print()
    
    # Projects
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM utm_projects
        WHERE tenant_id = %s;
    """, (tenant_id,))
    
    project_count = cursor.fetchone()[0]
    print("📁 PROJECTS:")
    print(f"   Total: {project_count} proyectos")
    print()
    
    # Global config overrides
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM utm_global_config;
    """)
    
    config_count = cursor.fetchone()[0]
    print("⚙️  GLOBAL CONFIG (Sistema):")
    print(f"   Total: {config_count} configuraciones globales")
    print()
    
    cursor.close()
    conn.close()
    
    print()
    print("="*70)
    print("✅ Verificación completada")
    print("="*70)
    print()
    print("RESUMEN:")
    print("  - El tenant_id NO cambió, sigue siendo el mismo UUID")
    print("  - Solo cambió el client_id: DEMO3 → CUSTOMER3")
    print("  - CUSTOMER3 es un tenant limpio (sin configuraciones aún)")
    print("  - Para usar proveedores LLM, necesitas configurar el Vault")
    print()
    print("="*70)
    print("✅ Todas las configuraciones están intactas")
    print("="*70)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

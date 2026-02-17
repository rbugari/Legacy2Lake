#!/usr/bin/env python3
"""
Extrae configuraciones de DEMO1, DEMO2, DEMO3 de PRODUCCIÓN
"""
import psycopg2
from typing import Dict, List

# Credenciales de PRODUCCIÓN
PROD_CONN_STRING = "postgresql://postgres:2321!!A@db.wdmlnvppkhjjeuiutnjl.supabase.co:5432/postgres"

def get_tenant_configs(tenant_client_ids: List[str]) -> Dict:
    """Extrae todas las configuraciones de los tenants especificados"""
    
    conn = psycopg2.connect(PROD_CONN_STRING)
    cursor = conn.cursor()
    
    configs = {}
    
    for client_id in tenant_client_ids:
        print(f"\n{'='*70}")
        print(f"EXTRAYENDO: {client_id}")
        print('='*70)
        
        # Obtener tenant_id
        cursor.execute("""
            SELECT tenant_id, client_id, org_name, tier
            FROM utm_tenants
            WHERE client_id = %s;
        """, (client_id,))
        
        tenant = cursor.fetchone()
        if not tenant:
            print(f"❌ {client_id} no encontrado en producción")
            continue
        
        tenant_id, client_id, org_name, tier = tenant
        print(f"✅ Tenant encontrado: {tenant_id}")
        print(f"   Org: {org_name}")
        print(f"   Tier: {tier}")
        
        configs[client_id] = {
            'tenant_id': str(tenant_id),
            'org_name': org_name,
            'tier': tier,
            'vault': [],
            'provider_vault': [],
            'projects_count': 0
        }
        
        # VAULT - Provider Credentials
        cursor.execute("""
            SELECT provider, api_key_encrypted, base_url_encrypted, metadata, is_active
            FROM utm_vault
            WHERE tenant_id = %s;
        """, (tenant_id,))
        
        vault_entries = cursor.fetchall()
        print(f"\n📦 VAULT: {len(vault_entries)} entradas")
        for provider, api_key_enc, base_url_enc, metadata, is_active in vault_entries:
            print(f"   {'✅' if is_active else '❌'} {provider}")
            configs[client_id]['vault'].append({
                'provider': provider,
                'api_key_encrypted': api_key_enc,
                'base_url_encrypted': base_url_enc,
                'metadata': metadata,
                'is_active': is_active
            })
        
        # PROVIDER VAULT
        cursor.execute("""
            SELECT provider_name, api_key, base_url, model_name, is_active
            FROM utm_provider_vault
            WHERE tenant_id = %s;
        """, (tenant_id,))
        
        provider_entries = cursor.fetchall()
        print(f"\n🔧 PROVIDER VAULT: {len(provider_entries)} entradas")
        for prov_name, api_key, base_url, model_name, is_active in provider_entries:
            print(f"   {'✅' if is_active else '❌'} {prov_name} - {model_name}")
            configs[client_id]['provider_vault'].append({
                'provider_name': prov_name,
                'api_key': api_key,
                'base_url': base_url,
                'model_name': model_name,
                'is_active': is_active
            })
        
        # Projects count
        cursor.execute("""
            SELECT COUNT(*) FROM utm_projects WHERE tenant_id = %s;
        """, (tenant_id,))
        
        project_count = cursor.fetchone()[0]
        configs[client_id]['projects_count'] = project_count
        print(f"\n📁 PROJECTS: {project_count} proyectos")
    
    cursor.close()
    conn.close()
    
    return configs

def main():
    print("="*70)
    print("EXTRACCIÓN DE CONFIGURACIONES - PRODUCCIÓN")
    print("="*70)
    
    # Tenants a extraer
    tenant_ids = ['DEMO1', 'DEMO2', 'DEMO3']
    
    try:
        configs = get_tenant_configs(tenant_ids)
        
        print("\n\n" + "="*70)
        print("RESUMEN DE CONFIGURACIONES EXTRAÍDAS")
        print("="*70)
        
        for client_id, config in configs.items():
            print(f"\n{client_id}:")
            print(f"  Vault entries: {len(config['vault'])}")
            print(f"  Provider vault: {len(config['provider_vault'])}")
            print(f"  Projects: {config['projects_count']}")
        
        # Guardar en archivo JSON para importar después
        import json
        output_file = "prod_configs_export.json"
        with open(output_file, 'w') as f:
            json.dump(configs, f, indent=2, default=str)
        
        print(f"\n✅ Configuraciones guardadas en: {output_file}")
        print("\nPara importar a DEV, ejecuta: python import_prod_configs.py")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

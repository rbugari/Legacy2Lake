"""Quick check of demo3 Azure configuration"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

tid = 'daac0ee6-3b28-412d-8acd-43ec51149188'

print("="*80)
print("🔍 DEMO3 TENANT - Azure Configuration Check")
print("="*80)

# Providers
vault = client.table('utm_provider_vault').select('provider_name, is_active, base_url').eq('tenant_id', tid).execute()
print(f"\n✅ PROVIDERS ({len(vault.data)})")
for p in vault.data:
    status = "✅ ACTIVE  " if p.get('is_active') else "❌ INACTIVE"
    print(f"   {status} {p.get('provider_name')}")
    if p.get('base_url'):
        print(f"              URL: {p.get('base_url')}")

# Models
models = client.table('utm_model_catalog').select('model_id, provider, deployment_id, api_version, is_active').eq('tenant_id', tid).execute()
active = [m for m in models.data if m.get('is_active')]
print(f"\n✅ MODELS ({len(active)} active / {len(models.data)} total)")
for m in active:
    print(f"   📦 {m.get('model_id')} ({m.get('provider')})")
    if m.get('deployment_id'):
        print(f"      Deployment: {m.get('deployment_id')}")
    if m.get('api_version'):
        print(f"      API Version: {m.get('api_version')}")

# Agent Matrix
matrix = client.table('utm_agent_matrix').select('agent_id, model_id, provider, is_active').eq('tenant_id', tid).execute()
active_agents = [a for a in matrix.data if a.get('is_active')]
print(f"\n✅ AGENT MATRIX ({len(active_agents)} active / {len(matrix.data)} total)")
for a in active_agents:
    print(f"   🤖 {a.get('agent_id')} → {a.get('model_id')} ({a.get('provider')})")

# Projects
projects = client.table('utm_projects').select('name, stage, status, settings').eq('tenant_id', tid).execute()
print(f"\n✅ PROJECTS ({len(projects.data)})")
for p in projects.data:
    print(f"   📁 {p.get('name')} - Stage: {p.get('stage')} - Status: {p.get('status')}")
    if p.get('settings'):
        s = p.get('settings')
        if isinstance(s, dict):
            print(f"      Source: {s.get('source_tech', 'N/A')} → Target: {s.get('target_tech', 'N/A')}")

print("\n" + "="*80)
print("📊 SUMMARY FOR AGENT C TESTING")
print("="*80)

checks = {
    "Azure Provider Vault": len([p for p in vault.data if 'azure' in p.get('provider_name', '').lower() and p.get('is_active')]),
    "Azure Models Active": len([m for m in active if m.get('provider') == 'azure']),
    "Agent Matrix Configured": len(active_agents),
    "Projects Available": len(projects.data)
}

for check, count in checks.items():
    status = "✅" if count > 0 else "❌"
    print(f"{status} {check}: {count}")

if all(v > 0 for v in checks.values()):
    print("\n🎉 CONFIGURACIÓN COMPLETA - Listo para Agent C testing!")
    print("\nUsa el proyecto 'ttt' para testear:")
    print("   Source: Microsoft SQL Server (SSIS)")
    print("   Target: Databricks (PySpark)")
    print("   Cartridge a testear: pyspark/bronze_layer.md, pyspark/silver_layer.md, pyspark/gold_layer.md")
else:
    print("\n⚠️  CONFIGURACIÓN INCOMPLETA - Faltan componentes")

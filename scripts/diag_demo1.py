"""Diagnóstico del estado de demo1 en DB."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from apps.api.services.persistence_service import SupabasePersistence

db = SupabasePersistence(tenant_id='daac0ee6-3b28-412d-8acd-43ec51149188')
pid = '1051e4b0-570d-443a-9412-0430a6ac3040'
tid = 'daac0ee6-3b28-412d-8acd-43ec51149188'

r = db.client.table('utm_objects').select('source_name,source_query,data_flow_analysis,criticality,is_pii,metadata').eq('project_id', pid).eq('tenant_id', tid).execute()
print(f'utm_objects: {len(r.data)} rows')
for row in r.data:
    sq = row.get('source_query') or ''
    dfa = row.get('data_flow_analysis') or {}
    meta = row.get('metadata') or {}
    has_medulla = bool(meta.get('logical_medulla'))
    print(f'  {row["source_name"]}: sq={len(sq)}chars  dfa={str(dfa)[:50]}  medulla={has_medulla}  crit={row.get("criticality")}  pii={row.get("is_pii")}')

t = db.client.table('utm_table_impacts').select('table_name,operation').eq('project_id', pid).eq('tenant_id', tid).execute()
print(f'\nutm_table_impacts: {len(t.data)} rows')
for row in t.data[:5]:
    print(f'  {row.get("table_name")} | {row.get("operation")}')

c = db.client.table('utm_asset_columns').select('column_name,is_pii,data_type').eq('project_id', pid).execute()
print(f'\nutm_asset_columns: {len(c.data)} rows')
for row in c.data[:5]:
    print(f'  {row.get("column_name")} | {row.get("data_type")} | pii={row.get("is_pii")}')

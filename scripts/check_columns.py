import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from apps.api.services.persistence_service import SupabasePersistence

db = SupabasePersistence(tenant_id='daac0ee6-3b28-412d-8acd-43ec51149188')
pid = '1051e4b0-570d-443a-9412-0430a6ac3040'

c = db.client.table('utm_asset_columns').select('column_name,data_type,is_pii').eq('project_id', pid).execute()
rows = c.data or []
print(f"utm_asset_columns: {len(rows)} rows\n")
for row in sorted(rows, key=lambda x: x['column_name']):
    print(f"  {row['column_name']:35} {row['data_type']:10} pii={row.get('is_pii', False)}")

# Also check column_mappings for FactSales
r = db.client.table('utm_objects').select('object_id,source_name').eq('source_name', 'FactSales.dtsx').eq('project_id', pid).execute()
if r.data:
    aid = r.data[0]['object_id']
    cm = db.client.table('utm_column_mappings').select('source_column,target_column,source_datatype').eq('asset_id', aid).execute()
    print(f"\nFactSales utm_column_mappings ({len(cm.data or [])} rows):")
    for row in (cm.data or []):
        print(f"  {row['source_column']:30} {row.get('source_datatype')}")

"""
Limpia utm_column_mappings y utm_asset_columns para demo1
y re-ejecuta el proceso de column profiling desde triage.
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.api.services.persistence_service import SupabasePersistence
from apps.api.services.column_profiling_service import ColumnProfilingService

TENANT_ID  = "daac0ee6-3b28-412d-8acd-43ec51149188"
PROJECT_ID = "1051e4b0-570d-443a-9412-0430a6ac3040"


async def main():
    db = SupabasePersistence(tenant_id=TENANT_ID)

    # 1. Get all asset_ids for this project
    res = db.client.table("utm_objects").select("object_id,source_name").eq("project_id", PROJECT_ID).eq("tenant_id", TENANT_ID).execute()
    assets = res.data or []
    print(f"Found {len(assets)} assets in utm_objects")
    asset_ids = [a["object_id"] for a in assets]

    # 2. Delete utm_asset_columns for this project
    del_ac = db.client.table("utm_asset_columns").delete().eq("project_id", PROJECT_ID).execute()
    print(f"Deleted utm_asset_columns rows: {len(del_ac.data or [])}")

    # 3. Delete utm_column_mappings for these assets (no project_id column on that table)
    if asset_ids:
        del_cm = db.client.table("utm_column_mappings").delete().in_("asset_id", asset_ids).execute()
        print(f"Deleted utm_column_mappings rows: {len(del_cm.data or [])}")

    # 4. Re-run _persist_column_mappings via triage helper
    from apps.api.routers.triage import _persist_column_mappings as pcm

    total_mappings = 0
    for asset in assets:
        asset_id = asset["object_id"]
        name = asset["source_name"]

        # Fetch medulla from utm_objects.metadata
        r = db.client.table("utm_objects").select("metadata").eq("object_id", asset_id).limit(1).execute()
        row = (r.data or [{}])[0]
        meta = row.get("metadata") or {}
        medulla = meta.get("logical_medulla") or {}

        if not medulla:
            print(f"  {name}: no medulla — skipping")
            continue

        n = await pcm(asset_id=asset_id, medulla=medulla, db=db)
        print(f"  {name}: {n} column mappings written")
        total_mappings += n

    print(f"\nTotal column mappings written: {total_mappings}")

    # 5. Re-run column profiling
    profiler = ColumnProfilingService(tenant_id=TENANT_ID, client_id=None)
    result = await profiler.profile_from_mappings(project_id=PROJECT_ID, force_refresh=True)
    print(f"\nColumn profiling result: {result}")

    # 6. Verify
    c = db.client.table("utm_asset_columns").select("column_name,data_type,is_pii").eq("project_id", PROJECT_ID).execute()
    rows = c.data or []
    print(f"\nutm_asset_columns: {len(rows)} rows")
    by_type = {}
    for row in rows:
        dt = row.get("data_type") or "NULL"
        by_type[dt] = by_type.get(dt, 0) + 1
    print(f"  Types distribution: {by_type}")
    date_cols = [r["column_name"] for r in rows if (r.get("data_type") or "").upper() == "DATE"]
    print(f"  DATE columns ({len(date_cols)}): {date_cols[:10]}")
    pii_cols = [r["column_name"] for r in rows if r.get("is_pii")]
    print(f"  PII columns ({len(pii_cols)}): {pii_cols[:10]}")


asyncio.run(main())

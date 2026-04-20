"""
sync_dev_to_prod.py  –  v4.5
Sincroniza configuración y tenants de DEV → PROD.

SCOPE:
  ✅ Copiado: tenants, usuarios/profiles, prompts, provider vault, model catalog,
              agent matrix, cartridges, configuración global, parser catalogs,
              quality rules, source tech catalog, workflow states
  ❌ EXCLUIDO: utm_projects y todas las tablas hijas (datos de proyectos,
               assets, columns, chat history, traceability, audit logs, validations, etc.)

COMPORTAMIENTO:
  - Borra primero los datos de PROD en cada tabla (DELETE sin filtros)
  - Luego upsert desde DEV en lotes de 100
  - Orden de tablas respeta foreign keys (padres antes que hijos)

USO:
  python scripts/sync_dev_to_prod.py
  python scripts/sync_dev_to_prod.py --dry-run      (solo muestra conteos, no escribe)
  python scripts/sync_dev_to_prod.py --tables utm_prompts,utm_provider_vault
"""
import sys
import argparse
from supabase import create_client

# ─── Credenciales ────────────────────────────────────────────────────────────
DEV_URL  = "https://qdsdfityyxmalyipqbfm.supabase.co"
DEV_KEY  = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFkc2RmaXR5eXhtYWx5aXBxYmZtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODg2NTczOSwiZXhwIjoyMDg0NDQxNzM5fQ.f4Ge4MPpeDoFLgLSD9e79V2N-ND-aU9YqwNp2VrOgC0"

PROD_URL = "https://wdmlnvppkhjjeuiutnjl.supabase.co"
PROD_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndkbWxudnBwa2hqamV1aXV0bmpsIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDA4MjM2NiwiZXhwIjoyMDg1NjU4MzY2fQ.ptqq5JugnDa2FcuTeSl28PfbfKfW5Qz4tDuMggH9eeg"

# ─── Tablas a sincronizar (en orden de dependencia) ──────────────────────────
# Formato: (tabla, primary_key_column)
TABLES_TO_SYNC = [
    # Tenants – padre de todo lo demás
    ("utm_tenants",           "tenant_id"),

    # Usuarios / profiles (Supabase auth.users no se toca, solo la tabla de perfiles)
    ("utm_user_profiles",     "id"),
    ("utm_client_profiles",   "id"),
    ("utm_project_members",   "id"),   # si existe

    # Configuración global
    ("utm_global_config",     "id"),

    # Prompts del sistema (Level 1 y Level 2)
    ("utm_prompts",           "prompt_id"),
    ("utm_system_prompts",    "id"),   # si existe

    # Provider vault y modelos
    ("utm_provider_vault",    "id"),
    ("utm_model_catalog",     "model_id"),
    ("utm_agent_matrix",      "id"),

    # Cartridges del sistema
    ("utm_system_cartridges", "id"),

    # Catálogos de parsers y tecnologías fuente
    ("utm_source_tech_catalog", "id"),
    ("utm_parser_catalog",    "id"),

    # Reglas de calidad
    ("utm_quality_rules",     "id"),

    # Workflow states (configuración, no datos de proyecto)
    ("utm_workflow_states",   "id"),
]

# Tablas que NUNCA se deben sincronizar (contienen datos de proyectos)
EXCLUDED_TABLES = {
    "utm_projects",
    "utm_objects",
    "utm_asset_columns",
    "utm_table_impacts",
    "utm_code_validations",
    "utm_schema_versions",
    "utm_execution_logs",
    "utm_file_inventory",
    "utm_audit_log",
    "utm_gaps",
    "utm_gap_comments",
    "utm_project_chat_threads",
    "utm_project_chat_messages",
    "utm_asset_traceability",
    "utm_data_quality_reports",
    "utm_quality_metrics",
    "utm_quality_anomalies",
    "utm_knowledge_snapshots",
    "utm_evidence_items",
    "utm_solutions",
    "utm_processes",
    "utm_orchestration_steps",
    "utm_operational_constraints",
    "utm_rule_signals",
}

BATCH_SIZE = 100


def fetch_all(client, table: str) -> list:
    """Paginación completa desde la tabla fuente."""
    rows = []
    offset = 0
    while True:
        res = client.table(table).select("*").range(offset, offset + BATCH_SIZE - 1).execute()
        batch = res.data or []
        rows.extend(batch)
        if len(batch) < BATCH_SIZE:
            break
        offset += BATCH_SIZE
    return rows


def delete_all(client, table: str, pk: str, dry_run: bool) -> int:
    """Borra todos los registros de la tabla en PROD."""
    if dry_run:
        return 0
    try:
        res = client.table(table).delete().neq(pk, "00000000-0000-0000-0000-000000000000").execute()
        return len(res.data or [])
    except Exception as e:
        # Intentar con string vacío como fallback
        try:
            res = client.table(table).delete().neq(pk, "").execute()
            return len(res.data or [])
        except Exception as e2:
            print(f"    ⚠️  delete error: {e2}")
            return 0


def upsert_batch(client, table: str, rows: list, pk: str, dry_run: bool) -> tuple[int, int]:
    """Upsert en lotes. Devuelve (ok, errors)."""
    if dry_run or not rows:
        return len(rows), 0
    ok = errors = 0
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        try:
            client.table(table).upsert(batch, on_conflict=pk).execute()
            ok += len(batch)
        except Exception as e:
            print(f"    ⚠️  upsert error batch {i//BATCH_SIZE}: {e}")
            errors += len(batch)
    return ok, errors


def sync_table(dev, prod, table: str, pk: str, dry_run: bool):
    if table in EXCLUDED_TABLES:
        print(f"  ⛔ SKIPPED (excluded): {table}")
        return

    print(f"  → {table} ...", end=" ", flush=True)
    try:
        rows = fetch_all(dev, table)
    except Exception as e:
        print(f"SKIP (read error: {e})")
        return

    if not rows:
        print("0 rows in DEV — skipping")
        return

    tag = "[DRY-RUN] " if dry_run else ""
    deleted = delete_all(prod, table, pk, dry_run)
    ok, errors = upsert_batch(prod, table, rows, pk, dry_run)
    print(f"{tag}{len(rows)} rows → {ok} upserted, {errors} errors")


def main():
    parser = argparse.ArgumentParser(description="Sync DEV → PROD (config + tenants only)")
    parser.add_argument("--dry-run", action="store_true", help="Mostrar conteos sin escribir en PROD")
    parser.add_argument("--tables", type=str, default="", help="Comma-separated lista de tablas a sincronizar (override)")
    args = parser.parse_args()

    print("=" * 60)
    print("Legacy2Lake — DEV → PROD config sync")
    print(f"DEV:  {DEV_URL}")
    print(f"PROD: {PROD_URL}")
    if args.dry_run:
        print("MODE: DRY-RUN (no changes will be written to PROD)")
    else:
        print("MODE: LIVE — PROD data will be DELETED and replaced")
        confirm = input("\n¿Confirmar? Escribe 'si' para continuar: ").strip().lower()
        if confirm not in ("si", "sí", "yes", "y"):
            print("Cancelado.")
            sys.exit(0)
    print("=" * 60)

    dev  = create_client(DEV_URL,  DEV_KEY)
    prod = create_client(PROD_URL, PROD_KEY)

    tables = TABLES_TO_SYNC
    if args.tables:
        pk_map = {t: pk for t, pk in TABLES_TO_SYNC}
        override = [(t.strip(), pk_map.get(t.strip(), "id")) for t in args.tables.split(",") if t.strip()]
        tables = override
        print(f"Override tables: {[(t, pk) for t,pk in tables]}\n")

    for table, pk in tables:
        sync_table(dev, prod, table, pk, args.dry_run)

    print("\n✅ Sync complete.")


if __name__ == "__main__":
    main()

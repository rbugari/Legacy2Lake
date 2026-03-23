import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from apps.api.prompts.catalog import get_canonical_prompt_specs


def get_supabase_client():
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("Missing Supabase credentials in .env")
        sys.exit(1)
    return create_client(url, key)


def get_active_prompt_rows(client):
    response = (
        client.table("utm_prompts")
        .select("prompt_id, metadata")
        .eq("is_active", True)
        .order("prompt_id")
        .execute()
    )
    return response.data or []


def main():
    parser = argparse.ArgumentParser(
        description="Deprecate active DB prompts that are outside the canonical prompt catalog."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply the deprecation in Supabase. Without this flag the script runs in dry-run mode.",
    )
    args = parser.parse_args()

    client = get_supabase_client()
    canonical_ids = {spec.prompt_id for spec in get_canonical_prompt_specs()}
    active_rows = get_active_prompt_rows(client)

    legacy_rows = [row for row in active_rows if row["prompt_id"] not in canonical_ids]

    if not legacy_rows:
        print("No active legacy prompts found.")
        return

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"Legacy prompt deprecation mode: {mode}")
    print(f"Legacy prompts found: {len(legacy_rows)}")

    for row in legacy_rows:
        print(f"  - {row['prompt_id']}")

    if not args.apply:
        print()
        print("Dry-run only. Re-run with --apply to deactivate these prompts.")
        return

    timestamp = datetime.now(timezone.utc).isoformat()
    for row in legacy_rows:
        metadata = row.get("metadata") or {}
        metadata.update(
            {
                "deprecated_at": timestamp,
                "deprecated_by": "scripts/deprecate_legacy_prompts.py",
                "deprecation_reason": "Outside canonical prompt catalog",
            }
        )

        (
            client.table("utm_prompts")
            .update({"is_active": False, "metadata": metadata})
            .eq("prompt_id", row["prompt_id"])
            .execute()
        )

    print()
    print(f"Deprecated {len(legacy_rows)} prompts.")


if __name__ == "__main__":
    main()

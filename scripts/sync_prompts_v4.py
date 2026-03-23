import sys
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client
import os


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


def main():
    print("=" * 80)
    print("UTM V4.0 - CANONICAL PROMPT SYNCHRONIZATION")
    print("=" * 80)

    client = get_supabase_client()
    specs = get_canonical_prompt_specs()

    print(f"Canonical prompt count: {len(specs)}")

    upserted_count = 0
    error_count = 0

    for spec in specs:
        try:
            data = spec.to_db_record()

            existing = (
                client.table("utm_prompts")
                .select("prompt_id")
                .eq("prompt_id", spec.prompt_id)
                .execute()
            )

            if existing.data:
                client.table("utm_prompts").update(data).eq("prompt_id", spec.prompt_id).execute()
                status = "UPDATED"
            else:
                client.table("utm_prompts").insert(data).execute()
                status = "INSERTED"

            print(f"[OK] {status}: {spec.prompt_id} ({spec.category})")
            upserted_count += 1

        except Exception as exc:
            print(f"[ERROR] {spec.prompt_id}: {exc}")
            error_count += 1

    print("=" * 80)
    print("SYNCHRONIZATION SUMMARY")
    print("=" * 80)
    print(f"Successfully upserted: {upserted_count}")
    print(f"Failed:                {error_count}")

    if error_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()

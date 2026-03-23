import sys
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client
import os
import hashlib


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


def get_db_prompts(client):
    response = (
        client.table("utm_prompts")
        .select("prompt_id, content, agent_id, tech_stack, pattern_type, metadata")
        .eq("is_active", True)
        .execute()
    )
    return {p["prompt_id"]: p for p in response.data}


def main():
    print("=" * 80)
    print("UTM V4.0 - CANONICAL PROMPT VALIDATION")
    print("=" * 80)

    client = get_supabase_client()
    db_prompts = get_db_prompts(client)
    expected_specs = get_canonical_prompt_specs()
    expected_ids = {spec.prompt_id for spec in expected_specs}
    db_ids = set(db_prompts)

    missing = sorted(expected_ids - db_ids)
    extra = sorted(db_ids - expected_ids)
    drift = []

    spec_by_id = {spec.prompt_id: spec for spec in expected_specs}
    for prompt_id in sorted(expected_ids & db_ids):
        spec = spec_by_id[prompt_id]
        db_row = db_prompts[prompt_id]
        disk_hash = hashlib.sha256(spec.read_text().encode("utf-8")).hexdigest()
        db_hash = hashlib.sha256((db_row.get("content") or "").encode("utf-8")).hexdigest()

        if disk_hash != db_hash:
            drift.append(f"{prompt_id} [content]")
            continue

        if (db_row.get("agent_id") or None) != spec.agent_id:
            drift.append(f"{prompt_id} [agent_id]")
            continue

        if (db_row.get("tech_stack") or None) != spec.tech_stack:
            drift.append(f"{prompt_id} [tech_stack]")
            continue

        if (db_row.get("pattern_type") or None) != spec.pattern_type:
            drift.append(f"{prompt_id} [pattern_type]")
            continue

    print(f"Canonical prompts expected: {len(expected_ids)}")
    print(f"Active prompts in DB:       {len(db_ids)}")
    print()

    if missing:
        print("Missing from DB:")
        for prompt_id in missing:
            print(f"  - {prompt_id}")
        print()

    if extra:
        print("Extra active prompts in DB (legacy or drift):")
        for prompt_id in extra:
            print(f"  - {prompt_id}")
        print()

    if drift:
        print("Canonical prompts with drift (content or metadata mismatch):")
        for item in drift:
            print(f"  - {item}")
        print()

    if missing or extra or drift:
        print("VALIDATION FAILED")
        print("Run `python scripts/sync_prompts_v4.py` and review legacy prompts before cleanup.")
        sys.exit(1)

    print("VALIDATION PASSED: DB matches canonical prompt catalog.")


if __name__ == "__main__":
    main()

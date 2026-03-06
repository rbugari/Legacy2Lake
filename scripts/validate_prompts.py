import os
import sys
from dotenv import load_dotenv
from supabase import create_client

def get_supabase_client():
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("❌ Missing Supabase credentials in .env")
        sys.exit(1)
    return create_client(url, key)

EXPECTED_TECHS = [
    "aws",
    "generic",
    "dbt",
    "gcp",
    "ms_fabric",
    "ms_fabric_sql",
    "pyspark",
    "salesforce",
    "snowflake",
    "snowflake_sql"
]

EXPECTED_LAYERS = ["bronze", "silver", "gold", "direct"]

def get_db_prompts(client):
    try:
        response = client.table("utm_prompts").select("prompt_id").execute()
        return [p["prompt_id"] for p in response.data]
    except Exception as e:
        print(f"❌ Error fetching from Supabase: {e}")
        sys.exit(1)

def main():
    print("="*80)
    print("🛡️  UTM V4.0 - PROMPT MATRIX VALIDATION")
    print("="*80)
    
    client = get_supabase_client()
    db_prompts = get_db_prompts(client)
    
    print(f"📦 Total Prompts in Database: {len(db_prompts)}\n")
    
    # Print Header
    header = f"{'TECH / LAYER':<15} | " + " | ".join(f"{layer:^8}" for layer in EXPECTED_LAYERS)
    print(header)
    print("-" * len(header))
    
    missing_count = 0
    
    for tech in EXPECTED_TECHS:
        row = f"{tech:<15} | "
        
        for layer in EXPECTED_LAYERS:
            # Recreate prompt_id matching sync_prompts_v4.py logic
            # E.g. agent_c_bronze_ms_fabric, or agent_c_direct_dbt
            expected_id = f"agent_c_{layer}_{tech}"
            
            if expected_id in db_prompts:
                row += f"{'✅':^9}| "
            else:
                row += f"{'❌':^9}| "
                missing_count += 1
                
        print(row)
        
    print("-" * len(header))
    
    if missing_count > 0:
        print(f"\n❌ VALIDATION FAILED: {missing_count} required prompt combinations are missing.")
        print("Run `python scripts/sync_prompts_v4.py` to seed them.")
        sys.exit(1)
    else:
        print("\n✅ VALIDATION PASSED: All prompt combinations exist in the database.")
        sys.exit(0)

if __name__ == "__main__":
    main()

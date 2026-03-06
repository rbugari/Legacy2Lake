import os
import sys
from pathlib import Path
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

# Map folder names to tech_stack identifiers in the DB
TECH_STACK_MAP = {
    "aws": "aws",
    "base": "generic",
    "dbt": "dbt",
    "gcp": "gcp",
    "ms_fabric": "ms_fabric",
    "ms_fabric_sql": "ms_fabric_sql",
    "pyspark": "pyspark",
    "sf": "salesforce",
    "snowflake": "snowflake",
    "snowflake_sql": "snowflake_sql"
}

# Map filename to pattern_type
PATTERN_TYPE_MAP = {
    "bronze_layer.md": "bronze",
    "silver_layer.md": "silver",
    "gold_layer.md": "gold",
    "direct_layer.md": "direct"
}

def main():
    print("="*80)
    print("🚀 UTM V4.0 - PROMPT SYNCHRONIZATION")
    print("="*80)
    
    client = get_supabase_client()
    base_dir = Path("prompt_lab/cartridges").resolve()
    
    if not base_dir.exists():
        print(f"❌ Directory not found: {base_dir}")
        sys.exit(1)

    print(f"📁 Scanning: {base_dir}")
    
    upserted_count = 0
    error_count = 0
    skipped_count = 0
    
    # Iterate through all tech folders
    for tech_folder in base_dir.iterdir():
        if not tech_folder.is_dir():
            continue
            
        tech_name = tech_folder.name
        tech_stack = TECH_STACK_MAP.get(tech_name, tech_name)
        
        # Iterate through layer markdown files
        for md_file in tech_folder.glob("*.md"):
            if md_file.name == "README.md":
                continue
                
            pattern_type = PATTERN_TYPE_MAP.get(md_file.name)
            if not pattern_type:
                print(f"⚠️  Skipping unknown file format: {md_file.name}")
                skipped_count += 1
                continue
                
            prompt_id = f"agent_c_{pattern_type}_{tech_stack}"
            
            try:
                content = md_file.read_text(encoding="utf-8")
                
                # V4.0 Schema matches utm_prompts columns strictly
                data = {
                    "prompt_id": prompt_id,
                    "content": content,
                    "tech_stack": tech_stack,
                    "pattern_type": pattern_type,
                    "agent_id": "agent-c",
                    "is_active": True,
                    "metadata": {"source": f"cartridges/{tech_name}/{md_file.name}"}
                }
                
                # Check if exists
                existing = client.table("utm_prompts").select("prompt_id").eq("prompt_id", prompt_id).execute()
                
                if len(existing.data) > 0:
                    client.table("utm_prompts").update(data).eq("prompt_id", prompt_id).execute()
                    status = "🔄 UPDATED"
                else:
                    client.table("utm_prompts").insert(data).execute()
                    status = "🆕 INSERTED"
                    
                print(f"✅ {status}: {prompt_id}")
                upserted_count += 1
                
            except Exception as e:
                print(f"❌ ERROR processing {prompt_id}: {e}")
                error_count += 1

    print("="*80)
    print("📊 SYNCHRONIZATION SUMMARY")
    print("="*80)
    print(f"✅ Successfully Upserted: {upserted_count}")
    print(f"⚠️  Skipped files:         {skipped_count}")
    print(f"❌ Failed:                {error_count}")
    
    if error_count > 0:
        sys.exit(1)
    
if __name__ == "__main__":
    main()

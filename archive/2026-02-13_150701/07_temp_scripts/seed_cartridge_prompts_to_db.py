"""
Sprint 1 - Cartridge Prompt Database Seeding Script
====================================================
Migrates all cartridge prompts from prompt_lab/cartridges filesystem to utm_prompts table.

Naming Convention:
  cartridge_{tech}_{layer}
  
Examples:
  - cartridge_pyspark_bronze
  - cartridge_pyspark_silver
  - cartridge_pyspark_gold
  - cartridge_snowflake_bronze
  - cartridge_dbt_bronze
  - cartridge_gcp_bronze
  - etc.

Features:
  - Auto-discovers all .md files in prompt_lab/cartridges/
  - Creates v1 entries in utm_prompts
  - Marks as active and global (tenant_id=NULL)
  - Skips if already exists (no overwrite)
  - Reports summary statistics
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
client = create_client(url, key)

# Cartridge directory
CARTRIDGES_DIR = Path("prompt_lab/cartridges")

# Tech folder mapping (filesystem → tech_id)
TECH_MAPPING = {
    "pyspark": "pyspark",
    "snowflake": "snowflake",
    "ms_fabric": "fabric",
    "aws": "aws",
    "base": "generic",
    "dbt": "dbt",
    "gcp": "gcp",
    "sf": "salesforce"
}

# Layer file mapping (filename → layer)
LAYER_MAPPING = {
    "bronze_layer.md": "bronze",
    "silver_layer.md": "silver",
    "gold_layer.md": "gold",
    "direct_layer.md": "direct"
}

def discover_cartridge_prompts():
    """Discover all cartridge prompt files in prompt_lab/cartridges/"""
    prompts = []
    
    for tech_folder in CARTRIDGES_DIR.iterdir():
        if not tech_folder.is_dir():
            continue
            
        tech_name = tech_folder.name
        tech_id = TECH_MAPPING.get(tech_name, tech_name)
        
        for md_file in tech_folder.glob("*.md"):
            if md_file.name == "README.md":
                continue
                
            layer = LAYER_MAPPING.get(md_file.name)
            if not layer:
                print(f"⚠️  Skipping unknown file: {md_file}")
                continue
            
            prompt_id = f"cartridge_{tech_id}_{layer}"
            
            prompts.append({
                "tech_id": tech_id,
                "layer": layer,
                "prompt_id": prompt_id,
                "file_path": md_file,
                "folder": tech_name
            })
    
    return prompts

def read_prompt_content(file_path):
    """Read prompt file content"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return None

def check_prompt_exists(prompt_id):
    """Check if prompt already exists in DB"""
    try:
        result = client.table("utm_prompts") \
            .select("id, version_number") \
            .eq("prompt_id", prompt_id) \
            .is_("tenant_id", "null") \
            .execute()
        return len(result.data) > 0
    except Exception as e:
        print(f"❌ Error checking existence for {prompt_id}: {e}")
        return False

def insert_prompt(prompt_data):
    """Insert prompt into utm_prompts table"""
    data = {
        "tenant_id": None,  # Global prompt
        "prompt_id": prompt_data["prompt_id"],
        "version_number": 1,
        "version": "1.0",
        "content": prompt_data["content"],
        "is_active": True,
        "changelog": f"Initial seed from filesystem: {prompt_data['file_path']}",
        "metadata": {
            "tech_id": prompt_data["tech_id"],
            "layer": prompt_data["layer"],
            "source_folder": prompt_data["folder"],
            "seeded_from": str(prompt_data["file_path"]),
            "seed_version": "sprint_1_migration"
        }
    }
    
    try:
        client.table("utm_prompts").insert(data).execute()
        return True
    except Exception as e:
        print(f"❌ Error inserting {prompt_data['prompt_id']}: {e}")
        return False

def main():
    print("="*80)
    print("🚀 SPRINT 1 - CARTRIDGE PROMPT DATABASE MIGRATION")
    print("="*80)
    print(f"\n📁 Source: {CARTRIDGES_DIR.absolute()}")
    print(f"🎯 Target: utm_prompts table (Supabase)")
    print(f"🌍 Scope: Global prompts (tenant_id=NULL)")
    
    # Discover all cartridge prompts
    print(f"\n{'='*80}")
    print("🔍 Phase 1: Discovery")
    print(f"{'='*80}")
    
    prompts = discover_cartridge_prompts()
    print(f"\n✅ Discovered {len(prompts)} cartridge prompt files")
    
    # Group by tech
    by_tech = {}
    for p in prompts:
        tech = p["tech_id"]
        if tech not in by_tech:
            by_tech[tech] = []
        by_tech[tech].append(p)
    
    print(f"\n📊 Breakdown by technology:")
    for tech, items in sorted(by_tech.items()):
        print(f"  {tech:15} {len(items)} prompts")
    
    # Read file contents
    print(f"\n{'='*80}")
    print("📖 Phase 2: Reading File Contents")
    print(f"{'='*80}")
    
    for prompt in prompts:
        content = read_prompt_content(prompt["file_path"])
        if content:
            prompt["content"] = content
            chars = len(content)
            lines = content.count('\n') + 1
            print(f"✅ {prompt['prompt_id']:40} {lines:4} lines, {chars:6} chars")
        else:
            prompt["content"] = None
            print(f"❌ {prompt['prompt_id']:40} FAILED TO READ")
    
    # Filter out failed reads
    valid_prompts = [p for p in prompts if p["content"]]
    print(f"\n📊 Successfully read {len(valid_prompts)}/{len(prompts)} files")
    
    # Check existing prompts
    print(f"\n{'='*80}")
    print("🔎 Phase 3: Checking Existing Database Entries")
    print(f"{'='*80}")
    
    existing_count = 0
    new_count = 0
    
    for prompt in valid_prompts:
        exists = check_prompt_exists(prompt["prompt_id"])
        prompt["exists"] = exists
        if exists:
            existing_count += 1
            print(f"⏭️  {prompt['prompt_id']:40} EXISTS (skipping)")
        else:
            new_count += 1
            print(f"🆕 {prompt['prompt_id']:40} NEW")
    
    print(f"\n📊 Status:")
    print(f"  ✅ Existing: {existing_count}")
    print(f"  🆕 New:      {new_count}")
    
    if new_count == 0:
        print(f"\n✨ All cartridge prompts already exist in database!")
        print(f"   No migration needed.")
        return
    
    # Insert new prompts
    print(f"\n{'='*80}")
    print("💾 Phase 4: Inserting New Prompts")
    print(f"{'='*80}")
    
    success_count = 0
    fail_count = 0
    
    for prompt in valid_prompts:
        if prompt["exists"]:
            continue  # Skip existing
        
        success = insert_prompt(prompt)
        if success:
            success_count += 1
            print(f"✅ {prompt['prompt_id']:40} INSERTED")
        else:
            fail_count += 1
            print(f"❌ {prompt['prompt_id']:40} FAILED")
    
    # Final summary
    print(f"\n{'='*80}")
    print("📊 MIGRATION SUMMARY")
    print(f"{'='*80}")
    print(f"\n✅ Successfully seeded: {success_count} prompts")
    if fail_count > 0:
        print(f"❌ Failed:              {fail_count} prompts")
    print(f"⏭️  Skipped (existing):  {existing_count} prompts")
    print(f"📁 Total discovered:    {len(prompts)} files")
    
    print(f"\n{'='*80}")
    print("✨ Migration Complete!")
    print(f"{'='*80}")
    
    # Show example queries
    print(f"\n💡 To verify in database:")
    print(f"   SELECT prompt_id, version_number, length(content)")
    print(f"   FROM utm_prompts")
    print(f"   WHERE prompt_id LIKE 'cartridge_%'")
    print(f"   ORDER BY prompt_id;")
    
    print(f"\n💡 To use in code:")
    print(f"   db = SupabasePersistence()")
    print(f"   prompt = await db.get_prompt('cartridge_pyspark_bronze')")

if __name__ == "__main__":
    main()

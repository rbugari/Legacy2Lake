import os
import glob
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Config
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(URL, KEY)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPTS_DIR = os.path.join(BASE_DIR, "apps", "api", "prompts")

def migrate_prompts():
    print("Migrating Prompts...")
    files = glob.glob(os.path.join(PROMPTS_DIR, "*.md"))
    for fpath in files:
        fname = os.path.basename(fpath)
        pid = fname.replace(".md", "")
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        
        data = {
            "prompt_id": pid,
            "content": content,
            "version": "v1.0 (Migrated)",
            "is_active": True
        }
        try:
            supabase.table("utm_prompts").upsert(data).execute()
            print(f"✅ Migrated {pid}")
        except Exception as e:
            print(f"❌ Error migrating {pid}: {e}")

def migrate_stages():
    print("Migrating Stages...")
    stages = [
        {"stage_id": 0, "label": "Discovery", "description": "Analyze source assets and identifying lineage."},
        {"stage_id": 1, "label": "Triage", "description": "Select assets for modernization."},
        {"stage_id": 2, "label": "Drafting", "description": "Generate initial code (Bronze Layer)."},
        {"stage_id": 3, "label": "Refinement", "description": "Optimize and validate code (Silver/Gold)."},
        {"stage_id": 4, "label": "Governance", "description": "Apply policies and checks."},
        {"stage_id": 5, "label": "Handover", "description": "Package for deployment."}
    ]
    try:
        supabase.table("utm_stages").upsert(stages).execute()
        print("✅ Migrated Stages")
    except Exception as e:
        print(f"❌ Error migrating stages: {e}")

def migrate_agents():
    print("Migrating Agents...")
    agents = [
        {"agent_id": "agent-a", "name": "Agent A (Detective)", "role_description": "Analyzes legacy code/manifests and builds knowledge graphs."},
        {"agent_id": "agent-c", "name": "Agent C (Interpreter)", "role_description": "Transpiles legacy logic into modern target patterns."},
        {"agent_id": "agent-f", "name": "Agent F (Critic)", "role_description": "Reviews code for optimization and compliance."},
        {"agent_id": "agent-g", "name": "Agent G (Governor)", "role_description": "Enforces security policies and naming conventions."},
        {"agent_id": "agent-s", "name": "Agent S (Scout)", "role_description": "Forensic analysis of file inventories."}
    ]
    try:
        supabase.table("utm_agent_catalog").upsert(agents).execute()
        print("✅ Migrated Agents")
    except Exception as e:
        print(f"❌ Error migrating agents: {e}")

if __name__ == "__main__":
    migrate_prompts()
    migrate_stages()
    migrate_agents()

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def check_prompts():
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    if not url or not key:
        print("Missing SUPABASE credentials in .env")
        return

    client = create_client(url, key)
    
    print("--- Listing AGENTS in Catalog ---")
    agents_res = client.table('utm_agent_catalog').select('*').execute()
    agents = agents_res.data
    for a in agents:
        print(f"Agent ID: {a['agent_id']} | Name: {a.get('name')} | Active: {a.get('is_active')}")

    print("\n--- Listing PROMPTS in utm_prompts ---")
    prompts_res = client.table('utm_prompts').select('prompt_id, name, is_active, tenant_id, content').execute()
    prompts = prompts_res.data
    print(f"Total rows in utm_prompts: {len(prompts)}")
    
    for p in prompts:
        content_len = len(p.get('content') or "")
        print(f"ID: {p['prompt_id']} | Name: {p.get('name')} | Active: {p['is_active']} | Tenant: {p['tenant_id']} | Length: {content_len}")
        if content_len > 0:
            print(f"   Snippet: {p['content'][:50]}...")

if __name__ == "__main__":
    check_prompts()

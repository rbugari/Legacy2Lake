import os
import asyncio
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

async def sync_prompt():
    # 1. Read the markdown prompt
    prompt_path = os.path.join("apps", "api", "prompts", "agent_a_discovery.md")
    with open(prompt_path, "r", encoding="utf-8") as f:
        detailed_prompt = f.read()
    
    print(f"Read prompt from {prompt_path} (Length: {len(detailed_prompt)})")

    # 2. Update Supabase
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    supabase: Client = create_client(url, key)

    print("Updating prompt for project 'base2' in utm_projects...")
    res = supabase.table("utm_projects").update({"prompt": detailed_prompt}).eq("name", "base2").execute()
    
    if res.data:
        print(f"Successfully updated prompt for project: {res.data[0]['name']}")
        print(f"New Database Prompt Length: {len(res.data[0]['prompt'])}")
    else:
        print("Error: Could not find project 'base2' in utm_projects.")

if __name__ == "__main__":
    asyncio.run(sync_prompt())

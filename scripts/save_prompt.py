
import asyncio
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

async def save_prompt_to_file():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    supabase = create_client(url, key)
    
    res = supabase.table("utm_prompts").select("content").eq("prompt_id", "agent_a_discovery").execute()
    if res.data:
        content = res.data[0].get("content", "")
        with open("scripts/prompt_debug.md", "w", encoding="utf-8") as f:
            f.write(content)
        print("Prompt saved to scripts/prompt_debug.md")
    else:
        print("Prompt not found")

if __name__ == "__main__":
    asyncio.run(save_prompt_to_file())

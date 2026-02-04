
import asyncio
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

async def read_full_prompt():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    supabase = create_client(url, key)
    
    res = supabase.table("utm_prompts").select("content").eq("prompt_id", "agent_a_discovery").execute()
    if res.data:
        content = res.data[0].get("content", "")
        print(f"TOTAL LENGTH: {len(content)}")
        # Print in 2000 char chunks
        for i in range(0, len(content), 2000):
            print(f"--- CHUNK {i//2000} ---")
            print(content[i:i+2000])
    else:
        print("Prompt not found")

if __name__ == "__main__":
    asyncio.run(read_full_prompt())

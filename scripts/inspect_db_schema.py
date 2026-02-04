
import asyncio
import os
from dotenv import load_dotenv
from supabase import create_client
import json

load_dotenv()

async def inspect_schema():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    supabase = create_client(url, key)
    
    print("Fetching 'agent_a_discovery' prompt...")
    try:
        res = supabase.table("utm_prompts").select("*").eq("prompt_id", "agent_a_discovery").execute()
        if res.data:
            print("--- AGENT A PROMPT ---")
            print(res.data[0].get("content", "No content found"))
            print("----------------------")
        else:
            print("Prompt 'agent_a_discovery' not found.")
    except Exception as e:
        print(f"Error fetching prompt: {e}")

if __name__ == "__main__":
    asyncio.run(inspect_schema())


import sys
import os
import asyncio
# Add the project root to sys.path to allow imports from apps
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from apps.api.services.persistence_service import SupabasePersistence

async def list_prompts():
    print("Connecting to DB...")
    db = SupabasePersistence()
    
    try:
        res = db.client.table("utm_prompts").select("prompt_id, metadata").execute()
        print(f"Found {len(res.data)} prompts:")
        for p in res.data:
            print(f" - ID: {p['prompt_id']}")
            print(f"   Meta: {p['metadata']}")
            print("---")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(list_prompts())

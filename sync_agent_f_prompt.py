"""
Sync Agent F Critic Prompt to Database (v4.0 Layer-Aware Update)
"""
import asyncio
from apps.api.services.persistence_service import SupabasePersistence

async def sync_prompt():
    db = SupabasePersistence(tenant_id=None)  # Global prompt
    
    # Read updated prompt
    with open("apps/api/prompts/agent_f_critic.md", "r", encoding="utf-8") as f:
        content = f.read()
    
    print(f"[SYNC] Read agent_f_critic.md: {len(content)} chars")
    
    # Save to database
    await db.save_prompt("agent_f_critic", content)
    
    print("[SYNC] ✅ Successfully synced agent_f_critic to database")
    print("[SYNC] Layer-aware validation now active for all tenants")

if __name__ == "__main__":
    asyncio.run(sync_prompt())

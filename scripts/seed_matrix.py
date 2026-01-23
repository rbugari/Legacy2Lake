
import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure we can import from apps
sys.path.append(os.getcwd())

from apps.api.services.persistence_service import SupabasePersistence

async def seed_matrix():
    print("--- Seeding Agent Matrix ---")
    
    # Admin Mode
    db = SupabasePersistence(tenant_id=None)

    # Dictionary mapping Agent ID to Technical ID (Provider + Model)
    # Default Configuration for MVP
    matrix = [
        # Agent A: Triage -> Groq Llama 3 70B (Fast & Good enough)
        {"agent_id": "agent_a", "provider": "groq", "model_id": "llama3-70b-8192", "temperature": 0.0},
        
        # Agent B: Refinement -> Azure GPT-4o (High Reasoning)
        {"agent_id": "agent_b", "provider": "azure", "model_id": "azure-gpt-4o", "temperature": 0.3},
        
        # Agent C: Coding -> Azure GPT-4o (Best Coding Model available)
        {"agent_id": "agent_c", "provider": "azure", "model_id": "azure-gpt-4o", "temperature": 0.0},
        
        # Agent F: Validation -> Azure GPT-3.5 Turbo (Fast Verification)
        {"agent_id": "agent_f", "provider": "azure", "model_id": "azure-gpt-35-turbo", "temperature": 0.0},
        
        # Agent G: Governance -> Azure GPT-4o (Strict Policy)
        {"agent_id": "agent_g", "provider": "azure", "model_id": "azure-gpt-4o", "temperature": 0.0},
    ]

    for item in matrix:
        try:
            # Check if exists
            existing = db.client.table("utm_agent_matrix")\
                .select("*", count="exact")\
                .eq("agent_id", item["agent_id"])\
                .execute()
            
            if existing.count > 0:
                print(f"[Update] Updating {item['agent_id']}...")
                db.client.table("utm_agent_matrix").update({
                    "provider": item["provider"],
                    "model_id": item["model_id"],
                    "temperature": item["temperature"]
                }).eq("agent_id", item["agent_id"]).execute()
            else:
                db.client.table("utm_agent_matrix").insert(item).execute()
                print(f"[Added] {item['agent_id']} -> {item['provider']}/{item['model_id']}")
                
        except Exception as e:
            print(f"[Error] Failed to seed matrix for {item['agent_id']}: {e}")

    print("--- Matrix Seeding Complete ---")

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(seed_matrix())


import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure we can import from apps
sys.path.append(os.getcwd())

from apps.api.services.persistence_service import SupabasePersistence

async def seed_model_catalog():
    print("--- Seeding Model Catalog ---")
    
    # Admin Mode
    db = SupabasePersistence(tenant_id=None)

    # Official Models List
    # These act as "Technical IDs" that the system understands.
    models = [
        # OpenAI
        {"provider": "openai", "model_id": "gpt-4o", "label": "GPT-4o", "context_window": 128000, "is_active": True},
        {"provider": "openai", "model_id": "gpt-4-turbo", "label": "GPT-4 Turbo", "context_window": 128000, "is_active": True},
        {"provider": "openai", "model_id": "gpt-3.5-turbo", "label": "GPT-3.5 Turbo", "context_window": 16000, "is_active": True},
        
        # Azure OpenAI (IDs often vary by deployment, but we standardize on base model names or specific deployment mappings)
        # For now, we assume user maps their deployment to these standard IDs or we allow custom.
        # But for MVP, let's stick to standard IDs.
        {"provider": "azure", "model_id": "azure-gpt-4o", "label": "Azure GPT-4o", "context_window": 128000, "is_active": True},
        {"provider": "azure", "model_id": "azure-gpt-35-turbo", "label": "Azure GPT-3.5 Turbo", "context_window": 16000, "is_active": True},
        
        # Anthropic
        {"provider": "anthropic", "model_id": "claude-3-5-sonnet-20240620", "label": "Claude 3.5 Sonnet", "context_window": 200000, "is_active": True},
        {"provider": "anthropic", "model_id": "claude-3-opus-20240229", "label": "Claude 3 Opus", "context_window": 200000, "is_active": True},
        {"provider": "anthropic", "model_id": "claude-3-haiku-20240307", "label": "Claude 3 Haiku", "context_window": 200000, "is_active": True},
        
        # Groq
        {"provider": "groq", "model_id": "llama3-70b-8192", "label": "Llama 3 70B (Groq)", "context_window": 8192, "is_active": True},
        {"provider": "groq", "model_id": "mixtral-8x7b-32768", "label": "Mixtral 8x7B (Groq)", "context_window": 32768, "is_active": True},
        
        # DeepSeek
        {"provider": "deepseek", "model_id": "deepseek-chat", "label": "DeepSeek V3", "context_window": 32000, "is_active": True},
        {"provider": "deepseek", "model_id": "deepseek-coder", "label": "DeepSeek Coder", "context_window": 32000, "is_active": True},

        # Ollama (Local)
        {"provider": "ollama", "model_id": "llama3", "label": "Llama 3 (Local)", "context_window": 8192, "is_active": True},
        {"provider": "ollama", "model_id": "mistral", "label": "Mistral (Local)", "context_window": 8192, "is_active": True},
    ]

    for m in models:
        try:
            # Check if exists by provider + model_id
            # Using count to avoid 'id column not found' error on existence check
            existing = db.client.table("utm_model_catalog")\
                .select("*", count="exact")\
                .eq("provider", m["provider"])\
                .eq("model_id", m["model_id"])\
                .execute()
            
            if existing.count > 0:
                print(f"[Skip] {m['provider']} / {m['model_id']} already exists.")
            else:
                db.client.table("utm_model_catalog").insert(m).execute()
                print(f"[Added] {m['provider']} / {m['model_id']}")
                
        except Exception as e:
            print(f"[Error] Failed to seed {m['model_id']}: {e}")

    print("--- Seeding Complete ---")

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(seed_model_catalog())

"""List all prompts in utm_prompts table"""
from connect_supabase_dev import get_supabase_client

supabase = get_supabase_client()

print("📋 Current Prompts in utm_prompts table:\n")

response = supabase.table('utm_prompts').select('prompt_id, version, is_active, created_at').execute()

print(f"Total prompts: {len(response.data)}\n")

for i, prompt in enumerate(response.data, 1):
    status = "✅ Active" if prompt['is_active'] else "❌ Inactive"
    print(f"{i:2}. {prompt['prompt_id']:30} {status:12} (v{prompt['version']})")

# Group by prefix
print("\n" + "="*70)
print("By Category:")
print("="*70)

agents = [p for p in response.data if p['prompt_id'].startswith('agent_')]
knowledge = [p for p in response.data if p['prompt_id'].startswith('knowledge_')]
system = [p for p in response.data if not p['prompt_id'].startswith('agent_') and not p['prompt_id'].startswith('knowledge_')]

print(f"\n🤖 Agents: {len(agents)}")
for p in agents:
    print(f"   - {p['prompt_id']}")

print(f"\n📚 Knowledge Modules: {len(knowledge)}")
for p in knowledge:
    print(f"   - {p['prompt_id']}")

print(f"\n⚙️  System/Other: {len(system)}")
for p in system:
    print(f"   - {p['prompt_id']}")

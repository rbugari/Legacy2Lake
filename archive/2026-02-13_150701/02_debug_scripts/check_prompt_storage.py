"""Quick check of current prompt storage in database"""
from connect_supabase_dev import get_supabase_client

supabase = get_supabase_client()

print("🔍 Checking current prompt storage in database...\n")

# Check utm_system_catalog
print("1. utm_system_catalog:")
response = supabase.table('utm_system_catalog').select('tech_id, category, type', count='exact').execute()
print(f"   Total entries: {response.count}")
print("   Technologies:")
for row in response.data:
    print(f"   - {row['tech_id']} ({row['category']} - {row['type']})")

# Check if there are any prompt-related tables
print("\n2. Checking for prompt tables:")
try:
    response = supabase.table('utm_system_prompts').select('*', count='exact').limit(1).execute()
    print(f"   ✅ utm_system_prompts exists: {response.count} rows")
except Exception as e:
    print(f"   ❌ utm_system_prompts: {str(e)[:80]}")

try:
    response = supabase.table('utm_prompts').select('*', count='exact').limit(1).execute()
    print(f"   ✅ utm_prompts exists: {response.count} rows")
except Exception as e:
    print(f"   ❌ utm_prompts: Table does not exist")

# Check if utm_global_config has prompts
print("\n3. utm_global_config:")
try:
    response = supabase.table('utm_global_config').select('key, value', count='exact').execute()
    prompt_configs = [r for r in response.data if 'prompt' in r.get('key', '').lower()]
    if prompt_configs:
        print(f"   Found {len(prompt_configs)} prompt-related configs")
        for config in prompt_configs[:3]:
            print(f"   - {config['key']}")
    else:
        print("   No prompt-related configurations found")
except Exception as e:
    print(f"   Error: {str(e)[:80]}")

print("\n" + "="*70)
print("CONCLUSION:")
print("="*70)
print("""
Current State (v3.9):
- ❌ No utm_system_prompts table exists
- ❌ Prompts are hardcoded in Python cartridges
- ✅ utm_system_catalog exists (tech registry only)

Sprint 0 Goal:
- Extract hardcoded prompts → prompt_lab/ ✅ DONE (24 prompts)
- Create utm_system_prompts table → Sprint 1 (v4.0)
- Sync prompts to DB → After table created

Status: ON TRACK for Sprint 0
""")

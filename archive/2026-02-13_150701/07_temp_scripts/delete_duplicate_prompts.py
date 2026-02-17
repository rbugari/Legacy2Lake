"""Quick check for remaining NULL tenant_id prompts"""
from supabase import create_client

SUPABASE_URL = "https://qdsdfityyxmalyipqbfm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFkc2RmaXR5eXhtYWx5aXBxYmZtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODg2NTczOSwiZXhwIjoyMDg0NDQxNzM5fQ.f4Ge4MPpeDoFLgLSD9e79V2N-ND-aU9YqwNp2VrOgC0"

client = create_client(SUPABASE_URL, SUPABASE_KEY)
response = client.table('utm_prompts').select('id, prompt_id, version, version_number').is_('tenant_id', 'null').execute()

print(f"Remaining NULL tenant_id prompts: {len(response.data)}")
print("\nPrompts to DELETE (duplicates exist):")
for p in response.data:
    print(f"  - {p['prompt_id']} (v{p['version']}, version_number={p['version_number']}, id={p['id']})")

# Delete these prompts
if response.data:
    print(f"\nDeleting {len(response.data)} duplicate prompts...")
    for p in response.data:
        try:
            delete_response = client.table("utm_prompts").delete().eq("id", p["id"]).execute()
            print(f"  ✅ Deleted {p['prompt_id']} (id={p['id']})")
        except Exception as e:
            print(f"  ❌ Error deleting {p['prompt_id']}: {e}")
    
    # Verify
    verify_response = client.table('utm_prompts').select('id').is_('tenant_id', 'null').execute()
    remaining = len(verify_response.data)
    print(f"\n{'✅ SUCCESS' if remaining == 0 else '⚠️ WARNING'}: {remaining} prompts still have NULL tenant_id")

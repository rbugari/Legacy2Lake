"""
Simplified Database Audit Script for Legacy2Lake
Quick analysis of table counts and basic code references
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client
import json
from datetime import datetime

load_dotenv()

# Initialize Supabase
url = os.getenv("SUPABASE_URL", "")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
supabase: Client = create_client(url, key)

# Known tables from documentation
KNOWN_TABLES = [
    'utm_clients', 'utm_tenants', 'utm_projects', 'utm_objects', 
    'utm_logical_steps', 'utm_column_mappings', 'utm_transformations',
    'utm_agent_matrix', 'utm_agent_catalog', 'utm_provider_vault',
    'utm_model_catalog', 'utm_design_registry', 'utm_execution_logs',
    'utm_file_inventory', 'utm_user_overrides', 'utm_asset_context',
    'utm_solution_context', 'utm_supported_techs', 'utm_tech_knowledge'
]

def get_table_row_count(table_name):
    """Get the count of rows in a table"""
    try:
        result = supabase.table(table_name).select('*', count='exact').limit(0).execute()
        return result.count if hasattr(result, 'count') else 0
    except Exception as e:
        return -1

print("🔍 Starting Quick Database Audit...")
print(f"📊 Analyzing {len(KNOWN_TABLES)} tables\n")

results = {
    'tables': [],
    'timestamp': datetime.now().isoformat()
}

for table in KNOWN_TABLES:
    print(f"Checking {table}...", end=" ")
    count = get_table_row_count(table)
    
    status = "❌ ERROR" if count == -1 else ("✅" if count > 0 else "📭")
    
    results['tables'].append({
        'name': table,
        'row_count': count,
        'exists': count != -1
    })
    
    print(f"{status} ({count} rows)" if count >= 0 else status)

# Generate summary
active = [t for t in results['tables'] if t['row_count'] > 0]
empty = [t for t in results['tables'] if t['row_count'] == 0 and t['exists']]
not_found = [t for t in results['tables'] if not t['exists']]

print("\n" + "="*50)
print("📊 SUMMARY")
print("="*50)
print(f"✅ Tables with data: {len(active)}")
print(f"📭 Empty tables: {len(empty)}")
print(f"❌ Tables not found: {len(not_found)}")

# Save results
output_dir = r"C:\Users\rfbugari\.gemini\antigravity\brain\4759dbd7-7a53-466e-90e0-8917a954c519"
json_path = os.path.join(output_dir, "database_quick_audit.json")

with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2)

print(f"\n✅ Results saved to: {json_path}")

# Generate simple markdown report
report = f"""# Database Quick Audit - Legacy2Lake
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- **Total Tables Checked**: {len(KNOWN_TABLES)}
- **✅ Tables with Data**: {len(active)}
- **📭 Empty Tables**: {len(empty)}
- **❌ Not Found**: {len(not_found)}

## Tables with Data ({len(active)})
"""

for t in sorted(active, key=lambda x: x['row_count'], reverse=True):
    report += f"- `{t['name']}`: **{t['row_count']:,}** records\n"

if empty:
    report += f"\n## Empty Tables ({len(empty)})\n"
    for t in empty:
        report += f"- `{t['name']}`\n"

if not_found:
    report += f"\n## Tables Not Found ({len(not_found)})\n"
    for t in not_found:
        report += f"- `{t['name']}` - May not exist in current schema\n"

md_path = os.path.join(output_dir, "database_quick_audit.md")
with open(md_path, 'w', encoding='utf-8') as f:
    f.write(report)

print(f"✅ Report saved to: {md_path}")
print("\n✅ Quick audit complete!")

"""
Database Audit Script for Legacy2Lake
Analyzes table usage, record counts, and code references to identify:
- Active tables (used and populated)
- Empty tables (schema exists but no data)
- Orphan tables (not referenced in code)
- Missing tables (referenced in code but don't exist)
"""

import os
import re
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client
from collections import defaultdict
import json

load_dotenv()

# Initialize Supabase
url = os.getenv("SUPABASE_URL", "")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
supabase: Client = create_client(url, key)

def get_all_tables():
    """Query PostgreSQL information schema to get all tables in public schema"""
    query = """
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE'
    ORDER BY table_name;
    """
    try:
        result = supabase.rpc('exec_sql', {'query': query}).execute()
        return [row['table_name'] for row in result.data] if result.data else []
    except Exception as e:
        print(f"Error getting tables: {e}")
        # Fallback to known tables from documentation
        return [
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
        print(f"  ⚠️  Error counting {table_name}: {e}")
        return -1

def find_table_references_in_code(table_name, project_root):
    """Search for references to table_name in Python/TypeScript files"""
    references = []
    patterns = [
        rf'\.table\(["\']({table_name}|{re.escape(table_name)})["\']',  # .table("utm_projects")
        rf'FROM\s+{table_name}\b',  # SQL FROM
        rf'JOIN\s+{table_name}\b',  # SQL JOIN
        rf'INTO\s+{table_name}\b',  # SQL INSERT INTO
        rf'UPDATE\s+{table_name}\b',  # SQL UPDATE
        rf'{table_name}',  # Direct reference (loose)
    ]
    
    search_dirs = [
        Path(project_root) / 'apps' / 'api',
        Path(project_root) / 'apps' / 'web',
        Path(project_root) / 'apps' / 'utm',
    ]
    
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
            
        for ext in ['*.py', '*.ts', '*.tsx', '*.js', '*.jsx']:
            for file_path in search_dir.rglob(ext):
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    for pattern in patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            references.append({
                                'file': str(file_path.relative_to(project_root)),
                                'type': 'code'
                            })
                            break  # Only count once per file
                except Exception as e:
                    pass
    
    return references

def analyze_database(project_root):
    """Main analysis function"""
    print("🔍 Starting Database Audit...")
    print(f"📂 Project Root: {project_root}\n")
    
    tables = get_all_tables()
    print(f"📊 Found {len(tables)} tables in database\n")
    
    results = {
        'active_tables': [],       # Has records AND code references
        'empty_tables': [],         # No records
        'orphan_tables': [],        # Has records but NO code references
        'referenced_only': [],      # Code references but empty
        'summary': {}
    }
    
    for table in tables:
        print(f"Analyzing: {table}")
        row_count = get_table_row_count(table)
        references = find_table_references_in_code(table, project_root)
        
        has_data = row_count > 0
        has_references = len(references) > 0
        
        table_info = {
            'name': table,
            'row_count': row_count,
            'reference_count': len(references),
            'references': references
        }
        
        if has_data and has_references:
            results['active_tables'].append(table_info)
            print(f"  ✅ ACTIVE: {row_count} rows, {len(references)} references")
        elif has_data and not has_references:
            results['orphan_tables'].append(table_info)
            print(f"  ⚠️  ORPHAN: {row_count} rows, NO code references")
        elif not has_data and has_references:
            results['referenced_only'].append(table_info)
            print(f"  📝 SCHEMA ONLY: 0 rows, {len(references)} references")
        else:
            results['empty_tables'].append(table_info)
            print(f"  ❌ EMPTY: No rows, NO references - CANDIDATE FOR DELETION")
        
        print()
    
    # Generate summary
    results['summary'] = {
        'total_tables': len(tables),
        'active_tables': len(results['active_tables']),
        'empty_tables': len(results['empty_tables']),
        'orphan_tables': len(results['orphan_tables']),
        'referenced_only': len(results['referenced_only'])
    }
    
    return results

def generate_report(results, output_path):
    """Generate markdown report"""
    report = f"""# Database Audit Report - Legacy2Lake
Generated: {os.popen('date /t').read().strip()}

## Executive Summary

- **Total Tables**: {results['summary']['total_tables']}
- **✅ Active Tables** (data + code): {results['summary']['active_tables']}
- **📝 Schema-Only Tables** (code but no data): {results['summary']['referenced_only']}
- **⚠️ Orphan Tables** (data but no code): {results['summary']['orphan_tables']}
- **❌ Empty Tables** (no data, no code): {results['summary']['empty_tables']}

---

## ✅ Active Tables ({len(results['active_tables'])})
These tables are actively used and contain data.

"""
    
    for table in results['active_tables']:
        report += f"\n### `{table['name']}` \n"
        report += f"- **Records**: {table['row_count']:,}\n"
        report += f"- **Code References**: {table['reference_count']}\n"
        if table['references']:
            report += f"- **Used in**: "
            files = list(set(r['file'] for r in table['references'][:5]))
            report += ', '.join(f"`{f}`" for f in files)
            if len(table['references']) > 5:
                report += f" (+{len(table['references']) - 5} more)"
            report += "\n"
    
    report += f"\n\n---\n\n## 📝 Schema-Only Tables ({len(results['referenced_only'])})\n"
    report += "These tables are referenced in code but have no data yet.\n\n"
    
    for table in results['referenced_only']:
        report += f"- **`{table['name']}`**: {table['reference_count']} references\n"
    
    report += f"\n\n---\n\n## ⚠️ Orphan Tables ({len(results['orphan_tables'])})\n"
    report += "These tables contain data but are NOT referenced in code. May be legacy or under-documented.\n\n"
    
    for table in results['orphan_tables']:
        report += f"- **`{table['name']}`**: {table['row_count']:,} records, NO code references\n"
    
    report += f"\n\n---\n\n## ❌ Empty Tables - Deletion Candidates ({len(results['empty_tables'])})\n"
    report += "These tables have no data AND no code references. Consider deleting.\n\n"
    
    for table in results['empty_tables']:
        report += f"- `{table['name']}`\n"
    
    report += "\n\n---\n\n## Recommendations\n\n"
    
    if results['empty_tables']:
        report += "### 🗑️ Immediate Actions\n"
        report += "Drop the following empty, unreferenced tables:\n```sql\n"
        for table in results['empty_tables']:
            report += f"DROP TABLE IF EXISTS {table['name']};\n"
        report += "```\n\n"
    
    if results['orphan_tables']:
        report += "### 🔍 Investigation Required\n"
        report += "Review these tables with data but no code references:\n"
        for table in results['orphan_tables']:
            report += f"- **{table['name']}**: {table['row_count']:,} rows - Is this legacy data?\n"
        report += "\n"
    
    # Save report
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ Report saved to: {output_path}")
    
    # Also save JSON for programmatic access
    json_path = output_path.replace('.md', '.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"✅ JSON data saved to: {json_path}")

if __name__ == "__main__":
    project_root = r"c:\proyectos_dev\UTM"
    output_dir = r"C:\Users\rfbugari\.gemini\antigravity\brain\4759dbd7-7a53-466e-90e0-8917a954c519"
    
    results = analyze_database(project_root)
    generate_report(results, os.path.join(output_dir, "database_audit_report.md"))
    
    print("\n✅ Database audit complete!")

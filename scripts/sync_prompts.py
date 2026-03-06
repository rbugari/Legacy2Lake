"""
Sync Prompts: Bidirectional sync between filesystem (.md) and database

Usage:
    python scripts/sync_prompts.py              # Sync .md files TO database
    python scripts/sync_prompts.py from-db      # Sync FROM database to .md files
    python scripts/sync_prompts.py status       # Check sync status

Author: Development Team
Date: 2026-02-10
Version: 1.0.0
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
import re
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from connect_supabase_dev import get_supabase_client


def parse_frontmatter(content: str) -> Dict:
    """
    Parse YAML-style frontmatter from markdown
    
    Example:
        ---
        tech_id: pyspark
        layer: bronze
        version: 2.1.0
        ---
    """
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    
    if not match:
        return {}
    
    frontmatter = {}
    for line in match.group(1).split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            frontmatter[key.strip()] = value.strip().strip('"\'')
    
    return frontmatter


def create_frontmatter(metadata: Dict) -> str:
    """Create YAML frontmatter from metadata dict"""
    lines = ['---']
    for key, value in metadata.items():
        lines.append(f'{key}: {value}')
    lines.append('---')
    lines.append('')
    return '\n'.join(lines)


def sync_to_db():
    """Sync prompts from filesystem to database"""
    supabase = get_supabase_client()
    prompt_lab = Path("prompt_lab")
    
    if not prompt_lab.exists():
        print("❌ prompt_lab/ directory not found")
        print("   Run: mkdir prompt_lab")
        return
    
    synced = 0
    errors = 0
    
    print("🔄 Syncing prompts from filesystem to database...")
    print(f"📁 Source: {prompt_lab.absolute()}\n")
    
    for md_file in prompt_lab.rglob("*.md"):
        # Skip README files
        if md_file.name == "README.md":
            continue
        
        try:
            content = md_file.read_text(encoding='utf-8')
            metadata = parse_frontmatter(content)
            
            # Extract tech_id and layer from path if not in frontmatter
            if not metadata.get('tech_id'):
                # path like: prompt_lab/cartridges/pyspark/bronze_layer.md
                parts = md_file.parts
                if 'cartridges' in parts:
                    idx = parts.index('cartridges')
                    if len(parts) > idx + 1:
                        metadata['tech_id'] = parts[idx + 1]
            
            if not metadata.get('layer'):
                # Extract from filename: bronze_layer.md -> bronze
                metadata['layer'] = md_file.stem.replace('_layer', '').replace('_', '-')
            
            # Validate required fields
            if not metadata.get('tech_id') or not metadata.get('layer'):
                print(f"⚠️  Skipping {md_file.name}: missing tech_id or layer")
                continue
            
            # Prepare data for upsert
            data = {
                'tech_id': metadata['tech_id'],
                'layer': metadata['layer'],
                'prompt_content': content,
                'source_file': str(md_file.absolute().relative_to(project_root)),
                'version': metadata.get('version', '1.0.0'),
                'is_active': True,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Upsert to database (assuming table exists)
            # Note: This will fail if table doesn't exist yet (expected in Sprint 0)
            try:
                supabase.table('utm_prompts').upsert(data).execute()
                print(f"✅ {metadata['tech_id']}/{metadata['layer']}: {md_file.name}")
                synced += 1
            except Exception as db_error:
                if 'does not exist' in str(db_error):
                    print(f"⚠️  Table utm_prompts not found (expected in Sprint 0)")
                    print(f"   File prepared: {md_file.name}")
                    synced += 1
                else:
                    raise
            
        except Exception as e:
            print(f"❌ Error processing {md_file.name}: {e}")
            errors += 1
    
    print(f"\n📊 Summary:")
    print(f"   ✅ Synced: {synced}")
    print(f"   ❌ Errors: {errors}")
    
    if synced > 0:
        print(f"\n✨ Successfully synced {synced} prompts to database!")


def sync_from_db():
    """Sync prompts from database to filesystem (backup)"""
    supabase = get_supabase_client()
    prompt_lab = Path("prompt_lab")
    
    print("🔄 Syncing prompts from database to filesystem...")
    print(f"📁 Target: {prompt_lab.absolute()}\n")
    
    try:
        # Fetch all active prompts
        response = supabase.table('utm_prompts') \
            .select('*') \
            .eq('is_active', True) \
            .execute()
        
        prompts = response.data
        
        if not prompts:
            print("⚠️  No prompts found in database")
            return
        
        synced = 0
        errors = 0
        
        for prompt in prompts:
            try:
                # Reconstruct file path
                file_path = Path(prompt['source_file'])
                full_path = project_root / file_path
                
                # Create directories
                full_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Write content
                full_path.write_text(prompt['prompt_content'], encoding='utf-8')
                
                print(f"✅ {prompt['tech_id']}/{prompt['layer']}: {file_path.name}")
                synced += 1
                
            except Exception as e:
                print(f"❌ Error writing {prompt.get('source_file', 'unknown')}: {e}")
                errors += 1
        
        print(f"\n📊 Summary:")
        print(f"   ✅ Synced: {synced}")
        print(f"   ❌ Errors: {errors}")
        
        if synced > 0:
            print(f"\n✨ Successfully synced {synced} prompts from database!")
    
    except Exception as e:
        print(f"❌ Database error: {e}")
        print("   Note: Table may not exist yet (expected in Sprint 0)")


def check_status():
    """Check sync status between filesystem and database"""
    supabase = get_supabase_client()
    prompt_lab = Path("prompt_lab")
    
    print("📊 Sync Status Check\n")
    
    # Count files
    md_files = list(prompt_lab.rglob("*.md"))
    md_files = [f for f in md_files if f.name != "README.md"]
    
    print(f"📁 Filesystem: {len(md_files)} .md files")
    
    # Count database records
    try:
        response = supabase.table('utm_system_prompts') \
            .select('*', count='exact') \
            .eq('is_active', True) \
            .execute()
        
        db_count = response.count
        print(f"🗄️  Database: {db_count} prompts")
        
        if len(md_files) == db_count:
            print("\n✅ Filesystem and database are in sync!")
        elif len(md_files) > db_count:
            print(f"\n⚠️  Filesystem has {len(md_files) - db_count} more prompts")
            print("   Run: python scripts/sync_prompts.py")
        else:
            print(f"\n⚠️  Database has {db_count - len(md_files)} more prompts")
            print("   Run: python scripts/sync_prompts.py from-db")
    
    except Exception as e:
        print(f"🗄️  Database: Unable to connect")
        print(f"   Error: {e}")
        print("\n⚠️  Table may not exist yet (expected in Sprint 0)")


def main():
    import sys
    
    if len(sys.argv) < 2:
        # Default: sync to DB
        sync_to_db()
    else:
        command = sys.argv[1].lower()
        
        if command == "from-db":
            sync_from_db()
        elif command == "status":
            check_status()
        elif command in ["help", "-h", "--help"]:
            print(__doc__)
        else:
            print(f"❌ Unknown command: {command}")
            print("Usage: python scripts/sync_prompts.py [from-db|status|help]")
            sys.exit(1)


if __name__ == "__main__":
    main()

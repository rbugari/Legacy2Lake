"""
v4.0: List Prompts in Database
Purpose: Show all prompts currently in utm_prompts table
Author: Legacy2Lake Engineering
Date: 2026-02-15
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from apps.api.services.persistence_service import SupabasePersistence
except ImportError:
    try:
        from services.persistence_service import SupabasePersistence
    except ImportError:
        from ..apps.api.services.persistence_service import SupabasePersistence


async def list_prompts():
    """List all prompts in database with details"""
    
    print("=" * 100)
    print("utm_prompts - Current Prompts in Database")
    print("=" * 100)
    print()
    
    try:
        db = SupabasePersistence()
        
        # Fetch all prompts
        result = db.client.table("utm_prompts") \
            .select("prompt_id, agent_id, tech_stack, pattern_type, is_active, created_at, updated_at") \
            .order("prompt_id") \
            .execute()
        
        prompts = result.data
        
        if not prompts:
            print("⚠️  No prompts found in database")
            return
        
        # Group by type
        agent_prompts = [p for p in prompts if p.get('agent_id') and not p.get('tech_stack')]
        cartridge_prompts = [p for p in prompts if p.get('tech_stack')]
        shared_prompts = [p for p in prompts if not p.get('agent_id') and not p.get('tech_stack')]
        
        # Agent Prompts
        if agent_prompts:
            print("🤖 AGENT PROMPTS")
            print("-" * 100)
            for p in agent_prompts:
                status = "✅" if p['is_active'] else "❌"
                print(f"{status} {p['prompt_id']:<35} | Agent: {p['agent_id']:<10}")
            print()
        
        # Cartridge Prompts
        if cartridge_prompts:
            print("📦 CARTRIDGE PROMPTS")
            print("-" * 100)
            for p in cartridge_prompts:
                status = "✅" if p['is_active'] else "❌"
                tech = p['tech_stack'] or 'N/A'
                pattern = p['pattern_type'] or 'N/A'
                print(f"{status} {p['prompt_id']:<40} | Tech: {tech:<12} | Pattern: {pattern:<8}")
            print()
        
        # Shared Prompts
        if shared_prompts:
            print("🔗 SHARED PROMPTS")
            print("-" * 100)
            for p in shared_prompts:
                status = "✅" if p['is_active'] else "❌"
                print(f"{status} {p['prompt_id']:<35}")
            print()
        
        # Summary
        print("=" * 100)
        print(f"📊 TOTAL: {len(prompts)} prompts")
        print(f"   🤖 Agents: {len(agent_prompts)}")
        print(f"   📦 Cartridges: {len(cartridge_prompts)}")
        print(f"   🔗 Shared: {len(shared_prompts)}")
        print()
        
        # Check for content length
        print("📏 Content Size Check:")
        print("-" * 100)
        result_with_content = db.client.table("utm_prompts") \
            .select("prompt_id") \
            .execute()
        
        for p in result_with_content.data[:5]:  # Show first 5 as sample
            content_result = db.client.table("utm_prompts") \
                .select("content") \
                .eq("prompt_id", p['prompt_id']) \
                .single() \
                .execute()
            
            if content_result.data:
                char_count = len(content_result.data['content'])
                print(f"   {p['prompt_id']:<40} | {char_count:>6} chars")
        
        print(f"   ... ({len(prompts) - 5} more prompts)")
        print()
        
    except Exception as e:
        print(f"\n❌ Error listing prompts: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(list_prompts())

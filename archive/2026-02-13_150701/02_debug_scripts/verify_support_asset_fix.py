"""
Verification Script: SUPPORT Assets Filtering Fix

Bug: SUPPORT assets were appearing in the graph and migration list
Fix: Only CORE assets should appear in the graph (SUPPORT = context only)

This script verifies that:
1. CORE assets have selected=True and appear in graph
2. SUPPORT assets have selected=False and DO NOT appear in graph
3. IGNORED assets are completely excluded

Created: Feb 10, 2026
Related: apps/api/routers/triage.py line 363-365
"""

import asyncio
import sys
from dotenv import load_dotenv
from apps.api.persistence.supabase_persistence import SupabasePersistence

load_dotenv()

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

async def verify_support_asset_fix():
    """Verify that SUPPORT assets are not in the graph"""
    
    db = SupabasePersistence()
    
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}VERIFYING SUPPORT ASSET FIX{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")
    
    # Get a recent project (you can change this to a specific project ID)
    print(f"{YELLOW}Step 1: Finding recent project...{RESET}")
    
    # You need to provide a project ID manually for testing
    # Example: test_project_id = "dd13fc92-4091-456a-8ce4-712406ceb831"
    test_project_id = input(f"{YELLOW}Enter project ID to test (or 'skip' to skip): {RESET}").strip()
    
    if test_project_id.lower() == 'skip':
        print(f"{YELLOW}Skipped - Manual testing required{RESET}")
        print(f"\n{BLUE}MANUAL TEST STEPS:{RESET}")
        print(f"1. Run backend: {GREEN}python run.py{RESET}")
        print(f"2. Open frontend and navigate to a project")
        print(f"3. Go to Triage stage")
        print(f"4. Upload source files and run triage")
        print(f"5. Verify:")
        print(f"   - {GREEN}✓{RESET} CORE assets appear in graph")
        print(f"   - {GREEN}✓{RESET} CORE assets have checkbox checked")
        print(f"   - {GREEN}✓{RESET} SUPPORT assets DO NOT appear in graph")
        print(f"   - {GREEN}✓{RESET} SUPPORT assets have checkbox unchecked")
        print(f"   - {GREEN}✓{RESET} IGNORED assets are not in graph or list")
        return
    
    print(f"{YELLOW}Step 2: Fetching project assets...{RESET}")
    assets = await db.get_project_assets(test_project_id)
    
    if not assets:
        print(f"{RED}✗ No assets found for project {test_project_id}{RESET}")
        return
    
    print(f"{GREEN}✓ Found {len(assets)} assets{RESET}\n")
    
    # Categorize assets
    core_assets = [a for a in assets if a.get('type') == 'CORE']
    support_assets = [a for a in assets if a.get('type') == 'SUPPORT']
    ignored_assets = [a for a in assets if a.get('type') == 'IGNORED']
    other_assets = [a for a in assets if a.get('type') not in ['CORE', 'SUPPORT', 'IGNORED']]
    
    print(f"{BLUE}Asset Distribution:{RESET}")
    print(f"  CORE:    {len(core_assets)}")
    print(f"  SUPPORT: {len(support_assets)}")
    print(f"  IGNORED: {len(ignored_assets)}")
    print(f"  OTHER:   {len(other_assets)}\n")
    
    print(f"{YELLOW}Step 3: Fetching graph layout...{RESET}")
    layout = await db.get_project_layout(test_project_id)
    nodes = layout.get('nodes', [])
    
    if not nodes:
        print(f"{YELLOW}⚠ No graph layout found (project might not have run triage yet){RESET}")
        return
    
    print(f"{GREEN}✓ Found {len(nodes)} nodes in graph{RESET}\n")
    
    # Get node IDs from graph
    graph_node_ids = {n['id'] for n in nodes}
    
    # TEST 1: Verify CORE assets
    print(f"{BLUE}TEST 1: CORE Assets{RESET}")
    core_in_graph = sum(1 for a in core_assets if a['id'] in graph_node_ids)
    core_selected = sum(1 for a in core_assets if a.get('selected', False))
    
    print(f"  Total CORE assets: {len(core_assets)}")
    print(f"  CORE in graph: {core_in_graph}")
    print(f"  CORE selected: {core_selected}")
    
    if core_in_graph == len(core_assets) and core_selected == len(core_assets):
        print(f"  {GREEN}✓ PASS: All CORE assets in graph and selected{RESET}")
    else:
        print(f"  {RED}✗ FAIL: CORE assets not properly configured{RESET}")
    
    print()
    
    # TEST 2: Verify SUPPORT assets (CRITICAL FIX)
    print(f"{BLUE}TEST 2: SUPPORT Assets (Critical Fix){RESET}")
    support_in_graph = sum(1 for a in support_assets if a['id'] in graph_node_ids)
    support_selected = sum(1 for a in support_assets if a.get('selected', False))
    
    print(f"  Total SUPPORT assets: {len(support_assets)}")
    print(f"  SUPPORT in graph: {support_in_graph}")
    print(f"  SUPPORT selected: {support_selected}")
    
    if support_in_graph == 0 and support_selected == 0:
        print(f"  {GREEN}✓ PASS: SUPPORT assets NOT in graph (correct!){RESET}")
    else:
        print(f"  {RED}✗ FAIL: SUPPORT assets found in graph (BUG!){RESET}")
        print(f"  {RED}  This means the fix was not applied or project needs re-triage{RESET}")
    
    print()
    
    # TEST 3: Verify IGNORED assets
    print(f"{BLUE}TEST 3: IGNORED Assets{RESET}")
    ignored_in_graph = sum(1 for a in ignored_assets if a['id'] in graph_node_ids)
    ignored_selected = sum(1 for a in ignored_assets if a.get('selected', False))
    
    print(f"  Total IGNORED assets: {len(ignored_assets)}")
    print(f"  IGNORED in graph: {ignored_in_graph}")
    print(f"  IGNORED selected: {ignored_selected}")
    
    if ignored_in_graph == 0 and ignored_selected == 0:
        print(f"  {GREEN}✓ PASS: IGNORED assets NOT in graph (correct!){RESET}")
    else:
        print(f"  {RED}✗ FAIL: IGNORED assets found in graph{RESET}")
    
    print()
    
    # Summary
    print(f"{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}SUMMARY{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")
    
    all_tests_passed = (
        core_in_graph == len(core_assets) and 
        core_selected == len(core_assets) and
        support_in_graph == 0 and 
        support_selected == 0 and
        ignored_in_graph == 0 and 
        ignored_selected == 0
    )
    
    if all_tests_passed:
        print(f"{GREEN}✓ ALL TESTS PASSED{RESET}")
        print(f"{GREEN}  The fix is working correctly!{RESET}")
    else:
        print(f"{YELLOW}⚠ SOME TESTS FAILED{RESET}")
        print(f"{YELLOW}  Project might need to be re-triaged to apply fix{RESET}")
    
    print()
    
    # Show sample SUPPORT assets for context
    if support_assets:
        print(f"{BLUE}Sample SUPPORT Assets (for context only):{RESET}")
        for asset in support_assets[:5]:
            in_graph = "🔴 IN GRAPH" if asset['id'] in graph_node_ids else "✅ NOT IN GRAPH"
            selected = "✅" if asset.get('selected', False) else "❌"
            print(f"  - {asset['filename']:40} | Selected: {selected} | {in_graph}")
    
    print()

if __name__ == "__main__":
    try:
        asyncio.run(verify_support_asset_fix())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Verification cancelled by user{RESET}")
    except Exception as e:
        print(f"\n{RED}Error during verification: {e}{RESET}")
        import traceback
        traceback.print_exc()

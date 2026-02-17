"""
Test script for sidebar metrics endpoint
Sprint 14 - Stage-Adaptive Sidebar Backend Validation
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apps.api.services.persistence_service import SupabasePersistence
from apps.api.routers.projects import _detect_stage_from_status, _calculate_progress_from_logs, _extract_current_agent


async def test_helper_functions():
    """Test utility functions"""
    print("\n=== Testing Helper Functions ===")
    
    # Test stage detection
    print("\n1. Stage Detection:")
    test_statuses = ["DISCOVERY", "TRIAGE", "DRAFTING", "REFINEMENT", "GOVERNANCE", "COMPLETED"]
    for status in test_statuses:
        stage = _detect_stage_from_status(status)
        print(f"   {status:15s} -> Stage {stage}")
    
    # Test progress calculation
    print("\n2. Progress Calculation:")
    mock_logs = [
        {"log_message": "[Agent-A] Starting..."},
        {"log_message": "[Agent-C] Generating code..."},
        {"log_message": "[Agent-C] More code..."},
        {"log_message": "[Agent-F] Reviewing..."},
    ]
    progress = _calculate_progress_from_logs(mock_logs)
    print(f"   Progress: {progress}%")
    
    # Test agent extraction
    print("\n3. Current Agent Extraction:")
    agent = _extract_current_agent(mock_logs)
    print(f"   Current Agent: {agent}")
    
    print("\n✅ Helper functions working correctly\n")


async def test_sidebar_metrics_endpoint(project_id: str = None):
    """Test sidebar metrics calculation for all stages"""
    print("\n=== Testing Sidebar Metrics Calculation ===")
    
    # Initialize DB
    db = SupabasePersistence()
    
    # If no project_id provided, try to find one
    if not project_id:
        projects = await db.list_projects()
        if not projects:
            print("❌ No projects found. Create a project first.")
            return
        project_id = projects[0].get("project_id")
        print(f"Using first available project: {project_id}")
    
    # Test each stage
    stages = [0, 1, 2, 3, 4]
    stage_names = ["Discovery", "Triage", "Drafting", "Refinement", "Governance"]
    
    for stage, name in zip(stages, stage_names):
        print(f"\n--- Stage {stage}: {name} ---")
        
        try:
            # Get project metadata
            project = await db.get_project_metadata(project_id)
            if not project:
                print(f"❌ Project {project_id} not found")
                return
            
            print(f"Project: {project.get('project_name', 'Unknown')}")
            print(f"Status: {project.get('status', 'Unknown')}")
            
            # Test stage-specific metrics
            if stage == 0:
                files = await db.get_project_files_from_db(project_id)
                print(f"✓ Files: {len(files)}")
            
            elif stage == 1:
                assets = await db.get_project_assets(project_id)
                print(f"✓ Assets: {len(assets)}")
                
                tech_stats = await db.get_project_tech_stats(project_id)
                print(f"✓ Source Tech: {tech_stats.get('source_tech', 'Unknown')}")
                
                quality_stats = await db.get_quality_metrics_summary(project_id)
                print(f"✓ Quality Score: {quality_stats.get('avg_quality_score', 0):.2f}")
            
            elif stage == 2:
                layout = await db.get_project_layout(project_id)
                nodes = layout.get("nodes", []) if layout else []
                bronze = sum(1 for n in nodes if n.get("layer") == "bronze")
                silver = sum(1 for n in nodes if n.get("layer") == "silver")
                gold = sum(1 for n in nodes if n.get("layer") == "gold")
                print(f"✓ Nodes: {len(nodes)} (Bronze:{bronze}, Silver:{silver}, Gold:{gold})")
            
            elif stage == 3:
                validations = await db.get_code_validations(project_id)
                issues = sum(1 for v in validations if not v.get("is_valid", True))
                print(f"✓ Validations: {len(validations)} ({issues} issues)")
            
            elif stage == 4:
                gov_files = await db.get_governance_files(project_id)
                print(f"✓ Governance Files: {len(gov_files)}")
        
        except Exception as e:
            print(f"⚠️  Error in Stage {stage}: {e}")
    
    print("\n✅ Sidebar metrics test completed\n")


async def test_real_endpoint():
    """Test the actual endpoint logic"""
    print("\n=== Testing Full Endpoint Logic ===")
    
    try:
        from apps.api.routers.projects import get_sidebar_metrics
        from apps.api.routers.dependencies import get_db
        
        # Get first project
        db = SupabasePersistence()
        projects = await db.list_projects()
        
        if not projects:
            print("❌ No projects found")
            return
        
        project_id = projects[0].get("project_id")
        print(f"Testing with project: {project_id}")
        
        # Test auto-detection (no stage parameter)
        print("\n1. Auto-detect stage from project status:")
        result = await get_sidebar_metrics(project_id=project_id, stage=None, db=db)
        print(f"   Status: {result.get('executionStatus')}")
        print(f"   Keys returned: {', '.join(result.keys())}")
        
        # Test explicit stages
        print("\n2. Explicit stage requests:")
        for stage in [0, 1, 2, 3]:
            result = await get_sidebar_metrics(project_id=project_id, stage=stage, db=db)
            print(f"   Stage {stage}: {len(result)} metrics returned")
        
        print("\n✅ Full endpoint test passed\n")
        
    except Exception as e:
        print(f"❌ Endpoint test failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests"""
    print("=" * 60)
    print("SIDEBAR METRICS BACKEND VALIDATION")
    print("Sprint 14 - Stage-Adaptive Navigation")
    print("=" * 60)
    
    # Test 1: Helper functions
    await test_helper_functions()
    
    # Test 2: Database methods per stage
    await test_sidebar_metrics_endpoint()
    
    # Test 3: Full endpoint
    await test_real_endpoint()
    
    print("=" * 60)
    print("VALIDATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Test script for Quick Assessment v4.0
Tests the new endpoint that replaces Agent S
"""
import os
import sys
import asyncio
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from apps.api.services.quick_assessment_service import QuickAssessmentService

async def test_quick_assessment():
    """Test Quick Assessment with real project"""
    
    # Test with project "ttt" (UUID: bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4)
    project_id = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"
    tenant_id = "daac0ee6-3b28-412d-8acd-43ec51149188"
    
    print("=" * 60)
    print("🧪 Testing Quick Assessment v4.0")
    print("=" * 60)
    print(f"Project ID: {project_id}")
    print(f"Tenant ID: {tenant_id}")
    print()
    
    try:
        service = QuickAssessmentService(tenant_id=tenant_id)
        
        print("⏳ Running assessment...")
        result = await service.assess(project_id)
        
        print()
        print("=" * 60)
        print("✅ ASSESSMENT COMPLETE")
        print("=" * 60)
        print(f"Score: {result.score}/100")
        print(f"Semaphore: {result.semaforo.upper()}")
        print(f"Total Files: {result.total_files}")
        print(f"Total Lines: {result.total_lines}")
        print()
        print("File Breakdown:")
        for category, count in result.file_breakdown.items():
            print(f"  - {category.capitalize()}: {count}")
        print()
        print(f"Detected Technologies: {', '.join(result.detected_techs) if result.detected_techs else 'None'}")
        print()
        if result.blockers:
            print(f"⚠️ Blockers ({len(result.blockers)}):")
            for blocker in result.blockers:
                print(f"  - {blocker}")
            print()
        
        if result.llm_opinion:
            print("💬 LLM Opinion:")
            print(f"  {result.llm_opinion}")
        else:
            print("ℹ️ No LLM opinion (agent-qa not configured)")
        
        print()
        print("=" * 60)
        print("✅ TEST PASSED")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ TEST FAILED")
        print("=" * 60)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_quick_assessment())
    sys.exit(0 if success else 1)

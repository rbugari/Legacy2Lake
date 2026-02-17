#!/usr/bin/env python3
"""
Test script for Quick Assessment HTTP endpoint
Tests the actual API endpoint that frontend calls
"""
import os
import sys
import requests
import json
from dotenv import load_dotenv

load_dotenv()

SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
TENANT_ID = "daac0ee6-3b28-412d-8acd-43ec51149188"
PROJECT_ID = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"
BASE_URL = "http://localhost:8000"

def test_quick_assessment_http():
    """Test Quick Assessment via HTTP endpoint"""
    
    print("=" * 60)
    print("🧪 Testing Quick Assessment HTTP Endpoint")
    print("=" * 60)
    print(f"URL: {BASE_URL}/projects/{PROJECT_ID}/quick-assessment")
    print(f"Tenant: {TENANT_ID}")
    print()
    
    headers = {
        "X-Tenant-ID": TENANT_ID,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    # POST request to run assessment
    print("⏳ Sending POST request...")
    response = requests.post(
        f"{BASE_URL}/projects/{PROJECT_ID}/quick-assessment",
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    print()
    
    if response.status_code == 200:
        data = response.json()
        
        print("=" * 60)
        print("✅ ASSESSMENT COMPLETE")
        print("=" * 60)
        print(f"Score: {data['score']}/100")
        print(f"Semaphore: {data['semaforo'].upper()}")
        print(f"Total Files: {data['total_files']}")
        print(f"Total Lines: {data['total_lines']}")
        print()
        print("File Breakdown:")
        for category, count in data['file_breakdown'].items():
            print(f"  - {category.capitalize()}: {count}")
        print()
        print(f"Detected Technologies: {', '.join(data['detected_techs']) if data['detected_techs'] else 'None'}")
        print()
        
        if data.get('blockers'):
            print(f"⚠️ Blockers ({len(data['blockers'])}):")
            for blocker in data['blockers']:
                print(f"  - {blocker}")
            print()
        
        if data.get('llm_opinion'):
            print("💬 LLM Opinion:")
            print(f"  {data['llm_opinion']}")
        else:
            print("ℹ️ No LLM opinion (agent-qa not configured)")
        
        print()
        print("=" * 60)
        print("✅ HTTP TEST PASSED")
        print("=" * 60)
        
        # Now test GET endpoint
        print()
        print("⏳ Testing GET endpoint (retrieve saved assessment)...")
        get_response = requests.get(
            f"{BASE_URL}/projects/{PROJECT_ID}/quick-assessment",
            headers=headers
        )
        
        print(f"Status Code: {get_response.status_code}")
        
        if get_response.status_code == 200:
            get_data = get_response.json()
            print("✅ GET endpoint works - assessment was saved to database")
            print(f"   Score from DB: {get_data['score']}")
        else:
            print(f"❌ GET endpoint failed: {get_response.text}")
        
        return True
        
    else:
        print("=" * 60)
        print("❌ HTTP TEST FAILED")
        print("=" * 60)
        print(f"Response: {response.text}")
        return False

if __name__ == "__main__":
    try:
        success = test_quick_assessment_http()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

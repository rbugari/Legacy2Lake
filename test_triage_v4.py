#!/usr/bin/env python3
"""
Test Phase 1 (Triage) - Verificación de v4.0 Zero-Hardcode
"""
import os
import sys
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()

SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
TENANT_ID = "daac0ee6-3b28-412d-8acd-43ec51149188"
PROJECT_ID = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"
BASE_URL = "http://localhost:8085"  # Backend en puerto 8085

def test_triage():
    """Test Phase 1 (Triage) execution"""
    
    print("=" * 70)
    print("🧪 Testing Phase 1 (Triage) - v4.0 Zero-Hardcode")
    print("=" * 70)
    print(f"Project ID: {PROJECT_ID}")
    print(f"Tenant: {TENANT_ID}")
    print()
    
    headers = {
        "X-Tenant-ID": TENANT_ID,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    # POST /projects/{id}/triage
    print("⏳ Executing Phase 1 (Triage)...")
    response = requests.post(
        f"{BASE_URL}/projects/{PROJECT_ID}/triage",
        headers=headers,
        json={},  # Empty body for TriageParams (all fields optional)
        timeout=60
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code != 200:
        print()
        print("=" * 70)
        print("❌ TRIAGE FAILED")
        print("=" * 70)
        print(f"Response: {response.text[:500]}")
        return False
    
    data = response.json()
    
    print()
    print("=" * 70)
    print("✅ TRIAGE COMPLETED")
    print("=" * 70)
    print(f"Status: {data.get('status')}")
    print(f"Assets Processed: {data.get('total_assets', 0)}")
    print()
    
    # Wait and check logs
    print("⏳ Fetching execution logs...")
    time.sleep(2)
    
    logs_response = requests.get(
        f"{BASE_URL}/projects/{PROJECT_ID}/execution-logs?type=triage",
        headers=headers
    )
    
    if logs_response.status_code == 200:
        logs = logs_response.json()
        
        print()
        print("📋 Execution Logs:")
        print("-" * 70)
        
        # Check for key indicators
        has_librarian = False
        has_table_impact = False
        has_400_error = False
        
        for log in logs[:20]:  # Show first 20 logs
            message = log.get('message', '')
            print(f"  [{log.get('severity', 'INFO')}] {message[:80]}")
            
            if '[Librarian]' in message:
                has_librarian = True
            if '[TableImpact]' in message:
                has_table_impact = True
            if '400' in message or 'Bad Request' in message:
                has_400_error = True
        
        print()
        print("=" * 70)
        print("🔍 Verification Results:")
        print("=" * 70)
        print(f"✅ Librarian executed: {'YES' if has_librarian else 'NO ❌'}")
        print(f"✅ TableImpact executed: {'YES' if has_table_impact else 'NO ❌'}")
        print(f"❌ 400 Bad Request errors: {'YES ❌' if has_400_error else 'NO ✅'}")
        print()
        
        if has_librarian and has_table_impact and not has_400_error:
            print("=" * 70)
            print("🎉 v4.0 ZERO-HARDCODE WORKING CORRECTLY!")
            print("=" * 70)
            return True
        else:
            print("=" * 70)
            print("⚠️ Some components not working correctly")
            print("=" * 70)
            return False
    else:
        print(f"❌ Could not fetch logs: {logs_response.status_code}")
        return False

if __name__ == "__main__":
    try:
        success = test_triage()
        sys.exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("❌ Connection refused - Is the backend running?")
        print("   Run: .\\start_backend.ps1")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

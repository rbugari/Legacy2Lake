#!/usr/bin/env python3
"""
Test fix for utm_asset_columns.tenant_id warnings
"""
import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
TENANT_ID = "daac0ee6-3b28-412d-8acd-43ec51149188"
PROJECT_ID = "bc0a94d4-e0e5-424a-ad93-0c8ae586a8f4"
USER_ID = "f0be9a13-340d-4327-a72f-cc9a2afb6de9"  # ADMIN user
BASE_URL = "http://localhost:8085"

def run_test():
    headers = {
        "X-Tenant-ID": TENANT_ID,
        "X-User-ID": USER_ID,
        "X-Role": "ADMIN",
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    print("=" * 70)
    print("🧪 Testing utm_asset_columns.tenant_id Fix")
    print("=" * 70)
    print(f"Project ID: {PROJECT_ID}")
    print()
    
    # Trigger Triage
    print("⏳ Triggering Triage...")
    try:
        response = requests.post(
            f"{BASE_URL}/projects/{PROJECT_ID}/triage",
            headers=headers,
            json={},
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Triage started: {data.get('message', 'Running in background')}")
        else:
            print(f"❌ Error: {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return
    
    # Wait for execution
    print("\n⏳ Waiting 60 seconds for Triage to execute...")
    time.sleep(60)
    
    # Check logs for warnings
    print("\n📋 Checking audit logs...")
    log_file = "logs/audit_log_20260213.jsonl"
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            tail_lines = lines[-200:]  # Last 200 lines
            
        # Count warnings
        warning_count = 0
        for line in tail_lines:
            if 'utm_asset_columns.tenant_id' in line:
                warning_count += 1
        
        print()
        print("=" * 70)
        if warning_count == 0:
            print("✅ SUCCESS: No tenant_id warnings found!")
            print("=" * 70)
            print("The fix is working correctly.")
        else:
            print(f"❌ FAILED: Found {warning_count} tenant_id warnings")
            print("=" * 70)
            print("Sample warnings:")
            count = 0
            for line in tail_lines:
                if 'utm_asset_columns.tenant_id' in line and count < 3:
                    print(f"  {line.strip()[:100]}...")
                    count += 1
    
    except FileNotFoundError:
        print(f"❌ Log file not found: {log_file}")
    except Exception as e:
        print(f"❌ Error reading logs: {e}")

if __name__ == "__main__":
    run_test()


import os
import sys
import asyncio
import json
from pathlib import Path

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from apps.api.services.persistence_service import PersistenceService
    from apps.api.services.refinement.governance_service import GovernanceService
    from apps.api.utils.logger import logger
except ImportError:
    print("Error: Could not import services. Make sure you are running from project root.")
    sys.exit(1)

async def verify_phase4():
    # Use a known project from R2 listing: 461b0d87-57a4-4ce5-b990-977bec9603eb/pruebausr
    project_id = "pruebausr" 
    tenant_id = "461b0d87-57a4-4ce5-b990-977bec9603eb" 
    
    print(f"--- Verifying Phase 4 R2 Migration for Project: {project_id} ---")
    
    # 1. Check Certification Report
    gov_service = GovernanceService(tenant_id=tenant_id)
    print("Step 1: Generating Certification Report...")
    
    # Simulate DB data for governance
    mock_gov_data = {
        "audit_json": {"score": 85, "summary": "R2 Verification Mock Audit"},
        "runbook_markdown": "# R2 Runbook\nVerified cloud-native generation."
    }
    
    try:
        # get_certification_report is now async and fetches its own governance data
        report = await gov_service.get_certification_report(project_id)
        
        print("\n[REPORT SUMMARY]")
        print(f"Project ID: {report['project_id']}")
        print(f"Score: {report['score']}")
        print(f"Stats: {json.dumps(report['stats'], indent=2)}")
        print(f"Lineage Count: {len(report['lineage'])}")
        print(f"Logs Count: {len(report['compliance_logs'])}")
        
        if report['stats']['total_files'] > 0:
            print("SUCCESS: Stats calculated from R2 files.")
        else:
            print("WARNING: No files found in R2 for stats calculation (check if test5 exists in R2).")
            
        if report['compliance_logs']:
             print("SUCCESS: Logs retrieved from R2.")
        else:
             print("INFO: No compliance logs found in R2 logs.")
             
    except Exception as e:
        print(f"ERROR in Certification Report: {e}")
        import traceback
        traceback.print_exc()

    # 2. Check Export Bundle
    print("\nStep 2: Creating Export Bundle (ZIP)...")
    try:
        zip_buffer = await gov_service.create_export_bundle(project_id)
        size_kb = len(zip_buffer.getvalue()) / 1024
        print(f"SUCCESS: Generated ZIP bundle in memory. Size: {size_kb:.2f} KB")
        
        if size_kb > 0:
            # Optionally save locally just for verification
            output_file = "phase4_r2_verify.zip"
            with open(output_file, "wb") as f:
                f.write(zip_buffer.getvalue())
            print(f"Sample bundle saved to: {output_file}")
    except Exception as e:
        print(f"ERROR in Export Bundle: {e}")

if __name__ == "__main__":
    asyncio.run(verify_phase4())

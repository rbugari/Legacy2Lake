import pytest
import io
import zipfile
from apps.api.services.refinement.governance_service import GovernanceService

@pytest.mark.asyncio
async def test_governance_export_bundle():
    """Verify that the export bundle contains the AI-generated runbook."""
    service = GovernanceService()
    
    # Using a dummy project ID
    project_id = "test_project_handover"
    
    # Generate bundle
    bundle_buffer = await service.create_export_bundle(project_id)
    
    # Check ZIP content
    with zipfile.ZipFile(bundle_buffer, 'r') as zip_ref:
        file_list = zip_ref.namelist()
        assert "Modernization_Runbook.md" in file_list, "Runbook should be in the bundle"
        
        # Read runbook content
        with zip_ref.open("Modernization_Runbook.md") as f:
            content = f.read().decode('utf-8')
            assert "# Modernization Runbook" in content
            
    print("Export Bundle Verification Passed!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_governance_export_bundle())

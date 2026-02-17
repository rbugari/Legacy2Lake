import asyncio
import os
import sys
from dotenv import load_dotenv
load_dotenv()

# Add apps/api to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "apps", "api")))

from services.prompt_lab_service import PromptLabService

async def debug_export():
    tenant_id = "f98edb5e-4165-4c49-9fce-18894e8a818c"
    client_id = "16368cc6-3d09-4316-b54f-2d64bab9b7ef"
    
    print(f"Testing export for Tenant: {tenant_id}")
    lab = PromptLabService(tenant_id=tenant_id, client_id=client_id)
    
    # Check if we can find Agent C
    content = await lab.db.get_prompt("agent_c_interpreter")
    if content:
        print(f"Content found for Agent C ({len(content)} chars)")
    else:
        print("Content NOT found for Agent C")
        # Let's see what the DB says
        res = lab.db.client.table("utm_prompts").select("*").eq("prompt_id", "agent_c_interpreter").execute()
        print(f"DB search for 'agent_c_interpreter': {res.data}")

    result = await lab.export_to_lab(output_dir="./test_lab_export")
    print(f"Export Result: {result}")

if __name__ == "__main__":
    asyncio.run(debug_export())

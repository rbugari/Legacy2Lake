
import sys
import os
import asyncio
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from apps.api.services.prompt_lab_service import PromptLabService

def test_enrichment():
    lab = PromptLabService()
    
    print("Testing Agent R mapping...")
    prompt_data = lab.get_enriched_prompt("agent-r", "ssis", "snowflake")
    
    if prompt_data and prompt_data.get("prompt"):
        print("SUCCESS: Prompt found!")
        print(f"Base Prompt Length: {len(prompt_data.get('base_prompt', ''))}")
        print(f"Enriched Prompt Length: {len(prompt_data.get('prompt', ''))}")
        print(f"Is Enriched: {prompt_data.get('is_enriched')}")
    else:
        print("FAILURE: No prompt returned.")
        print(prompt_data)

if __name__ == "__main__":
    test_enrichment()

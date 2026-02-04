
import os
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()

async def test_azure():
    # Use credentials from .env or hardcode from what I found in DB for testing
    api_key = "58132a497d104bcda424721d8fcf5d4d"
    endpoint = "https://gpt4-testing-soprasteriaspain.openai.azure.com/"
    deployment = "gpt-4.1"
    api_version = "2025-01-01-preview"
    
    print(f"Testing Azure OpenAI at {endpoint}...")
    try:
        llm = AzureChatOpenAI(
            azure_endpoint=endpoint,
            azure_deployment=deployment,
            openai_api_version=api_version,
            api_key=api_key,
            temperature=0
        )
        
        print("Invoking model...")
        response = await llm.ainvoke([HumanMessage(content="Hello, please return a JSON { 'status': 'ok' }")])
        print(f"Response: '{response.content}'")
        
        if not response.content:
            print("WARNING: Received EMPTY response from Azure OpenAI!")
            
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_azure())

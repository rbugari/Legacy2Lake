
import os
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()

async def test_azure():
    # Use credentials from .env
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "https://gpt4-testing-soprasteriaspain.openai.azure.com/")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
    
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

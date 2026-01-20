import os
from openai import AzureOpenAI, OpenAI
# from groq import Groq  # Uncomment when Groq usage is active

class LLMRouter:
    """
    Handles request routing to different LLM providers (Azure, OpenAI, Groq)
    based on the Agent's need (Complexity vs Speed).
    """

    def __init__(self):
        # Azure Configuration
        self.azure_client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_ID", "gpt-4.1")

        # Fallback/Direct Configuration (Optional)
        # self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def complete(self, prompt: str, system_role: str = "You are a helpful AI assistant.", provider: str = "AZURE", temperature: float = 0.0) -> str:
        """
        Universal completion method.
        """
        if provider == "AZURE":
            return self._call_azure(prompt, system_role, temperature)
        elif provider == "GROQ":
            return self._call_azure(prompt, system_role, temperature) # Fallback to Azure for now until Groq key is provided
        else:
            return self._call_azure(prompt, system_role, temperature)

    def _call_azure(self, prompt: str, system_role: str, temperature: float) -> str:
        try:
            response = self.azure_client.chat.completions.create(
                model=self.azure_deployment,
                messages=[
                    {"role": "system", "content": system_role},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error calling Azure OpenAI: {e}")
            raise e

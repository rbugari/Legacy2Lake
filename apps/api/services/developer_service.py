import os
import json
from typing import Dict, Any, List
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
try:
    from apps.api.utils.logger import logger
except ImportError:
    try:
        from utils.logger import logger
    except ImportError:
        from ..utils.logger import logger

class DeveloperService:
    """
    The Code Developer: Context-Aware Transpiler.
    Generates PySpark code using Platform Rules and Schema Context.
    """

    def __init__(self):
        self.llm = AzureChatOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_ID", "gpt-4"),
            openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            temperature=0  # Deterministic code gen
        )
        self.prompt_path = os.path.join(os.path.dirname(__file__), "../prompts/developer_transpiler.md")

    def _load_prompt(self) -> str:
        with open(self.prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    @logger.llm_debug("Developer-Transpiler")
    async def generate_code(self, 
                            task_def: Dict[str, Any], 
                            platform_spec: Dict[str, Any], 
                            schema_ref: Dict[str, Any],
                            prompt_template: str = None) -> Dict[str, Any]:
        """
        Generates code for a specific task/package.
        """
        logger.info(f"Generating code for task: {task_def.get('package_name')}", "Developer")
        if prompt_template:
            system_prompt = prompt_template
        else:
            system_prompt = self._load_prompt()
        
        # Prepare Context
        # Filter schema ref to only relevant tables if possible, 
        # but for now passing full context (or a summarized version is better for token limits).
        # We'll rely on the LLM to pick what it needs from the provided JSONs.
        
        user_message = f"""
        PLATFORM RULES (Use these patterns):
        {json.dumps(platform_spec, indent=2)}
        
        TARGET SCHEMA (Use these types):
        {json.dumps(schema_ref, indent=2)}
        
        TASK TO TRANSPILE:
        Name: {task_def.get('package_name')}
        Inputs: {task_def.get('inputs')}
        Lookups: {task_def.get('lookups')}
        Outputs: {task_def.get('outputs')}
        Description: Auto-generated task from SSIS package {task_def.get('package_name')}.
        """

        # DEBUG: Log the full constructed prompt
        logger.debug("Constructed LLM Prompt (System)", "Developer", system_prompt)
        logger.debug("Constructed LLM Prompt (User)", "Developer", user_message)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]

        try:
            response = await self.llm.ainvoke(messages)
            content = response.content.strip()

            logger.debug("Raw LLM Response", "Developer", content)

            # Clean JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            return json.loads(content)
        except Exception as e:
            logger.error(f"Error generating code: {e}", "Developer")
            return {
                "error": str(e),
                "notebook_content": f"# Error generating code: {e}"
            }

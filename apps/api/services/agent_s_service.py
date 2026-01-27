import os
import json
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from typing import Dict, Any, List, Optional

try:
    from apps.api.utils.logger import logger
    from apps.api.services.persistence_service import SupabasePersistence
except ImportError:
    try:
        from utils.logger import logger
        from services.persistence_service import SupabasePersistence
    except ImportError:
        from ..utils.logger import logger
        from .persistence_service import SupabasePersistence

class AgentSService:
    """Service for Agent S (Scout) - Forensic Repository Assessment."""
    
    def __init__(self, tenant_id: Optional[str] = None, client_id: Optional[str] = None):
        self.tenant_id = tenant_id
        self.client_id = client_id

    async def _get_llm(self):
        """Resolves LLM client from Agent Matrix (DB) or Env Vars."""
        db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
        
        # 1. Try DB Resolution
        resolved = await db.resolve_agent_model("agent-s")
        
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        key = os.getenv("AZURE_OPENAI_API_KEY")
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_ID", "gpt-4")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION")
        temperature = 0
        provider = "azure"
        
        if resolved:
            provider = resolved.get("provider", "azure")
            if resolved.get("endpoint"): endpoint = resolved.get("endpoint")
            if resolved.get("api_key"): key = resolved.get("api_key")
            if resolved.get("deployment"): deployment = resolved.get("deployment")
            if resolved.get("api_version"): api_version = resolved.get("api_version")
            if "temperature" in resolved: temperature = resolved["temperature"]
            
        if provider == "azure":
            return AzureChatOpenAI(
                azure_endpoint=endpoint,
                azure_deployment=deployment,
                openai_api_version=api_version,
                api_key=key,
                temperature=temperature
            )
        else:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=deployment,
                api_key=key,
                base_url=endpoint,
                temperature=temperature
            )
        
    async def _load_prompt(self) -> str:
        db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
        return await db.get_prompt("agent_s_scout")

    async def save_prompt(self, content: str):
        db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
        await db.save_prompt("agent_s_scout", content)

    async def assess_repository(self, file_list: List[str], system_prompt_override: str = None) -> Dict[str, Any]:
        """Performs forensic assessment of the provided file list."""
        system_prompt = system_prompt_override or await self._load_prompt()
        
        # Classify files by type for better analysis
        file_types = {}
        for file_path in file_list:
            ext = file_path.split('.')[-1].lower() if '.' in file_path else 'unknown'
            file_types[ext] = file_types.get(ext, 0) + 1
        
        user_message = f"""
FILE INVENTORY TO ASSESS:
-------------------------
Total Files: {len(file_list)}
File Types Distribution: {json.dumps(file_types, indent=2)}

Complete File List:
{json.dumps(file_list, indent=2)}

INSTRUCTIONS:
1. Analyze the inventory for completeness
2. Identify missing dependencies (files referenced but not present)
3. Detect technology stack from file extensions and patterns
4. Assign a completeness score (0-100) based on typical project structure
5. List specific gaps with impact level (HIGH/MEDIUM/LOW)

Expected Output Format (JSON only):
{{
    "assessment_summary": "Brief 2-3 sentence summary of findings",
    "completeness_score": 85,
    "detected_technology": "SSIS/SQL Server",
    "detected_gaps": [
        {{
            "category": "MISSING_DEPENDENCY|MISSING_CONFIG|MISSING_DOCUMENTATION|TECHNOLOGY_MISMATCH",
            "impact": "HIGH|MEDIUM|LOW",
            "gap_description": "Specific description of what's missing or wrong",
            "suggested_file": "filename.ext"
        }}
    ]
}}

IMPORTANT: Return ONLY valid JSON, no markdown formatting.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]
        
        llm = await self._get_llm()
        response = await llm.ainvoke(messages)
        content = response.content
        
        # Clean potential markdown formatting
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()
            
        try:
            result = json.loads(content)
            # Ensure required fields exist
            if "assessment_summary" not in result:
                result["assessment_summary"] = "Assessment complete"
            if "completeness_score" not in result:
                result["completeness_score"] = 50
            if "detected_gaps" not in result:
                result["detected_gaps"] = []
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Agent S response: {str(e)}", "Agent S")
            return {
                "error": f"Failed to parse LLM response: {str(e)}", 
                "raw_response": content[:500],
                "assessment_summary": "Error parsing assessment",
                "completeness_score": 0,
                "detected_gaps": []
            }

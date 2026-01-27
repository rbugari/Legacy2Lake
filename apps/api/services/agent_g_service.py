import os
import json
from typing import Dict, Any, List, Optional
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
try:
    from apps.api.services.persistence_service import SupabasePersistence
except ImportError:
    try:
        from services.persistence_service import SupabasePersistence
    except ImportError:
        from .persistence_service import SupabasePersistence


class AgentGService:
    async def _get_llm(self):
        """Resolves LLM client from Agent Matrix (DB)."""
        db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
        
        resolved = await db.resolve_agent_model("agent-g")
        
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

    def __init__(self, tenant_id: Optional[str] = None, client_id: Optional[str] = None):
        self.tenant_id = tenant_id
        self.client_id = client_id

    async def _load_prompt(self, path: str = None) -> str:
        db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
        return await db.get_prompt("agent_g_governance")

    async def save_prompt(self, content: str):
        db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
        await db.save_prompt("agent_g_governance", content)

    async def generate_governance(self, project_name: str, mesh: Dict[str, Any], transformations: List[Dict[str, Any]], metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generates technical documentation (Runbook) and Compliance Audit (JSON)."""
        system_prompt = await self._load_prompt()
        
        human_content = f"""
        PROJECT NAME: {project_name}
        
        PROJECT METADATA (Architect v2.0 Forensics):
        {json.dumps(metadata or {}, indent=2)}

        EXECUTION MESH (Logic Relationships):
        {json.dumps(mesh, indent=2)}
        
        TRANSFORMED CODE (PySpark Logic):
        {json.dumps(transformations, indent=2)}
        
        Please generate the Governance Audit and Runbook. Return ONLY the JSON object.
        """

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_content)
        ]

        llm = await self._get_llm()
        response = await llm.ainvoke(messages)
        content = response.content.strip()

        # Clean JSON if LLM added markdown blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {
                "error": "Failed to parse Agent G response",
                "raw_response": content
            }

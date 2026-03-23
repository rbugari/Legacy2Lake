import os
import json
import re
from typing import Dict, Any, List, Optional
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
try:
    from apps.api.utils.logger import logger
    from apps.api.services.persistence_service import SupabasePersistence
except ImportError:
    try:
        from utils.logger import logger
        from services.persistence_service import SupabasePersistence
    except ImportError:
        from .persistence_service import SupabasePersistence
        # logger might be harder here, but uvicorn should have worked
        from ..utils.logger import logger


class AgentGService:
    def _extract_balanced_object(self, text: str, start_index: int) -> Optional[str]:
        depth = 0
        in_string = False
        escape = False

        for index in range(start_index, len(text)):
            char = text[index]

            if in_string:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == '"':
                    in_string = False
                continue

            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[start_index:index + 1]

        return None

    def _parse_response(self, content: str) -> Dict[str, Any]:
        normalized = content.strip()

        if normalized.startswith("```json"):
            normalized = normalized[len("```json"):].strip()
            if normalized.endswith("```"):
                normalized = normalized[:-3].strip()
        elif normalized.startswith("```"):
            first_newline = normalized.find("\n")
            if first_newline != -1:
                normalized = normalized[first_newline + 1:].strip()
            else:
                normalized = normalized[3:].strip()
            if normalized.endswith("```"):
                normalized = normalized[:-3].strip()

        first_brace = normalized.find("{")
        last_brace = normalized.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            normalized = normalized[first_brace:last_brace + 1]

        for candidate in (normalized, normalized.strip()):
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                try:
                    return json.loads(candidate, strict=False)
                except json.JSONDecodeError:
                    continue

        # Best-effort salvage for partially malformed JSON responses.
        audit_match = re.search(r'"audit_json"\s*:\s*(\{.*\})\s*,\s*"runbook_markdown"', normalized, re.DOTALL)
        runbook_match = re.search(r'"runbook_markdown"\s*:\s*"(.*)"\s*\}\s*$', normalized, re.DOTALL)
        if audit_match and runbook_match:
            try:
                audit_json = json.loads(audit_match.group(1), strict=False)
                runbook_markdown = json.loads(f'"{runbook_match.group(1)}"', strict=False)
                return {
                    "audit_json": audit_json,
                    "runbook_markdown": runbook_markdown,
                }
            except Exception:
                pass

        audit_key = normalized.find('"audit_json"')
        runbook_key = normalized.find('"runbook_markdown"')
        if audit_key != -1 and runbook_key != -1:
            audit_object_start = normalized.find("{", audit_key)
            if audit_object_start != -1:
                audit_object = self._extract_balanced_object(normalized, audit_object_start)
                if audit_object:
                    try:
                        audit_json = json.loads(audit_object, strict=False)
                        runbook_marker = normalized.find(":", runbook_key)
                        if runbook_marker != -1:
                            runbook_raw = normalized[runbook_marker + 1:].strip()
                            if runbook_raw.endswith("}"):
                                runbook_raw = runbook_raw[:-1].rstrip()
                            if runbook_raw.startswith('"') and runbook_raw.endswith('"'):
                                try:
                                    runbook_markdown = json.loads(runbook_raw, strict=False)
                                except json.JSONDecodeError:
                                    runbook_markdown = runbook_raw[1:-1]
                            else:
                                runbook_markdown = runbook_raw
                            return {
                                "audit_json": audit_json,
                                "runbook_markdown": runbook_markdown,
                            }
                    except Exception:
                        pass

        return {
            "error": "Failed to parse Agent G response",
            "raw_response": content
        }

    async def _get_llm(self):
        """Resolves LLM client strictly from Agent Matrix (DB)."""
        db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
        resolved = await db.resolve_agent_model("agent-g")
        
        if not resolved:
            raise ValueError(f"LLM configuration not found for 'agent-g' (Tenant: {self.tenant_id}). Please check Agent Matrix and Provider Vault.")
            
        provider = resolved.get("provider", "azure").lower()
        endpoint = resolved.get("endpoint")
        key = resolved.get("api_key")
        deployment = resolved.get("deployment")
        api_version = resolved.get("api_version")
        temperature = resolved.get("temperature", 0)
            
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

    @logger.llm_debug("Agent G")
    async def generate_governance(self, project_name: str, mesh: Dict[str, Any], transformations: List[Dict[str, Any]], metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generates technical documentation (Runbook) and Compliance Audit (JSON)."""
        system_prompt = await self._load_prompt()
        
        human_content = f"""
        PROJECT NAME: {project_name}
        
        PROJECT METADATA (Architect v2.0 Forensics):
        {json.dumps(metadata or {}, indent=2)}

        EXECUTION MESH (Logic Relationships):
        {json.dumps(mesh, indent=2)}
        
        TRANSFORMED ASSETS AND CODE:
        {json.dumps(transformations, indent=2)}
        
        Please generate the Governance Audit and Runbook. Return ONLY the JSON object.
        """

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_content)
        ]

        llm = await self._get_llm()
        response = await llm.ainvoke(messages)
        return self._parse_response(response.content)

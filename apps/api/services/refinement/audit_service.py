import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

try:
    from apps.api.services.persistence_service import PersistenceService, SupabasePersistence
except ImportError:
    from services.persistence_service import PersistenceService, SupabasePersistence

class AuditService:
    def __init__(self, tenant_id: str = None, client_id: str = None, db_client=None):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.db = db_client
        self.prompt_path = os.path.join(os.path.dirname(__file__), "../../prompts/agent_d_auditor.md")

    async def _get_llm(self):
        """Resolves LLM client from Agent Matrix (DB) or Env Vars."""
        db = SupabasePersistence(tenant_id=self.tenant_id, client_id=self.client_id)
        
        # We reuse agent-f config for AuditService or can use a global one
        resolved = await db.resolve_agent_model("agent-f")
        
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        key = os.getenv("AZURE_OPENAI_API_KEY")
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_ID", "gpt-4")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION")
        provider = "azure"
        
        if resolved:
            provider = resolved.get("provider", "azure")
            if resolved.get("endpoint"): endpoint = resolved.get("endpoint")
            if resolved.get("api_key"): key = resolved.get("api_key")
            if resolved.get("deployment"): deployment = resolved.get("deployment")
            if resolved.get("api_version"): api_version = resolved.get("api_version")
            
        if provider == "azure":
            return AzureChatOpenAI(
                azure_endpoint=endpoint,
                azure_deployment=deployment,
                openai_api_version=api_version,
                api_key=key,
                temperature=0
            )
        else:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=deployment,
                api_key=key,
                base_url=endpoint,
                temperature=0
            )

    def _load_prompt(self) -> str:
        with open(self.prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    async def run_audit(self, project_id: str) -> Dict[str, Any]:
        """Runs a complete audit on all refined files of a project."""
        project_name = project_id
        if "-" in project_id:
             # Try to get project name from DB
             res = self.db.table('utm_projects').select('name').eq('project_id', project_id).execute()
             if res.data:
                 project_name = res.data[0]['name']

        project_path = PersistenceService.ensure_solution_dir(project_name)
        refined_dir = Path(project_path) / "Refined"
        
        if not refined_dir.exists():
            return {"error": "No refined files found to audit."}

        # 1. Collect all code
        audit_content = []
        for root, _, files in os.walk(refined_dir):
            for file in files:
                if file.endswith(".py"):
                    rel_path = os.path.relpath(os.path.join(root, file), refined_dir)
                    with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                        audit_content.append({
                            "file": rel_path,
                            "content": f.read()
                        })

        if not audit_content:
             return {"error": "Project contains folder but no .py files."}

        # 2. Get Column Mappings for context (Security/PII check)
        # We'll fetch mappings to see which columns were marked as PII
        mappings_res = self.db.table('utm_column_mappings').select('*').eq('project_id', project_id).execute()
        pii_columns = [m['source_column'] for m in mappings_res.data if m.get('is_pii')]

        # 3. Call LLM
        system_prompt = self._load_prompt()
        human_content = f"""
        AUDIT TARGET: Project {project_name}
        PII COLUMNS (Must be masked): {json.dumps(pii_columns)}
        
        REFINED CODE:
        {json.dumps(audit_content, indent=2)}
        
        Please provide the Audit JSON report.
        """

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_content)
        ]

        llm = await self._get_llm()
        response = await llm.ainvoke(messages)
        
        try:
            # Cleanup common LLM markdown artifacts
            clean_json = response.content.strip()
            if "```json" in clean_json:
                clean_json = clean_json.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_json:
                clean_json = clean_json.split("```")[1].split("```")[0].strip()
            
            return json.loads(clean_json)
        except Exception as e:
            return {
                "error": "Failed to parse audit report",
                "raw_response": response.content,
                "detail": str(e)
            }

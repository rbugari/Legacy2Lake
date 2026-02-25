import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import shutil

try:
    from apps.api.utils.logger import logger
    from apps.api.services.persistence_service import SupabasePersistence
except ImportError:
    try:
        from utils.logger import logger
        from services.persistence_service import SupabasePersistence
    except ImportError:
        from ...utils.logger import logger
        from .persistence_service import SupabasePersistence


class PromptLabService:
    """Service for Export/Import of prompts for external laboratory optimization."""
    
    AGENT_MAP = {
        "agent-s": "agent_s_scout",
        "agent-a": "agent_a_discovery",
        "agent-c": "agent_c_interpreter",
        "agent-f": "agent_f_critic",
        "agent-g": "agent_g_governance",
        "agent-b": "agent_b_cartographer",
        "agent-d": "agent_d_auditor",
        "agent-p": "agent_p_profiler",
        "agent-r": "agent_r_refactor",
        "agent-o": "agent_o_devops",
        "agent_s": "agent_s_scout",
        "agent_a": "agent_a_discovery"
    }
    
    def __init__(self, tenant_id: Optional[str] = None, client_id: Optional[str] = None):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.db = SupabasePersistence(tenant_id=tenant_id, client_id=client_id)
        self.lab_export_path = os.path.abspath("./prompt_lab_export")
    
    def get_enriched_prompt(
        self,
        agent_name: str,
        origin_tech: Optional[str] = None,
        dest_tech: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Returns an agent prompt enriched with technology-specific best practices.
        """
        # Normalize tech IDs and resolve mapped name
        resolved_name = self.AGENT_MAP.get(agent_name, agent_name)
        origin_id = origin_tech.lower() if origin_tech else None
        dest_id = dest_tech.lower() if dest_tech else None
        
        try:
            # 1. Load base agent prompt
            base_prompt = self._load_agent_prompt(resolved_name)
            
            if not base_prompt:
                logger.warning(f"Base prompt not found for {agent_name}", "PromptLabService")
                return ""
            
            # 2. Load origin knowledge (if specified)
            origin_knowledge = ""
            if origin_id:
                origin_knowledge = self._load_improvements(f"origins/{origin_id}")
            
            # 3. Load destination knowledge (if specified)
            dest_knowledge = ""
            if dest_id:
                dest_knowledge = self._load_improvements(f"destinations/{dest_id}")
            
            # 4. Inject knowledge into prompt
            enriched_prompt = self._inject_knowledge(
                base_prompt=base_prompt,
                origin_knowledge=origin_knowledge,
                dest_knowledge=dest_knowledge,
                origin_tech=origin_id,
                dest_tech=dest_id
            )
            
            logger.info(
                f"Enriched prompt for {agent_name} (origin={origin_tech}, dest={dest_tech})",
                "PromptLabService"
            )
            
            return {
                "prompt": enriched_prompt,
                "base_prompt": base_prompt,
                "origin_knowledge": origin_knowledge,
                "dest_knowledge": dest_knowledge,
                "is_enriched": bool(origin_knowledge or dest_knowledge)
            }
            
        except Exception as e:
            logger.error(f"Error enriching prompt for {agent_name}: {e}", "PromptLabService")
            # Fall back to base prompt
            base = self._load_agent_prompt(agent_name) or ""
            return {
                "prompt": base,
                "base_prompt": base,
                "origin_knowledge": "",
                "dest_knowledge": "",
                "is_enriched": False
            }
    
    def _load_agent_prompt(self, agent_name: str) -> str:
        """Load base agent prompt from prompt_lab_export directory with DB fallback."""
        # 1. Try prompt_lab_export filesystem
        agent_path = os.path.join(self.lab_export_path, "core_agents", agent_name, "prompt_v1.md")
        
        if os.path.exists(agent_path):
            with open(agent_path, "r", encoding="utf-8") as f:
                return f.read()
        
        # 2. Fallback: try to load from database
        # Try both the name provided and its reverse mapping if possible
        lookup_names = [agent_name]
        # If we have a reverse mapping (e.g. agent_s_scout -> agent-s), add it
        reverse_map = {v: k for k, v in self.AGENT_MAP.items()}
        if agent_name in reverse_map:
            lookup_names.append(reverse_map[agent_name])
            
        try:
            # 2.1 Try by prompt_id first (original logic)
            res = self.db.client.table("utm_prompts")\
                .select("content")\
                .eq("is_active", True)\
                .in_("prompt_id", lookup_names)\
                .limit(1)\
                .execute()
            
            if res.data:
                return res.data[0]["content"]
                
            # 2.2 Fallback: Try by agent_id (v4.0 logic)
            # Find the original agent name (e.g. agent-s)
            agent_id = next((k for k, v in self.AGENT_MAP.items() if v == agent_name), agent_name)
            
            res = self.db.client.table("utm_prompts")\
                .select("content")\
                .eq("agent_id", agent_id)\
                .eq("is_active", True)\
                .limit(1)\
                .execute()
            
            if res.data:
                return res.data[0]["content"]

        except Exception as e:
            logger.error(f"Error loading prompt from DB for {agent_name}: {e}", "PromptLabService")
        
        return None
    
    def _load_improvements(self, tech_path: str) -> str:
        """
        Load improvements.md content for a given technology.
        
        Args:
            tech_path: Relative path like 'origins/ssis' or 'destinations/databricks'
            
        Returns:
            Content of improvements.md or empty string if not found
        """
        improvements_path = os.path.join(self.lab_export_path, tech_path, "improvements.md")
        
        if os.path.exists(improvements_path):
            with open(improvements_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            logger.warning(f"Improvements file not found: {improvements_path}", "PromptLabService")
            return ""
    
    def _inject_knowledge(
        self,
        base_prompt: str,
        origin_knowledge: str,
        dest_knowledge: str,
        origin_tech: Optional[str],
        dest_tech: Optional[str]
    ) -> str:
        """
        Injects technology-specific knowledge into the base prompt.
        
        Looks for placeholder patterns in the base prompt:
        - {origin_best_practices}
        - {dest_best_practices}
        - {origin_tech}
        - {dest_tech}
        
        If placeholders aren't found, appends knowledge at the end.
        """
        enriched = base_prompt
        
        # Replace placeholders if they exist
        if "{origin_best_practices}" in enriched and origin_knowledge:
            enriched = enriched.replace("{origin_best_practices}", origin_knowledge)
        elif origin_knowledge:
            # Append origin knowledge
            enriched += f"\n\n---\n\n## Origin Technology Knowledge: {origin_tech.upper()}\n\n{origin_knowledge}"
        
        if "{dest_best_practices}" in enriched and dest_knowledge:
            enriched = enriched.replace("{dest_best_practices}", dest_knowledge)
        elif dest_knowledge:
            # Append destination knowledge
            enriched += f"\n\n---\n\n## Destination Technology Knowledge: {dest_tech.upper()}\n\n{dest_knowledge}"
        
        # Replace simple tech IDs
        if "{origin_tech}" in enriched:
            enriched = enriched.replace("{origin_tech}", origin_tech or "unknown")
        
        if "{dest_tech}" in enriched:
            enriched = enriched.replace("{dest_tech}", dest_tech or "unknown")
        
        return enriched
    
    async def export_to_lab(self, output_dir: str = "./prompt_lab_export") -> Dict[str, Any]:
        """
        Exports all active prompts and technologies to a structured laboratory directory.
        """
        # Ensure base directories
        abs_output_dir = os.path.abspath(output_dir)
        os.makedirs(abs_output_dir, exist_ok=True)
        os.makedirs(os.path.join(abs_output_dir, "_meta"), exist_ok=True)
        os.makedirs(os.path.join(abs_output_dir, "core_agents"), exist_ok=True)
        os.makedirs(os.path.join(abs_output_dir, "origins"), exist_ok=True)
        os.makedirs(os.path.join(abs_output_dir, "destinations"), exist_ok=True)
        
        exported_count = 0
        tech_count = 0
        
        # 1. Export Core Agents (DYNAMIC Discovery)
        try:
            # Fetch all prompts that have metadata (indicating they belong to the lab)
            query = self.db.client.table("utm_prompts").select("prompt_id, metadata, content").eq("is_active", True)
            if self.tenant_id:
                query = query.eq("tenant_id", self.tenant_id)
            
            res = query.execute()
            
            for agent in res.data:
                prompt_id = agent["prompt_id"]
                meta = agent.get("metadata") or {}
                content = agent.get("content")
                
                if not meta or not content:
                    continue
                
                name = meta.get("name", prompt_id)
                category = meta.get("category", "core_agents")
                
                # Agent folder structure
                agent_dir = os.path.join(abs_output_dir, category, prompt_id)
                os.makedirs(agent_dir, exist_ok=True)
                os.makedirs(os.path.join(agent_dir, "examples"), exist_ok=True)
                
                # Write current active prompt
                with open(os.path.join(agent_dir, "prompt_v1.md"), "w", encoding="utf-8") as f:
                    f.write(content)
                
                # Generate contract stub
                contract = self._generate_contract_stub(prompt_id, meta)
                with open(os.path.join(agent_dir, "contract.json"), "w", encoding="utf-8") as f:
                    json.dump(contract, f, indent=2)
                
                # Create initial improvements.md
                with open(os.path.join(agent_dir, "improvements.md"), "w", encoding="utf-8") as f:
                    f.write(f"# Changelog: {name}\n\n")
                    f.write("## Version 1\n")
                    f.write("- Initial version exported from the engine.\n")
                    f.write("- Use this space to document improvements for Version 2.\n")
                
                exported_count += 1
                
        except Exception as e:
            logger.error(f"Error discovering agents: {e}", "LabService")

        # 2. Export Technologies (System Catalog)
        try:
            res = self.db.client.table("utm_system_catalog").select("*").eq("is_active", True).execute()
            for tech in res.data:
                category_dir = "origins" if tech["type"] == "origin" else "destinations"
                tech_id = tech["tech_id"]
                tech_dir = os.path.join(abs_output_dir, category_dir, tech_id)
                os.makedirs(tech_dir, exist_ok=True)
                
                # Write current configuration
                config_v1 = {
                    "tech_id": tech_id,
                    "name": tech["name"],
                    "version": tech.get("version"),
                    "category": tech.get("category"),
                    "config": tech.get("config", {})
                }
                with open(os.path.join(tech_dir, "config_v1.json"), "w", encoding="utf-8") as f:
                    json.dump(config_v1, f, indent=2)
                
                # Write schema if exists
                if tech.get("config_schema"):
                    with open(os.path.join(tech_dir, "schema.json"), "w", encoding="utf-8") as f:
                        json.dump(tech["config_schema"], f, indent=2)

                # Only create improvements.md if it doesn't exist (preserve existing)
                improvements_path = os.path.join(tech_dir, "improvements.md")
                if not os.path.exists(improvements_path):
                    with open(improvements_path, "w", encoding="utf-8") as f:
                        f.write(f"# Changelog: Technology {tech['name']} ({tech_id})\n\n")
                        f.write("## Version 1\n")
                        f.write("- Current engine configuration exported.\n")
                        f.write("- Optimize the 'config' object for better engine interpretation.\n")
                
                tech_count += 1

        except Exception as e:
            logger.error(f"Error exporting technologies: {e}", "LabService")
        
        # Write Instructions README
        self._write_readme(abs_output_dir)
        
        # Export metadata
        export_info = {
            "export_timestamp": datetime.now().isoformat(),
            "tenant_id": self.tenant_id or "default",
            "prompts_count": exported_count,
            "tech_count": tech_count,
            "lab_version": "1.1",
            "status": "ready_for_optimization"
        }
        
        with open(os.path.join(abs_output_dir, "_meta", "export_info.json"), "w") as f:
            json.dump(export_info, f, indent=2)

        # 3. Create ZIP Archive
        zip_base_name = os.path.join(os.path.dirname(abs_output_dir), "prompt_lab_export")
        zip_path = shutil.make_archive(zip_base_name, 'zip', abs_output_dir)
        
        return {
            "status": "success",
            "exported_count": exported_count,
            "tech_count": tech_count,
            "output_path": abs_output_dir,
            "zip_path": zip_path
        }
    
    def _generate_contract_stub(self, prompt_id: str, meta: Dict) -> Dict:
        """Generates a basic contract stub for the prompt."""
        return {
            "contract_id": meta["contract_id"],
            "version": 1,
            "description": f"Output contract for {meta['name']}",
            "immutable_schema": {
                "type": "object",
                "notes": "Define the expected JSON output schema here."
            }
        }
    
    def _write_readme(self, output_dir: str):
        """Generates README.md with guidance for external IAs."""
        content = """# Prompt Laboratory: Guidelines for External IAs

## 🎯 Goal
Optimize the prompts in this directory to improve the accuracy and efficiency of the Legacy2Lake engine.

## 🚨 Rules
1. **Maintain Contracts**: DO NOT alter `contract.json`. The engine expects specific JSON structures.
2. **Document Everything**: Record all changes in `improvements.md`.
3. **Save as v2**: Keep `prompt_v1.md` as reference and save optimizations as `prompt_v2.md`.

## 📁 Workflow
- **Step 1**: Analyze `prompt_v1.md` and `contract.json`.
- **Step 2**: Create `prompt_v2.md` with your improvements.
- **Step 3**: Describe your changes in `improvements.md`.
- **Step 4**: Return the updated folder structure for import.
"""
        with open(os.path.join(output_dir, "README.md"), "w", encoding="utf-8") as f:
            f.write(content)
    
    async def import_from_lab(self, prompt_id: str, lab_path: str) -> Dict[str, Any]:
        """
        Imports an optimized prompt or tech config from the lab as a new version.
        """
        try:
            abs_lab_path = os.path.abspath(lab_path)
            
            # 1. Check if it's a Core Agent (Markdown)
            v2_path = os.path.join(abs_lab_path, "prompt_v2.md")
            if os.path.exists(v2_path):
                return await self._import_core_prompt(prompt_id, abs_lab_path)
            
            # 2. Check if it's a Technology Config (JSON)
            config_v2_path = os.path.join(abs_lab_path, "config_v2.json")
            if os.path.exists(config_v2_path):
                return await self._import_tech_config(prompt_id, abs_lab_path)
            
            return {"status": "error", "message": "No v2 optimization file (prompt_v2.md or config_v2.json) found in directory."}
            
        except Exception as e:
            logger.error(f"Import error for {prompt_id}: {e}", "LabService")
            return {"status": "error", "message": str(e)}

    async def _import_core_prompt(self, prompt_id: str, abs_lab_path: str) -> Dict[str, Any]:
        """Handles import of seasonal markdown prompts."""
        v2_path = os.path.join(abs_lab_path, "prompt_v2.md")
        imp_path = os.path.join(abs_lab_path, "improvements.md")
        
        if not os.path.exists(imp_path):
            return {"status": "error", "message": "Changelog (improvements.md) not found in directory."}
            
        with open(v2_path, "r", encoding="utf-8") as f:
            new_content = f.read()
            
        with open(imp_path, "r", encoding="utf-8") as f:
            changelog = f.read()
        
        # Get next version number
        res = self.db.client.table("utm_prompts").select("version_number").eq("prompt_id", prompt_id).order("version_number", desc=True).limit(1).execute()
        
        next_v = 1
        if res.data:
            next_v = res.data[0]["version_number"] + 1
        
        # Create new version (INACTIVE)
        data = {
            "tenant_id": self.tenant_id,
            "prompt_id": prompt_id,
            "version_number": next_v,
            "content": new_content,
            "changelog": changelog,
            "is_active": False,
            "created_by": "lab_import"
        }
        
        self.db.client.table("utm_prompts").insert(data).execute()
        
        return {
            "status": "success", 
            "new_version": next_v,
            "message": f"Successfully imported core {prompt_id} version {next_v}."
        }

    async def _import_tech_config(self, tech_id: str, abs_lab_path: str) -> Dict[str, Any]:
        """Handles import of optimized technology JSON configurations."""
        v2_path = os.path.join(abs_lab_path, "config_v2.json")
        imp_path = os.path.join(abs_lab_path, "improvements.md")
        
        with open(v2_path, "r", encoding="utf-8") as f:
            new_data = json.load(f)
            
        new_config = new_data.get("config")
        if not new_config:
             return {"status": "error", "message": "JSON must contain a 'config' object."}

        # Update the system catalog directly (or we could use a staging approach, but for now direct update)
        # Note: We keep tech_id in catalog unique.
        res = self.db.client.table("utm_system_catalog").update({
            "config": new_config,
            "updated_at": datetime.now().isoformat()
        }).eq("tech_id", tech_id).execute()
        
        if not res.data:
            return {"status": "error", "message": f"Technology {tech_id} not found in catalog."}

        return {
            "status": "success",
            "message": f"Successfully updated configuration for {tech_id} from laboratory."
        }
            
    async def activate_version(self, prompt_id: str, version: int) -> Dict[str, Any]:
        """
        Activates a specific version of a prompt (Blue-Green deployment).
        """
        try:
            # 1. Deactivate old version
            self.db.client.table("utm_prompts").update({"is_active": False})\
                .eq("prompt_id", prompt_id).eq("is_active", True).execute()
                
            # 2. Activate new version
            res = self.db.client.table("utm_prompts").update({"is_active": True})\
                .eq("prompt_id", prompt_id).eq("version_number", version).execute()
                
            if not res.data:
                return {"status": "error", "message": f"Version {version} for {prompt_id} not found."}
                
            logger.info(f"Successfully activated {prompt_id} v{version}", "LabService")
            return {"status": "success", "active_version": version}
            
        except Exception as e:
            logger.error(f"Activation error for {prompt_id} v{version}: {e}", "LabService")
            return {"status": "error", "message": str(e)}

    async def list_versions(self, prompt_id: str) -> List[Dict[str, Any]]:
        """Lists all versions for a prompt."""
        res = self.db.client.table("utm_prompts")\
            .select("version_number, is_active, changelog, created_at")\
            .eq("prompt_id", prompt_id)\
            .order("version_number", desc=True)\
            .execute()
        return res.data or []

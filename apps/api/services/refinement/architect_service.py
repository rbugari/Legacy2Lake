
import os
import shutil
from pathlib import Path
import json
import datetime

try:
    from apps.api.services.persistence_service import PersistenceService, SupabasePersistence
    from apps.api.services.knowledge_service import KnowledgeService
except ImportError:
    try:
        from services.persistence_service import PersistenceService, SupabasePersistence
        from services.knowledge_service import KnowledgeService
    except ImportError:
        from ..persistence_service import PersistenceService, SupabasePersistence
        from ..knowledge_service import KnowledgeService

class ArchitectService:
    def __init__(self, tenant_id: str = None, client_id: str = None):
        self.tenant_id = tenant_id
        self.client_id = client_id

    def _log(self, log: list, msg: str, level: str = "Architect", model: str = "Medallion Mapper"):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log.append(f"[{timestamp}] [{level}] [{model}] {msg}")

    async def refine_project(self, project_id: str, profile_metadata: dict, log: list = None, project_name: str = None) -> dict:
        """
        Segments Code into Medallion Architecture (Bronze/Silver/Gold).
        Generates config.py and utils.py.
        """
        if log is None: log = []
        
        storage = PersistenceService.get_storage()
        # [Fix] Use project_name for R2 paths if provided
        folder_id = project_name or project_id
        base_path = PersistenceService.ensure_solution_dir(folder_id, tenant_id=self.tenant_id)
        input_dir = f"{base_path.rstrip('/')}/{PersistenceService.STAGE_DRAFTING}"
        output_dir = f"{base_path.rstrip('/')}/{PersistenceService.STAGE_REFINEMENT}"
        
        self._log(log, f"Solutions Directory (R2): {base_path}")
        
        # Release 2.0: Fetch Design Registry
        db = SupabasePersistence(tenant_id=self.tenant_id)
        # Release 3.0: Cartridge Pattern
        from .cartridges.factory import CartridgeFactory
        from ..knowledge_service import KnowledgeService
        
        # Release 3.0: Fetch and Flatten Registry
        registry_list = await db.get_design_registry(project_id)
        
        defaults = KnowledgeService.get_default_registry_entries(project_id)
        existing_keys = set()
        for r in registry_list:
             cat = r.get('category') if isinstance(r, dict) else r.category
             key = r.get('key') if isinstance(r, dict) else r.key
             existing_keys.add((str(cat).upper(), str(key)))
             
        missing_defaults = []
        for d in defaults:
            d_cat = str(d['category']).upper()
            d_key = str(d['key'])
            if (d_cat, d_key) not in existing_keys:
                missing_defaults.append(d)

        if missing_defaults:
            registry_list.extend(missing_defaults)
            
        registry = KnowledgeService.flatten_knowledge(registry_list)
        
        cartridge = CartridgeFactory.get_cartridge(project_id, registry)
        self._log(log, f"Using Cartridge: {cartridge.__class__.__name__}")

        # Logical Medallion Structure (Lowercase)
        bronze_prefix = f"{output_dir.rstrip('/')}/bronze"
        silver_prefix = f"{output_dir.rstrip('/')}/silver"
        gold_prefix = f"{output_dir.rstrip('/')}/gold"
        
        self._log(log, "Ensuring Medallion folder structure (bronze/silver/gold)...")
        # In R2 we don't need to physically create folders.

        refined_files = {
            "bronze": [],
            "silver": [],
            "gold": [],
            "config": [],
            "utils": []
        }

        # 1. Generate Shared Scaffolding
        scaffolding = cartridge.generate_scaffolding()
        for filename, content in scaffolding.items():
            file_key = f"{output_dir.rstrip('/')}/{filename}"
            storage.save_file(file_key, content)
            
            # Categorize known files
            if "config" in filename: refined_files["config"].append(file_key)
            elif "utils" in filename: refined_files["utils"].append(file_key)
            else: refined_files["config"].append(file_key) # Fallback
            
            self._log(log, f"Generated Scaffolding: {filename}")

        # 2. Process each analyzed file
        files_to_process = profile_metadata.get("analyzed_files", [])
        self._log(log, f"Processing {len(files_to_process)} source files with {cartridge.get_file_extension()} extension...")
        
        for filename in files_to_process:
            file_key = f"{input_dir.rstrip('/')}/{filename}"
            
            original_code = storage.read_file(file_key)
            if not original_code:
                self._log(log, f"WARNING: File skipped (not found in R2): {filename}", level="Architect", model="System")
                continue
            
            if isinstance(original_code, bytes):
                original_code = original_code.decode("utf-8")

            table_metadata = {
                "source_path": filename,
                "original_code": original_code,
                "output_table_name": None,
                "pk_columns": profile_metadata.get("primary_keys", {}).get(filename, ["id"]),
                "table_type": profile_metadata.get("table_metadata", {}).get(filename, {}).get("type", "DIMENSION")
            }
            
            # Determine base filename and extension
            ext = cartridge.get_file_extension()
            clean_name = filename.replace(ext, "").replace(".py", "") # Support .dtsx or .py source
            base_filename = f"{clean_name}"

            # 1. Bronze Layer
            bronze_code = cartridge.generate_bronze(table_metadata)
            bronze_key = f"{bronze_prefix}/{base_filename}_bronze{ext}"
            storage.save_file(bronze_key, bronze_code)
            refined_files["bronze"].append(bronze_key)
            
            # 2. Silver Layer
            silver_code = cartridge.generate_silver(table_metadata)
            silver_key = f"{silver_prefix}/{base_filename}_silver{ext}"
            storage.save_file(silver_key, silver_code)
            refined_files["silver"].append(silver_key)
            
            # 3. Gold Layer
            gold_code = cartridge.generate_gold(table_metadata)
            gold_key = f"{gold_prefix}/{base_filename}_gold{ext}"
            storage.save_file(gold_key, gold_code)
            refined_files["gold"].append(gold_key)

            self._log(log, f"Refined {filename} into Bronze, Silver, and Gold layers.")
            

        # 3. Generate Orchestration (Release 3.5)
        # Prepare full list of processed metadata for the orchestrator
        all_metadata = []
        for filename in files_to_process:
             clean_name = filename.replace(".py", "")
             all_metadata.append({
                 "source_path": filename,
                 "table_name": clean_name
             })

        orch_content = cartridge.generate_orchestration(all_metadata)
        if orch_content:
            orch_filename = "orchestration_dag" if ".py" in cartridge.get_file_extension() else "orchestration_pipeline"
            orch_ext = ".py" if "airflow" in orch_content.lower() else ".json"
            orch_key = f"{output_dir.rstrip('/')}/Orchestration/{orch_filename}{orch_ext}"
            
            storage.save_file(orch_key, orch_content)
            
            refined_files["orchestration"] = [orch_key]
            self._log(log, f"Generated Orchestration: {orch_filename}{orch_ext}")

        return {
            "status": "COMPLETED",
            "refined_files": refined_files,
            "cartridge": cartridge.__class__.__name__
        }

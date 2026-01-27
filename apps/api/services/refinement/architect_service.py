
import os
import shutil
from pathlib import Path
import json

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
    def __init__(self):
        pass

    async def refine_project(self, project_id: str, profile_metadata: dict, log: list = None) -> dict:
        """
        Segments Code into Medallion Architecture (Bronze/Silver/Gold).
        Generates config.py and utils.py.
        """
        if log is None: log = []
        
        base_path = PersistenceService.ensure_solution_dir(project_id)
        project_path = Path(base_path)
        input_dir = project_path / PersistenceService.STAGE_DRAFTING
        output_dir = project_path / PersistenceService.STAGE_REFINEMENT
        
        log.append(f"[Architect] Solutions Directory: {base_path}")
        
        # Release 2.0: Fetch Design Registry
        db = SupabasePersistence()
        # Release 3.0: Cartridge Pattern
        from .cartridges.factory import CartridgeFactory
        from ..knowledge_service import KnowledgeService
        
        # Release 3.0: Fetch and Flatten Registry
        registry_list = await db.get_design_registry(project_id)
        # We must flatten it because Factory expects {category: {key: value}}
        # Note: KnowledgeService might need to merge defaults here too if not already persisted?
        # Ideally persistence handles defaults on read, but main.py has that logic now.
        # Let's rely on what's in DB for now, assuming defaults are persisted.
        # Wait, if main.py merges defaults on READ but doesn't persist them unless saved, 
        # then we might miss defaults here if they aren't in DB.
        # But get_design_registry in PersistenceService has a call to initialize if empty.
        # However, new keys like target_stack might be missing if we don't merge defaults here too.
        # Best practice: Re-use the merge logic or rely on DB being up to date.
        # For safety, let's merge defaults here as well.
        
        defaults = KnowledgeService.get_default_registry_entries(project_id)
        existing_keys = set()
        for r in registry_list:
             cat = r.get('category') if isinstance(r, dict) else r.category
             key = r.get('key') if isinstance(r, dict) else r.key
             # Normalize for comparison
             existing_keys.add((str(cat).upper(), str(key)))
             
        # Check defaults with normalized keys
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
        log.append(f"[Architect] Using Cartridge: {cartridge.__class__.__name__}")

        # Create Medallion Structure
        bronze_dir = output_dir / "Bronze"
        silver_dir = output_dir / "Silver"
        gold_dir = output_dir / "Gold"
        
        log.append("[Architect] Ensuring Medallion folder structure (Bronze/Silver/Gold)...")
        for d in [bronze_dir, silver_dir, gold_dir]:
            d.mkdir(parents=True, exist_ok=True)

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
            file_path = output_dir / filename
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            # Categorize known files, others go to config/utils generic bucket or ignored
            if "config" in filename: refined_files["config"].append(str(file_path))
            elif "utils" in filename: refined_files["utils"].append(str(file_path))
            else: refined_files["config"].append(str(file_path)) # Fallback
            
            log.append(f"[Architect] Generated Scaffolding: {filename}")

        # 2. Process each analyzed file
        files_to_process = profile_metadata.get("analyzed_files", [])
        log.append(f"[Architect] Processing {len(files_to_process)} source files with {cartridge.get_file_extension()} extension...")
        
        ext = cartridge.get_file_extension()
        
        for filename in files_to_process:
            file_path = input_dir / filename
            if not file_path.exists():
                log.append(f"[Architect] WARNING: File skipped (not found): {filename}")
                continue
            
            # Read original code/metadata
            with open(file_path, "r", encoding="utf-8") as f:
                original_code = f.read()

            table_metadata = {
                "source_path": filename,
                "original_code": original_code,
                "output_table_name": None, # Let cartridge decide or extract
                "pk_columns": profile_metadata.get("primary_keys", {}).get(filename, ["id"]),
                "table_type": profile_metadata.get("table_metadata", {}).get(filename, {}).get("type", "DIMENSION")
            }
            if isinstance(table_metadata["pk_columns"], str): table_metadata["pk_columns"] = [table_metadata["pk_columns"]]

            
            # Bronze Generation
            # Suffix logic should be handled here or inside cartridge? 
            # Cartridge returns CONTENT. We decide filename.
            # Standard: source_bronze.ext
            bronze_name = filename.replace(".py", f"_bronze{ext}")
            bronze_code = cartridge.generate_bronze(table_metadata)
            
            with open(bronze_dir / bronze_name, "w", encoding="utf-8") as f:
                f.write(bronze_code)
            refined_files["bronze"].append(str(bronze_dir / bronze_name))
            
            # Silver Generation
            # Naming conventions are handled INSIDE cartridge for table names, but filenames we control?
            # Actually, `silver_prefix` is inside cartridge logic.
            # Let's align filenames with table names if possible, but for now simple mapping:
            clean_name = filename.replace(".py", "")
            silver_prefix = registry.get("naming", {}).get("silver_prefix", "stg_")
            silver_name = f"{silver_prefix}{clean_name}{ext}"
            
            # Update metadata for Silver
            table_metadata["output_table_name"] = f"{silver_prefix}{clean_name}"
            silver_code = cartridge.generate_silver(table_metadata)
            
            with open(silver_dir / silver_name, "w", encoding="utf-8") as f:
                f.write(silver_code)
            refined_files["silver"].append(str(silver_dir / silver_name))
            
            # Gold Generation
            gold_prefix = registry.get("naming", {}).get("gold_prefix", "dim_")
            gold_name = f"{gold_prefix}{clean_name}{ext}"
             
            table_metadata["output_table_name"] = f"{gold_prefix}{clean_name}"
            gold_code = cartridge.generate_gold(table_metadata)
            
            with open(gold_dir / gold_name, "w", encoding="utf-8") as f:
                f.write(gold_code)
            refined_files["gold"].append(str(gold_dir / gold_name))

            # [Release 2.1] SQL Generation (Dual Output)
            # If cartridge supports SQL generation, write .sql files alongside .py
            
            # Bronze SQL
            if hasattr(cartridge, "generate_bronze_sql"):
                sql_content = cartridge.generate_bronze_sql(table_metadata)
                sql_name = bronze_name.replace(ext, ".sql")
                with open(bronze_dir / sql_name, "w", encoding="utf-8") as f:
                     f.write(sql_content)
                refined_files["bronze"].append((bronze_dir / sql_name).as_posix())

            # Silver SQL
            if hasattr(cartridge, "generate_silver_sql"):
                sql_content = cartridge.generate_silver_sql(table_metadata)
                sql_name = silver_name.replace(ext, ".sql")
                with open(silver_dir / sql_name, "w", encoding="utf-8") as f:
                     f.write(sql_content)
                refined_files["silver"].append((silver_dir / sql_name).as_posix())

                refined_files["gold"].append((gold_dir / sql_name).as_posix())

        # 3. Generate Orchestration (Release 3.5)
        orchestration_dir = output_dir / "Orchestration"
        orchestration_dir.mkdir(parents=True, exist_ok=True)
        
        # Prepare full list of processed metadata for the orchestrator
        # We need to reconstruct or store them during the loop.
        # For simplicity infra for now, we'll re-scan or use a list.
        # Let's use a simplified list from what we just processed.
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
            # Add proper extension based on content? 
            # For now, if "import airflow" is in it, use .py, else .json
            orch_ext = ".py" if "airflow" in orch_content.lower() else ".json"
            orch_path = orchestration_dir / f"{orch_filename}{orch_ext}"
            
            with open(orch_path, "w", encoding="utf-8") as f:
                f.write(orch_content)
            
            refined_files["orchestration"] = [str(orch_path)]
            log.append(f"[Architect] Generated Orchestration: {orch_path.name}")

        return {
            "status": "COMPLETED",
            "refined_files": refined_files
        }



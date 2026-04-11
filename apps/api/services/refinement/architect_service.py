
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

    def _resolve_processing_units(self, profile_metadata: dict, execution_mode: str = "structured_refinement") -> list:
        if execution_mode == "intelligent_reengineering":
            reengineering_units = profile_metadata.get("reengineering_units") or []
            if reengineering_units:
                consolidation_units = [
                    unit for unit in reengineering_units
                    if unit.get("is_consolidation_candidate")
                ]
                if consolidation_units:
                    return consolidation_units

        refinement_units = profile_metadata.get("refinement_units") or []
        if refinement_units:
            return refinement_units

        fallback_units = []
        for filename in profile_metadata.get("analyzed_files", []):
            fallback_units.append({
                "unit_name": filename.rsplit(".", 1)[0],
                "output_table_name": filename.rsplit(".", 1)[0],
                "source_files": [filename],
                "pk_columns": profile_metadata.get("primary_keys", {}).get(filename, ["id"]),
                "table_type": profile_metadata.get("table_metadata", {}).get(filename, {}).get("type", "DIMENSION"),
                "reuse_strategy": "single_source",
            })
        return fallback_units

    def _build_unit_payload(self, processing_unit: dict, profile_metadata: dict, storage, input_dir: str):
        source_files = processing_unit.get("source_files") or []
        combined_sources = []
        existing_sources = []

        for source_file in source_files:
            file_key = f"{input_dir.rstrip('/')}/{source_file}"
            original_code = storage.read_file(file_key)
            if not original_code:
                continue
            if isinstance(original_code, bytes):
                original_code = original_code.decode("utf-8")
            existing_sources.append(source_file)
            combined_sources.append(
                f"# ================= SOURCE: {source_file} =================\n{original_code.strip()}\n"
            )

        if not existing_sources:
            return None

        logical_name = processing_unit.get("output_table_name") or processing_unit.get("unit_name") or Path(existing_sources[0]).stem
        source_suffix = Path(existing_sources[0]).suffix or ".py"

        return {
            "unit_name": processing_unit.get("unit_name", logical_name),
            "base_filename": logical_name,
            "table_metadata": {
                "source_path": f"{logical_name}{source_suffix}",
                "source_files": existing_sources,
                "original_code": "\n\n".join(combined_sources),
                "output_table_name": logical_name,
                "pk_columns": processing_unit.get("pk_columns") or profile_metadata.get("unit_primary_keys", {}).get(logical_name) or ["id"],
                "table_type": processing_unit.get("table_type", "DIMENSION"),
                "refinement_strategy": processing_unit.get("reuse_strategy", "single_source"),
            },
        }

    def _build_reengineering_manifest_entry(self, processing_unit: dict, table_metadata: dict, output_assets: dict) -> dict:
        return {
            "unit_name": processing_unit.get("unit_name") or table_metadata.get("output_table_name"),
            "target_asset_name": processing_unit.get("target_asset_name") or table_metadata.get("output_table_name"),
            "contributing_sources": table_metadata.get("source_files", []),
            "reuse_strategy": processing_unit.get("reuse_strategy", "bounded_enhancement"),
            "consolidation_rationale": "Consolidation applied only because multiple drafted packages/files share the same logical source object.",
            "generated_assets": output_assets,
            "traceability_notes": "Each generated asset includes explicit source references in metadata and manifest.",
        }

    async def refine_project(self, project_id: str, profile_metadata: dict, log: list = None, project_name: str = None, target_tech: str = None, execution_mode: str = "structured_refinement") -> dict:
        """
        Segments Code into Medallion Architecture (Bronze/Silver/Gold).
        Generates config.py and utils.py.
        """
        print(f"[ARCHITECT DEBUG] === refine_project() INVOKED ===")
        print(f"[ARCHITECT DEBUG] project_id: {project_id}")
        print(f"[ARCHITECT DEBUG] project_name: {project_name}")
        print(f"[ARCHITECT DEBUG] profile_metadata keys: {profile_metadata.keys() if profile_metadata else 'None'}")
        
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
        
        cartridge = CartridgeFactory.get_cartridge(project_id, registry, tenant_id=self.tenant_id, target_tech=target_tech)
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
            "utils": [],
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

        # 2. Process units according to execution mode.
        processing_units = self._resolve_processing_units(profile_metadata, execution_mode=execution_mode)
        print(f"[ARCHITECT DEBUG] processing_units: {processing_units}")
        print(f"[ARCHITECT DEBUG] About to process {len(processing_units)} refinement units")
        self._log(log, f"Processing {len(processing_units)} units in mode={execution_mode} with {cartridge.get_file_extension()} extension...")

        reengineering_manifest = []

        for processing_unit in processing_units:
            unit_name = processing_unit.get("unit_name") or "refined_asset"
            source_files = processing_unit.get("source_files") or []
            print(f"[ARCHITECT DEBUG] === Processing refinement unit: {unit_name} ===")
            print(f"[ARCHITECT DEBUG] source_files: {source_files}")

            unit_payload = self._build_unit_payload(processing_unit, profile_metadata, storage, input_dir)
            if not unit_payload:
                self._log(log, f"WARNING: Refinement unit skipped (no readable source files): {unit_name}", level="Architect", model="System")
                continue

            table_metadata = unit_payload["table_metadata"]
            base_filename = unit_payload["base_filename"]
            ext = cartridge.get_file_extension()
            trace_header = ""
            if execution_mode == "intelligent_reengineering":
                trace_header = "\n".join([
                    "# --- REENGINEERING TRACEABILITY ---",
                    f"# Unit: {processing_unit.get('unit_name', base_filename)}",
                    f"# Sources: {', '.join(table_metadata.get('source_files', []))}",
                    "# -----------------------------------",
                    "",
                ])

            # 1. Bronze Layer
            print(f"[ARCHITECT DEBUG] Generating bronze for {unit_name}...")
            bronze_code = (trace_header + (cartridge.generate_bronze(table_metadata) or "")) if execution_mode == "intelligent_reengineering" else cartridge.generate_bronze(table_metadata)
            print(f"[ARCHITECT DEBUG] Bronze code length: {len(bronze_code) if bronze_code else 0}")
            bronze_key = f"{bronze_prefix}/{base_filename}_bronze{ext}"
            print(f"[ARCHITECT DEBUG] Saving bronze to: {bronze_key}")
            try:
                storage.save_file(bronze_key, bronze_code)
                print(f"[ARCHITECT DEBUG] ✅ Bronze saved successfully")
                refined_files["bronze"].append(bronze_key)
            except Exception as e:
                print(f"[ARCHITECT DEBUG] ❌ Bronze save FAILED: {e}")
                import traceback
                traceback.print_exc()
                raise
            
            # 2. Silver Layer
            print(f"[ARCHITECT DEBUG] Generating silver for {unit_name}...")
            silver_code = (trace_header + (cartridge.generate_silver(table_metadata) or "")) if execution_mode == "intelligent_reengineering" else cartridge.generate_silver(table_metadata)
            print(f"[ARCHITECT DEBUG] Silver code length: {len(silver_code) if silver_code else 0}")
            silver_key = f"{silver_prefix}/{base_filename}_silver{ext}"
            print(f"[ARCHITECT DEBUG] Saving silver to: {silver_key}")
            try:
                storage.save_file(silver_key, silver_code)
                print(f"[ARCHITECT DEBUG] ✅ Silver saved successfully")
                refined_files["silver"].append(silver_key)
            except Exception as e:
                print(f"[ARCHITECT DEBUG] ❌ Silver save FAILED: {e}")
                import traceback
                traceback.print_exc()
                raise
            
            # 3. Gold Layer
            print(f"[ARCHITECT DEBUG] Generating gold for {unit_name}...")
            gold_code = (trace_header + (cartridge.generate_gold(table_metadata) or "")) if execution_mode == "intelligent_reengineering" else cartridge.generate_gold(table_metadata)
            print(f"[ARCHITECT DEBUG] Gold code length: {len(gold_code) if gold_code else 0}")
            gold_key = f"{gold_prefix}/{base_filename}_gold{ext}"
            print(f"[ARCHITECT DEBUG] Saving gold to: {gold_key}")
            try:
                storage.save_file(gold_key, gold_code)
                print(f"[ARCHITECT DEBUG] ✅ Gold saved successfully")
                refined_files["gold"].append(gold_key)
            except Exception as e:
                print(f"[ARCHITECT DEBUG] ❌ Gold save FAILED: {e}")
                import traceback
                traceback.print_exc()
                raise

            print(f"[ARCHITECT DEBUG] === Completed processing {unit_name} ===")
            self._log(log, f"Refined unit {unit_name} from {len(source_files)} source file(s) into reusable Bronze, Silver, and Gold layers.")

            if execution_mode == "intelligent_reengineering":
                reengineering_manifest.append(
                    self._build_reengineering_manifest_entry(
                        processing_unit,
                        table_metadata,
                        {
                            "bronze": bronze_key,
                            "silver": silver_key,
                            "gold": gold_key,
                        },
                    )
                )
            

        # 3. Generate Orchestration (Release 3.5)
        # Prepare full list of processed metadata for the orchestrator
        all_metadata = []
        for processing_unit in processing_units:
             unit_name = processing_unit.get("output_table_name") or processing_unit.get("unit_name")
             if not unit_name:
                 continue
             all_metadata.append({
                 "source_path": unit_name,
                 "table_name": unit_name
             })

        manifest_name = "reengineering_manifest.json" if execution_mode == "intelligent_reengineering" else "refinement_manifest.json"
        manifest_key = f"{output_dir.rstrip('/')}/{manifest_name}"
        manifest_objective = (
            "Consolidate Drafting outputs into project-scoped medallion layers only when multiple drafted packages/files share the same logical source object."
            if execution_mode == "intelligent_reengineering"
            else "Consolidate Drafting outputs into reusable ELT-oriented refinement units instead of naively splitting each package into three layers."
        )
        storage.save_file(manifest_key, json.dumps({
            "generated_at": datetime.datetime.now().isoformat(),
            "execution_mode": execution_mode,
            "processing_units": processing_units,
            "reengineering_summary": reengineering_manifest,
            "objective": manifest_objective,
        }, indent=2))
        refined_files["manifest"] = [manifest_key]

        orch_content = cartridge.generate_orchestration(all_metadata)
        if orch_content:
            orch_filename = "orchestration_dag" if ".py" in cartridge.get_file_extension() else "orchestration_pipeline"
            orch_ext = ".py" if "airflow" in orch_content.lower() else ".json"
            orch_key = f"{output_dir.rstrip('/')}/Orchestration/{orch_filename}{orch_ext}"
            
            storage.save_file(orch_key, orch_content)
            
            refined_files["orchestration"] = [orch_key]
            self._log(log, f"Generated Orchestration: {orch_filename}{orch_ext}")

        print(f"[ARCHITECT DEBUG] === refine_project() COMPLETED ===")
        print(f"[ARCHITECT DEBUG] refined_files: {refined_files}")
        print(f"[ARCHITECT DEBUG] Total bronze: {len(refined_files.get('bronze', []))}")
        print(f"[ARCHITECT DEBUG] Total silver: {len(refined_files.get('silver', []))}")
        print(f"[ARCHITECT DEBUG] Total gold: {len(refined_files.get('gold', []))}")
        
        return {
            "status": "COMPLETED",
            "refined_files": refined_files,
            "cartridge": cartridge.__class__.__name__,
            "execution_mode": execution_mode,
        }

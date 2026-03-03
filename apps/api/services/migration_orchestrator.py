import os
import json
import asyncio
from typing import Dict, Any, List
from datetime import datetime

# Import all agents
from apps.api.services.librarian_service import LibrarianService
from apps.api.services.topology_service import TopologyService
from apps.api.services.agent_c_service import AgentCService
from apps.api.services.agent_f_service import AgentFService
from apps.api.services.agent_g_service import AgentGService

from apps.api.services.persistence_service import PersistenceService, SupabasePersistence
try:
    from apps.api.utils.logger import logger
except ImportError:
    try:
        from utils.logger import logger
    except ImportError:
        from ..utils.logger import logger

class MigrationOrchestrator:
    """
    The Director: Manages the end-to-end migration lifecycle.
    Orchestrates the hand-offs between Librarian, Topology, Developer, and Compliance agents.
    """

    def __init__(self, project_id: str, project_uuid: str = None, tenant_id: str = None, client_id: str = None):

        self.project_id = project_id # This acts as Project Name / Folder Name
        self.project_uuid = project_uuid or project_id # Fallback if not provided
        self.tenant_id = tenant_id
        
        # Persistence Service handles paths
        self.base_path = PersistenceService.ensure_solution_dir(project_id, tenant_id=tenant_id)
        self.output_path = f"{self.base_path.rstrip('/')}/{PersistenceService.STAGE_DRAFTING}"
        self.storage = PersistenceService.get_storage()
        
        # Load Platform Spec
        # For config files that are part of the app, we can still use local or read via resource.
        # But for project artifacts, we use storage.
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.spec_path = os.path.join(base_dir, "config", "platform_spec.json")
        try:
            with open(self.spec_path, "r") as f:
                self.platform_spec = json.load(f)
        except FileNotFoundError:
            self.spec_path = os.path.abspath(os.path.join("apps", "api", "config", "platform_spec.json"))
            with open(self.spec_path, "r") as f:
                self.platform_spec = json.load(f)

        # Initialize Agents
        self.librarian = LibrarianService(project_id, tenant_id=tenant_id)
        self.topology = TopologyService(project_id, tenant_id=tenant_id)
        self.agent_c = AgentCService(tenant_id=tenant_id, client_id=client_id)
        self.agent_f = AgentFService(tenant_id=tenant_id, client_id=client_id)
        self.persistence = SupabasePersistence(tenant_id=tenant_id, client_id=client_id)

        
        # Log Persistence
        self.log_file = os.path.join(self.base_path, "migration.log")

    async def _log_persistence(self, message: str, step: str = "SYSTEM"):
        """Persists a message to the database log and cloud storage log."""
        # Use UUID for DB logging if possible
        target_id = self.project_uuid if len(str(self.project_uuid)) > 30 else self.project_id
        await self.persistence.log_execution(target_id, "MIGRATION", message, step=step)
        
        # Storage Persistence
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_msg = f"[{now}] [{step.upper()}] {message}"
        
        try:
            log_key = f"{self.base_path.rstrip('/')}/migration.log"
            # In a real environment, we'd append. R2/S3 doesn't support append efficiently.
            # We fetch, append, and re-save, or just keep a local buffer for the session.
            # For simplicity in this session, we'll try to keep it cloud-safe.
            # However, for performance, we might just write the final log at the end or use a buffer.
            # Let's use a simpler approach: try to read-append-write if small.
            existing = ""
            try: 
                existing_bytes = self.storage.read_file(log_key)
                existing = existing_bytes.decode("utf-8") if existing_bytes else ""
            except: pass
            
            self.storage.save_file(log_key, existing + formatted_msg + "\n")
        except:
            pass

    async def _check_cancellation(self):
        """Check if cancellation has been requested for this project."""
        try:
            # Check flag via persistence service (Standardized in v3.6)
            cancellation_requested = await self.persistence.check_cancellation(self.project_uuid)
            
            if cancellation_requested:
                logger.info(f"Cancellation detected for project {self.project_id}", "Orchestrator")
                await self._log_persistence("[SYSTEM] Process cancelled by user.")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking cancellation: {e}", "Orchestrator")
            return False

    async def run_full_migration(self, limit: int = 0):
        """Executes the complete Legacy2Lake migration loop."""
        print(f"DEBUG: Starting run_full_migration for {self.project_id}")
        
        # 0. Clear previous logs (File & DB)
        try:
            # Reset cancellation flag for the new run
            await self.persistence.update_project_metadata(self.project_uuid, {"cancellation_requested": False})

            # Clear Database Logs for MIGRATION phase
            await self.persistence.clear_execution_logs(self.project_uuid or self.project_id, phase="MIGRATION")
            
            # Clear Storage Logs
            log_key = f"{self.base_path.rstrip('/')}/migration.log"
            self.storage.save_file(log_key, f"--- Migration Started for {self.project_id} ---\n")
        except Exception as e:
            print(f"WARNING: Could not clear log storage/DB: {e}")

        await self._log_persistence(f"Starting Migration for {self.project_id}")
        logger.info(f"Starting Migration for {self.project_id}", "Orchestrator")
        
        # 1. Governance Check
        # Use UUID for status check
        # Allow both DRAFTING (first run) and DRAFTED (regeneration)
        status = await self.persistence.get_project_status(self.project_uuid)
        allowed_statuses = ["DRAFTING", "DRAFTED"]
        
        if status not in allowed_statuses:
            logger.error(f"BLOCKED: Project status is '{status}'. Must be DRAFTING or DRAFTED.", "Orchestrator")
            await self._log_persistence(f"BLOCKED: Project status is '{status}'. Must be DRAFTING or DRAFTED.")
            return {
                "project_id": self.project_id,
                "error": f"Project is in {status} mode. Cannot run migration from this state.",
                "succeeded": [],
                "failed": []
            }
        
        # Status validation passed - now change to ORCHESTRATING
        is_regeneration = (status == "DRAFTED")
        await self.persistence.update_project_status(self.project_uuid, "ORCHESTRATING")
        
        if is_regeneration:
            await self._log_persistence("♻️ REGENERATION MODE: Project already drafted. Re-generating code...")
            logger.info("Regeneration mode: Re-running migration", "Orchestrator")
        else:
            await self._log_persistence("Status changed to ORCHESTRATING. Starting pipeline...")
            logger.info("First generation: Starting fresh migration", "Orchestrator")

        # 1. THE LIBRARIAN (Context)
        logger.info("Step 1: Librarian - Scanning Schema Context...", "Orchestrator")
        await self._log_persistence("Step 1: Librarian - Scanning Schema Context...")
        schema_ref = await self.librarian.scan_project()
        logger.info(f"Found {len(schema_ref['tables'])} tables.", "Librarian")
        await self._log_persistence(f"Librarian: Found {len(schema_ref['tables'])} tables.")
        logger.debug("Schema Reference", "Librarian", schema_ref)

        # 2. THE TOPOLOGY ARCHITECT (Plan)
        logger.info("Step 2: Topology - Building Orchestration Plan...", "Orchestrator")
        await self._log_persistence("Step 2: Topology - Building Orchestration Plan...")
        topology_result = self.topology.build_orchestration_plan()
        orchestration = topology_result["orchestration"]
        package_metadatas = topology_result["package_metadatas"]
        
        logger.info(f"Generated DAG with {len(orchestration['dag_execution'])} phases.", "Topology")
        await self._log_persistence(f"Topology: Generated DAG with {len(orchestration['dag_execution'])} phases.")
        logger.debug("Orchestration Plan", "Topology", orchestration)

        # 3. EXECUTION LOOP (Developer + Compliance)
        logger.info("Step 3: Execution - Generating & Auditing Code...", "Orchestrator")
        await self._log_persistence("Step 3: Execution - Generating & Auditing Code...")
        
        # Pre-fetch and cache DB assets for enrichment
        db_assets = await self.persistence.get_project_assets(self.project_uuid)
        
        # Load Project Intelligence (Support + Forensic)
        project_meta = await self.persistence.get_project_metadata(self.project_uuid)
        settings = project_meta.get("settings", {})
        config = project_meta.get("config", {})
        
        support_intel = settings.get("support_intelligence", [])
        scout_assessment = settings.get("scout_assessment", {})
        
        # Resolve Technologies (Settings > Config > Default)
        source_tech = settings.get("source_tech") or config.get("source_tech", "mssql")
        target_tech = settings.get("target_tech") or config.get("target_tech", "pyspark")
        
        results = {
            "project_id": self.project_id,
            "succeeded": [],
            "failed": []
        }

        # Initialize Bitácora
        timestamp_log = datetime.utcnow().isoformat()
        self.bitacora = [
            f"# Migration Bitácora - {self.project_id}",
            f"**Generated At**: {timestamp_log}Z",
            f"**Target Tech**: {target_tech.upper()}",
            "---"
        ]

        # Create metadata lookup map
        metadata_map = { pm["package_name"]: pm for pm in package_metadatas }

        # Count total assets for accurate frontend progress tracking
        total_assets = sum(len(p.get("packages", [])) for p in orchestration["dag_execution"])
        processed_count = 0
        await self._log_persistence(f"[PIPELINE START] {total_assets} assets queued for processing...")
        logger.info(f"Total assets to process: {total_assets}", "Orchestrator")

        for phase in orchestration["dag_execution"]:
            # Check for cancellation before processing each phase
            if await self._check_cancellation():
                logger.info("Migration cancelled by user", "Orchestrator")
                return {
                    "project_id": self.project_id,
                    "cancelled": True,
                    "succeeded": results["succeeded"],
                    "failed": results["failed"]
                }
            
            if limit > 0 and len(results["succeeded"]) + len(results["failed"]) >= limit:
                break

            logger.info(f"Entering Phase: {phase['phase']}", "Orchestrator")
            await self._log_persistence(f"Entering Phase: {phase['phase']}")
            
            # Resolve models once per phase for logging clarity
            config_c = await self.persistence.resolve_llm_for_agent("agent-c", self.project_uuid)
            config_f = await self.persistence.resolve_llm_for_agent("agent-f", self.project_uuid)
            model_c = config_c.get("model_name", "Unknown")
            model_f = config_f.get("model_name", "Unknown")
            for pkg_name in phase["packages"]:
                # Check for cancellation before processing each package
                if await self._check_cancellation():
                    logger.info("Migration cancelled by user", "Orchestrator")
                    return {
                        "project_id": self.project_id,
                        "cancelled": True,
                        "succeeded": results["succeeded"],
                        "failed": results["failed"]
                    }
                
                if limit > 0 and len(results["succeeded"]) + len(results["failed"]) >= limit:
                    break
                
                processed_count += 1
                logger.info(f"Processing [{processed_count}/{total_assets}]: {pkg_name}", "Orchestrator")
                await self._log_persistence(f"[PROGRESS: {processed_count}/{total_assets}] Processing: {pkg_name}...")
                
                # A. Prepare Task Context
                pm = metadata_map.get(pkg_name, {})
                
                # Enrich with DB Metadata if available
                asset_meta = next((a for a in db_assets if a.get("source_name") == pkg_name), {})
                
                # Sprint 13: Normalize tech_id for persistence
                tech_id_raw = target_tech.lower()
                if '(' in tech_id_raw:
                    tech_id_raw = tech_id_raw.split('(')[0].strip()
                tech_id_normalized = tech_id_raw.replace(' ', '_')
                
                task_def = {
                    "asset_id": asset_meta.get("object_id") or asset_meta.get("id"),  # Sprint 13: Required for persistence
                    "tech_id": tech_id_normalized,  # Sprint 13: For persistence
                    "layer": "direct",  # v4.0: Direct translation (1:1 transpilation). For architectural patterns (Medallion/Data Vault), apply in Refinement phase.
                    "project_id": self.project_uuid,
                    "package_name": pkg_name,
                    "name": pkg_name, # Compatibility with Agent C expecting 'name'
                    "type": "SSIS Package",
                    "description": f"Transpilation of {pkg_name}",
                    "inputs": pm.get("inputs", []),
                    "outputs": pm.get("outputs", []),
                    "lookups": pm.get("lookups", []),
                    # Pass through user-configured metadata from DB
                    "frequency": asset_meta.get("frequency"),
                    "load_strategy": asset_meta.get("load_strategy"),
                    "is_pii": asset_meta.get("is_pii"),
                    "masking_rule": asset_meta.get("masking_rule"),
                    "business_entity": asset_meta.get("business_entity"),
                    "target_name": asset_meta.get("target_name"),
                    "metadata": asset_meta.get("metadata", {}), # Extracted XML metadata
                    "support_intelligence": support_intel,
                    "scout_assessment": scout_assessment,
                    "source_tech": source_tech, 
                    "target_tech": target_tech
                }
                
                
                # B. AGENT-C: DEVELOPER (Write)
                provider_c = config_c.get("provider", "UNKNOWN").upper()
                await self._log_persistence(f"Initiating Agent C (Developer) via {provider_c} using model {model_c}", step="Developer")
                
                # Set-based Operations: Provide context of other packages
                set_context = package_metadatas if len(package_metadatas) < 50 else [] # Limit size for tokens
                code_result = await self.agent_c.transpile_task(task_def, set_context=set_context)
                
                notebook_content = code_result.get("pyspark_code", "")
                sql_content = code_result.get("sql_code", "")
                
                if not notebook_content and not sql_content:
                    reason = code_result.get("error") or code_result.get("reason", "Empty code response")
                    logger.error(f"Agent-C failed to generate code for {pkg_name}: {reason}", "Orchestrator")
                    await self._log_persistence(f"Agent-C: Failed to generate code for {pkg_name} - Reason: {reason}", step="Developer")
                    results["failed"].append({"package": pkg_name, "reason": reason})
                    continue

                # NEW: Check for cancellation after Agent C
                if await self._check_cancellation():
                    logger.info("Migration cancelled by user after Agent C", "Orchestrator")
                    return {
                        "project_id": self.project_id,
                        "cancelled": True,
                        "succeeded": results["succeeded"],
                        "failed": results["failed"]
                    }

                # C. AGENT-F: COMPLIANCE (Audit)
                provider_f = config_f.get("provider", "UNKNOWN").upper()
                await self._log_persistence(f"Initiating Agent F (Compliance) via {provider_f} using model {model_f}", step="Compliance")
                
                audit_report = await self.agent_f.review_code(task_def, notebook_content, project_id=self.project_uuid)
                
                status = audit_report.get("status", "UNKNOWN")
                logger.info(f"Audit Status: {status} (Score: {audit_report.get('score', 0)})", "Compliance")
                
                # Save Artifacts
                clean_name = pkg_name.replace(".dtsx", "")
                if notebook_content:
                    self._save_artifact(f"{clean_name}.py", notebook_content)
                if sql_content:
                    self._save_artifact(f"{clean_name}.sql", sql_content)
                
                self._save_artifact(f"{clean_name}_audit.json", json.dumps(audit_report, indent=2))
                
                if status in ["APPROVED", "IMPROVED"]:
                    results["succeeded"].append(pkg_name)
                    display_status = "APPROVED" if status == "APPROVED" else "IMPROVED (Optimized)"
                    await self._log_persistence(f"Compliance: {display_status} {pkg_name} (Score: {audit_report.get('score')})")
                    
                    # If improved, we might want to use the optimized code
                    if status == "IMPROVED" and audit_report.get("optimized_code"):
                         notebook_content = audit_report.get("optimized_code")
                         # Re-save with optimized content
                         self._save_artifact(f"{clean_name}.py", notebook_content)
                else:
                    await self._log_persistence(f"Compliance: REJECTED {pkg_name} (Score: {audit_report.get('score')})")
                    results["failed"].append({
                        "package": pkg_name, 
                        "reason": audit_report.get("critique", "Audit Rejected"), 
                        "violations": audit_report.get("violations")
                    })

                # NEW: Check for cancellation after Agent F
                if await self._check_cancellation():
                    logger.info("Migration cancelled by user after Agent F", "Orchestrator")
                    return {
                        "project_id": self.project_id,
                        "cancelled": True,
                        "succeeded": results["succeeded"],
                        "failed": results["failed"]
                    }

                # Update Bitácora
                bitacora_entry = f"## Package: {pkg_name}\n"
                bitacora_entry += f"**Status**: {status} (Score: {audit_report.get('score', 0)}/10)\n\n"
                
                bitacora_entry += "### Agent C (Developer)\n"
                bitacora_entry += f"{code_result.get('explanation', 'No explanation provided.')}\n\n"
                
                bitacora_entry += "### Agent F (Compliance)\n"
                bitacora_entry += f"**Critique**: {audit_report.get('critique', 'N/A')}\n"
                if audit_report.get("violations"):
                    bitacora_entry += "**Violations**:\n"
                    for v in audit_report.get("violations", []):
                        bitacora_entry += f"- {v}\n"
                bitacora_entry += "---\n"
                
                self.bitacora.append(bitacora_entry)

        if limit > 0 and len(results["succeeded"]) + len(results["failed"]) >= limit:
            logger.warning(f"Limit Reached: Stopping after {limit} packages.", "Orchestrator")
            await self._log_persistence(f"Limit Reached: Stopping after {limit} packages.")

        # NEW: Check for cancellation before Agent G
        if await self._check_cancellation():
            logger.info("Migration cancelled by user before Governance", "Orchestrator")
            return {
                "project_id": self.project_id,
                "cancelled": True,
                "succeeded": results["succeeded"],
                "failed": results["failed"]
            }

        # AGENT-G: GOVERNANCE (Generate Runbook & Certification)
        if results["succeeded"]:
            await self._log_persistence("Initiating Agent G (Governance)...", step="Certification")
            try:
                agent_g = AgentGService(tenant_id=self.tenant_id, client_id=None)
                
                # Construct mesh from orchestration result (Topology v2) - Moved up to fix Agent G error
                mesh = {
                    "nodes": package_metadatas, 
                    "edges": [], # Edges are implicit in v2 phases
                    "phases": orchestration.get("dag_execution", [])
                }

                # Collect sample transformations and audits
                sample_transformations = []
                for pkg_name in results["succeeded"][:3]:  # Sample first 3 successful packages
                    clean_name = pkg_name.replace(".dtsx", "")
                    code_key = f"{self.output_path.rstrip('/')}/{clean_name}.py"
                    audit_key = f"{self.output_path.rstrip('/')}/{clean_name}_audit.json"
                    
                    try:
                        code_content = self.storage.read_file(code_key)
                        audit_content = self.storage.read_file(audit_key)
                        sample_transformations.append({
                            "name": pkg_name,
                            "code": code_content,
                            "audit": json.loads(audit_content) if audit_content else {}
                        })
                    except Exception as e:
                        logger.warning(f"Could not load sample for {pkg_name}: {e}", "Governance")
                
                # Generate governance documentation
                governance_result = await agent_g.generate_governance(
                    project_name=self.project_id,
                    mesh=mesh,
                    transformations=sample_transformations,
                    metadata={
                        "total_packages": len(results["succeeded"]) + len(results["failed"]),
                        "succeeded": len(results["succeeded"]),
                        "failed": len(results["failed"]),
                        "target_platform": target_tech
                    }
                )
                
                # Save governance artifacts
                if governance_result.get("runbook"):
                    self._save_artifact("governance_runbook.md", governance_result["runbook"])
                    await self._log_persistence("Governance: Generated Runbook", step="Certification")
                
                if governance_result.get("certification"):
                    self._save_artifact("certification_audit.json", json.dumps(governance_result["certification"], indent=2))
                    await self._log_persistence("Governance: Generated Certification Audit", step="Certification")
                
                logger.info("Agent G: Governance documentation generated successfully", "Governance")
            except Exception as e:
                logger.error(f"Agent G failed: {e}", "Governance")
                await self._log_persistence(f"Governance: Failed to generate documentation - {str(e)}", step="Certification")

        # NEW: Check for cancellation before Handover
        if await self._check_cancellation():
            logger.info("Migration cancelled by user before Handover", "Orchestrator")
            return {
                "project_id": self.project_id,
                "cancelled": True,
                "succeeded": results["succeeded"],
                "failed": results["failed"]
            }

        # Generate MANIFEST.json
        await self._log_persistence("Generating MANIFEST.json...", step="Handover")

        # Fix for missing variables (Migration from SSIS to Generic)
        target_tech = settings.get("target_tech", "pyspark")
        
        # Initialize mesh if not already defined (topology information)
        # TODO: mesh should be constructed during Agent G phase
        mesh = {"nodes": [], "edges": [], "phases": []}
        
        # Construction of mesh was moved up to Agent G section
        manifest = self._generate_manifest(results, mesh, target_tech)
        self._save_artifact("MANIFEST.json", json.dumps(manifest, indent=2))
        await self._log_persistence("MANIFEST.json generated successfully", step="Handover")

        # Save Bitácora
        self._save_artifact("drafting_bitacora.md", "\n".join(self.bitacora))
        await self._log_persistence("Migration Bitácora generated.", step="Handover")

        logger.info(f"Migration Complete. Succeeded: {len(results['succeeded'])}, Failed: {len(results['failed'])}", "Orchestrator")
        await self._log_persistence("=" * 60)
        await self._log_persistence(
            f"PIPELINE COMPLETE — {len(results['succeeded'])} assets migrated successfully, "
            f"{len(results['failed'])} failed."
        )
        await self._log_persistence("=" * 60)
        return results

    def _save_artifact(self, filename: str, content: str):
        artifact_key = f"{self.output_path.rstrip('/')}/{filename}"
        self.storage.save_file(artifact_key, content)

    def _generate_manifest(self, results: Dict[str, List], mesh: Dict[str, Any], target_tech: str) -> Dict[str, Any]:
        """Generate MANIFEST.json with complete artifact inventory."""
        # Calculate total lines generated
        total_lines = 0
        for pkg_name in results["succeeded"]:
            clean_name = pkg_name.replace(".dtsx", "")
            code_key = f"{self.output_path.rstrip('/')}/{clean_name}.py"
            try:
                code_content = self.storage.read_file(code_key)
                if code_content:
                    total_lines += len(code_content.split('\n'))
            except:
                pass
        
        manifest = {
            "project_id": self.project_uuid,
            "project_name": self.project_id,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "migration_summary": {
                "total_packages": len(results["succeeded"]) + len(results["failed"]),
                "succeeded": len(results["succeeded"]),
                "failed": len(results["failed"]),
                "total_lines_generated": total_lines
            },
            "artifacts": {
                "code_files": [
                    {"name": f"{pkg.replace('.dtsx', '')}.py", "type": "pyspark", "package": pkg}
                    for pkg in results["succeeded"]
                ],
                "audit_files": [
                    {"name": f"{pkg.replace('.dtsx', '')}_audit.json", "type": "compliance", "package": pkg}
                    for pkg in results["succeeded"]
                ],
                "governance": [
                    {"name": "governance_runbook.md", "type": "documentation"},
                    {"name": "certification_audit.json", "type": "compliance"}
                ]
            },
            "failed_packages": results["failed"],
            "deployment_info": {
                "target_platform": target_tech,
                "recommended_runtime": self._get_recommended_runtime(target_tech),
                "deployment_guide": "See governance_runbook.md for detailed deployment instructions"
            },
            "topology": {
                "total_nodes": len(mesh.get("nodes", [])),
                "total_edges": len(mesh.get("edges", [])),
                "execution_phases": mesh.get("phases", [])
            }
        }
        
        return manifest
    
    def _get_recommended_runtime(self, target_tech: str) -> str:
        """Get recommended runtime for target platform."""
        runtimes = {
            "pyspark": "Databricks Runtime 13.3 LTS or Apache Spark 3.4+",
            "snowflake": "Snowflake Snowpark Python 1.0+",
            "bigquery": "BigQuery Standard SQL + Python 3.9+",
            "synapse": "Azure Synapse Spark 3.3+"
        }
        return runtimes.get(target_tech.lower(), "See documentation for runtime requirements")

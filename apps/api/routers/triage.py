"""
Triage Router  
Handles discovery, triage, and asset analysis operations.
This is a major router with complex logic extracted from main.py.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import os
import uuid
import logging
import json
import re
import asyncio

from apps.api.routers.dependencies import get_db, get_identity
from apps.api.services.persistence_service import SupabasePersistence, PersistenceService
from apps.api.services.discovery_service import DiscoveryService
from apps.api.services.agent_a_service import AgentAService
from apps.api.services.knowledge_packet_service import KnowledgePacketService
from apps.api.services.table_impact_service import TableImpactService
from apps.api.services.lock_service import LockService, ProcessLockError
from apps.api.services.quick_assessment_service import QuickAssessmentService

router = APIRouter(tags=["Triage & Discovery"])
logger = logging.getLogger(__name__)


# --- Helper Functions for Origin Analysis Extraction (Sprint 8.5) ---

async def _extract_origin_from_medulla(medulla: Dict[str, Any], connections: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract origin system details from SSIS medulla"""
    origin = {
        "source_type": None,
        "server": None,
        "database": None,
        "connections": []
    }
    
    for conn in connections:
        conn_string = conn.get("connection_string", [""])[0] if isinstance(conn.get("connection_string"), list) else conn.get("connection_string", "")
        
        if conn_string:
            parsed = _parse_connection_string(conn_string)
            
            origin["connections"].append({
                "name": conn.get("name"),
                "id": conn.get("id"),
                "type": parsed.get("type", "OLEDB"),
                "server": parsed.get("server"),
                "database": parsed.get("database")
            })
            
            if not origin["source_type"]:
                origin["source_type"] = f"SQL Server ({parsed.get('type', 'OLEDB')})"
                origin["server"] = parsed.get("server")
                origin["database"] = parsed.get("database")
    
    return origin

def _parse_connection_string(conn_string: str) -> Dict[str, Any]:
    """Parse OLEDB/ODBC connection string"""
    parsed = {"type": "OLEDB", "server": None, "database": None}
    
    if "ODBC" in conn_string.upper():
        parsed["type"] = "ODBC"
    
    server_match = re.search(r'Data Source=([^;]+)', conn_string, re.IGNORECASE)
    if server_match:
        parsed["server"] = server_match.group(1).strip()
    else:
        server_match = re.search(r'Server=([^;]+)', conn_string, re.IGNORECASE)
        if server_match:
            parsed["server"] = server_match.group(1).strip()
    
    db_match = re.search(r'Initial Catalog=([^;]+)', conn_string, re.IGNORECASE)
    if db_match:
        parsed["database"] = db_match.group(1).strip()
    else:
        db_match = re.search(r'Database=([^;]+)', conn_string, re.IGNORECASE)
        if db_match:
            parsed["database"] = db_match.group(1).strip()
    
    return parsed

async def _extract_transformations_from_medulla(medulla: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract transformation components from SSIS medulla"""
    transformations = []
    
    # Real medulla structure uses 'data_flow_logic', not 'components'
    for comp in medulla.get("data_flow_logic", []):
        comp_type = comp.get("type", "").upper()
        
        # Map real SSIS types to transformation categories
        if comp_type in ["LOOKUP", "DERIVED_COLUMN", "CONDITIONAL_SPLIT", "AGGREGATE", "SORT", "MERGE", "UNION_ALL", "TRANSFORM"]:
            transformations.append({
                "type": comp_type,
                "name": comp.get("name", ""),
                "id": comp.get("ref_id", "")
            })
    
    return transformations

async def _extract_queries_from_medulla(medulla: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract SQL queries from SSIS medulla"""
    queries = []
    
    # Real medulla structure uses 'data_flow_logic', not 'components'
    for comp in medulla.get("data_flow_logic", []):
        # SQL queries are in raw_properties.SqlCommand
        sql_command = comp.get("raw_properties", {}).get("SqlCommand", "")
        
        if sql_command and sql_command.strip():  # Not empty
            queries.append({
                "component_type": comp.get("type"),
                "component_name": comp.get("name"),
                "query": sql_command
            })
    
    return queries

def _calculate_complexity(transformations: List[Dict[str, Any]]) -> int:
    """Calculate complexity score based on transformations"""
    complexity_weights = {
        "LOOKUP": 15,
        "DERIVED_COLUMN": 10,
        "CONDITIONAL_SPLIT": 12,
        "AGGREGATE": 20,
        "SORT": 8,
        "MERGE": 18,
        "UNION_ALL": 10
    }
    
    score = 0
    for trans in transformations:
        score += complexity_weights.get(trans.get("type", ""), 5)
    
    return min(score, 100)  # Cap at 100


# --- Models ---

class TriageParams(BaseModel):
    system_prompt: Optional[str] = None
    user_context: Optional[str] = None
    pre_classification: Optional[Dict[str, Dict[str, Any]]] = None  # {"path": {"classification": "CORE", "include": true}}


class AssetContextPayload(BaseModel):
    source_path: str
    notes: str
    rules: Optional[Dict[str, Any]] = None


# --- Discovery Endpoints ---

@router.get("/discovery/project/{project_id}")
async def get_discovery_project(project_id: str, db: SupabasePersistence = Depends(get_db)):
    """Returns all assets and the system prompt for a project."""
    project_uuid = project_id
    if "-" not in project_id:
        u = await db.get_project_id_by_name(project_id)
        if u: 
            project_uuid = u
        
    assets = await db.get_project_assets(project_uuid)
    meta = await db.get_project_metadata(project_uuid)
    
    # Fallback to default Triage prompt if not customized for project
    prompt = meta.get("prompt") if meta else None
    if not prompt:
        agent_a = AgentAService(tenant_id=db.tenant_id, client_id=db.client_id)
        prompt = await agent_a._load_prompt()
        
    # Extract tech info from config or settings
    def get_tech(key):
        if not meta: return None
        # Try settings first as it's the standard for new projects
        val = meta.get("settings", {}).get(key)
        if not val:
            # Fallback to config
            val = meta.get("config", {}).get(key)
        return val

    return {
        "assets": assets,
        "prompt": prompt,
        "source_tech": get_tech("source_tech"),
        "target_tech": get_tech("target_tech")
    }


@router.get("/discovery/status/{project_id}")
async def get_discovery_status(project_id: str, db: SupabasePersistence = Depends(get_db)):
    """Returns the discovery/triage status for a project."""
    metadata = await db.get_project_metadata(project_id)
    if not metadata:
        uuid = await db.get_project_id_by_name(project_id)
        if uuid: 
            metadata = await db.get_project_metadata(uuid)

    if not metadata:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {
        "status": metadata.get("status", "TRIAGE"),
        "stage": metadata.get("stage", "1"),
        "is_ready": metadata.get("status") != "TRIAGE" or metadata.get("stage") != "1"
    }


# --- Background Task Execution ---

async def _run_triage_background(
    project_id: str,
    params: TriageParams,
    lock_id: Optional[str],
    lock_service: LockService,
    tenant_id: str,
    username: str,
    db_config: dict  # Pass DB connection params instead of instance
):
    """
    Background task to execute triage process.
    Updates execution logs in real-time to DB.
    """
    # Create fresh DB instance for background task (thread-safe)
    db = SupabasePersistence(tenant_id=tenant_id, client_id=db_config.get("client_id"))
    
    try:
        # Resolve UUID and Name correctly
        project_uuid = project_id
        project_folder = project_id
        
        if "-" in project_id:  # Heuristic: if UUID, get name for folder
            resolved_name = await db.get_project_name_by_id(project_id)
            if resolved_name:
                project_folder = resolved_name
        else:  # If name, get UUID for DB operations
            resolved_uuid = await db.get_project_id_by_name(project_id)
            if resolved_uuid:
                project_uuid = resolved_uuid

        # GOVERNANCE CHECK: TRIAGE is only allowed in TRIAGE mode.
        current_status = await db.get_project_status(project_uuid)
        if current_status == "DRAFTING":
            await db.log_execution(
                project_uuid, "TRIAGE", 
                "[ERROR] Project is in DRAFTING mode. Triage is locked.",
                step="SYSTEM"
            )
            return

        import datetime
    
        # 0. Clear previous logs for TRIAGE phase
        try:
            await db.clear_execution_logs(project_uuid, phase="TRIAGE")
        except Exception as e:
            print(f"WARNING: Could not clear TRIAGE DB logs: {e}")

        log_lines = []
    
        # Helper to persist log incrementally
        async def _log(msg: str, agent: str = "SYSTEM"):
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            formatted_msg = f"[{now}] [{agent}] {msg}"
            log_lines.append(formatted_msg)
        
            # 1. Database Logging (Primary for real-time streaming)
            await db.log_execution(project_uuid, "TRIAGE", msg, step=agent)
        
            # 2. Storage Logging (Fallback / Historical)
            try:
                current_log_content = "\n".join(log_lines)
                storage = PersistenceService.get_storage()
                proj_base = PersistenceService.ensure_solution_dir(project_folder, tenant_id=db.tenant_id)
                log_key = f"{proj_base.rstrip('/')}/triage.log"
                storage.save_file(log_key, current_log_content)
            except Exception as e:
                print(f"DEBUG: Triage Log Error: {e}")
            
        async def _check_cancellation():
            """Check if cancellation has been requested for this project."""
            try:
                return await db.check_cancellation(project_uuid)
            except: return False

        # 1. Reset cancellation flag and clear previous logs for TRIAGE phase
        try:
            await db.update_project_metadata(project_uuid, {"cancellation_requested": False})
            await db.clear_execution_logs(project_uuid, phase="TRIAGE")
        except Exception as e:
            print(f"WARNING: Could not reset flag or clear TRIAGE DB logs: {e}")

        # Clear previous log in storage
        await _log("--- Triage Started ---", agent="SYSTEM")
    
        # Check for cancellation
        if await _check_cancellation():
            await _log("Triage cancelled by user.", agent="SYSTEM")
            return

        await _log(f"Initializing Legacy2Lake Triage Agent for Project: {project_id}")

        # 1. Deep Scan (The Scanner / Pre-processing)
        await _log("Running Deep Scanner (Python Engine)...", agent="SCANNER")
    
        # Fetch persistent human context
        user_context = await db.get_project_context(project_uuid)
        if user_context:
            await _log(f"Found {len(user_context)} human context overrides. Injecting into scanner...", agent="SCANNER")
        
        manifest = DiscoveryService.generate_manifest(project_folder, tenant_id=db.tenant_id, user_context=user_context)
        manifest["project_id"] = project_uuid
    
        file_count = len(manifest["file_inventory"])
        tech_stats = manifest["tech_stats"]
        await _log(f"Scanned {file_count} files.", agent="SCANNER")
        await _log(f"Tech Stack Detected: {tech_stats}", agent="SCANNER")
    
        # Phase B: Enrich manifest with schema reference (Librarian)
        await _log("Enriching manifest with schema intelligence (Librarian)...", agent="LIBRARIAN")
        try:
            librarian = KnowledgePacketService(tenant_id=db.tenant_id, project_id=project_uuid)
            scan_result = await librarian.scan_project(project_uuid)
            
            manifest["schema_reference"] = scan_result.get("schema_reference", {})
            manifest["knowledge_summary"] = {
                "total_assets": scan_result.get("total_assets", 0),
                "assets_with_ddl_types": scan_result.get("assets_with_ddl_types", 0),
                "assets_with_profiled_types": scan_result.get("assets_with_profiled_types", 0),
                "pii_columns_detected": scan_result.get("pii_columns_detected", 0)
            }
            
            await _log(
                f"Schema reference loaded: {len(manifest['schema_reference'].get('tables', {}))} tables, "
                f"{scan_result.get('pii_columns_detected', 0)} PII columns detected",
                agent="LIBRARIAN"
            )
        except Exception as e:
            await _log(f"Warning: Schema enrichment failed (non-critical): {e}", agent="LIBRARIAN")
            manifest["schema_reference"] = {}
            manifest["knowledge_summary"] = {}
    
        # Check for cancellation
        if await _check_cancellation():
            await _log("Triage cancelled by user.", agent="SYSTEM")
            return
    
        # 2. Agent A Analysis (The Detective)
        await _log("Invoking Agent A (Mesh Architect)...", agent="ORCHESTRATOR")
        if params.system_prompt:
            await _log("Applying custom System Prompt override.", agent="ORCHESTRATOR")
    
        # Resolve Model info for logging before calling agent
        llm_config = await db.resolve_agent_model("agent-a")
        if llm_config:
            provider = llm_config.get('provider', 'UNKNOWN').upper()
            model = llm_config.get('deployment') or llm_config.get('model_name', 'UNKNOWN')
            await _log(f"Initiating Agent A (Detective) via {provider} using model {model}", agent="AGENT_A")
        else:
            await _log("FAILED: LLM configuration for 'agent-a' is missing or invalid for this tenant.", agent="AGENT_A")
            return

        agent_a = AgentAService(tenant_id=db.tenant_id, client_id=db.client_id)
        try:
            prompt = params.system_prompt
            if params.user_context:
                prompt = (prompt or "") + f"\n\n[USER CONTEXT CONSTRAINTS]:\n{params.user_context}"
            
            result = await agent_a.analyze_manifest(manifest, system_prompt_override=prompt)
        
            if "error" in result:
                await _log(f"Agent A failed: {result['error']}", agent="AGENT_A")
                return
             
            rf_nodes = result.get("mesh_graph", {}).get("nodes", [])
            rf_edges = result.get("mesh_graph", {}).get("edges", [])
        
            # Auto-Promotion Fallback: Ensure CORE-likely physical assets are in the graph
            for item in manifest["file_inventory"]:
                if item["name"].lower() in ['triage.log', 'thumbs.db', '.ds_store', 'desktop.ini']:
                    continue
                 
                if not any(n["id"] == item["path"] for n in rf_nodes):
                    ext = item["name"].split('.')[-1].lower() if '.' in item["name"] else ''
                    if ext in ['dtsx', 'sql', 'py', 'spark', 'scala']:
                        rf_nodes.append({
                            "id": item["path"],
                            "label": item["name"],
                            "category": "CORE",
                            "complexity": "LOW",
                            "confidence": 0.5,
                            "business_entity": "SYSTEM_INFERRED",
                            "target_name": item["name"]
                        })
        
            await _log(f"Analysis Complete. Total Nodes (AI + Inferred): {len(rf_nodes)}", agent="AGENT_A")
        
        except Exception as e:
            await _log(f"CRITICAL Architecture Analysis Failed: {e}", agent="AGENT_A")
            return

        # Check for cancellation
        if await _check_cancellation():
            await _log("Triage cancelled by user.", agent="SYSTEM")
            return

        # Phase D: Agent S removed - replaced by Quick Assessment (Phase A) in Discovery stage
        # Scout functionality consolidated into deterministic analysis

        # Check for cancellation
        if await _check_cancellation():
            await _log("Triage cancelled by user.", agent="SYSTEM")
            return

        # 4. Persistence (Supabase)
        await _log("Persisting Mesh Graph and Discovered Assets...", agent="DATABASE")
    
        db_assets = []
        qa_service = QuickAssessmentService(tenant_id=db.tenant_id)
        
        # Get pre_classification from params (optional - backward compatible)
        pre_classification = params.pre_classification or {}
        
        # Count included/excluded for logging
        total_files = len(manifest["file_inventory"])
        included_count = 0
        excluded_count = 0
        
        for item in manifest["file_inventory"]:
            file_path = item["path"]
            
            # Check if user excluded this file in Discovery
            file_preclassification = pre_classification.get(file_path, {})
            include_file = file_preclassification.get("include", True)  # Default: include if no pre-classification
            
            if not include_file:
                excluded_count += 1
                await _log(f"⊘ Skipping excluded file: {item['name']}", agent="TRIAGE")
                continue  # Skip this file completely
            
            included_count += 1
            
            # Use pre-assigned classification if available, otherwise auto-detect
            if file_preclassification:
                # Usuario ajustó la clasificación en Discovery
                category = file_preclassification.get("classification", "CORE")
            else:
                # Fallback: lógica anterior (backward compatible)
                agent_node = next((n for n in rf_nodes if n["id"] == item["path"]), None)
                category = agent_node["category"] if agent_node else "IGNORED" 
                if not agent_node:
                    category = DiscoveryService._map_extension_to_type(
                        item["name"].split('.')[-1].lower() if '.' in item["name"] else 'none'
                    )
            
            # Classify file for category field (Sprint 14)
            file_category, detected_tech = qa_service._classify_file(item)

            db_assets.append({
                "filename": item["name"],
                "type": category,  # CORE/SUPPORT/IGNORED - from user pre-classification or auto
                "category": file_category,  # migrable, soporte, documentacion, no_reconocido
                "source_path": item["path"],
                "metadata": {**item.get("metadata", {}), "size": item["size"]},
                "selected": True if category == "CORE" else False
            })
        
        # Log optimization stats
        if excluded_count > 0:
            await _log(
                f"✓ Optimized processing: {included_count} of {total_files} files included ({excluded_count} excluded by user)",
                agent="TRIAGE"
            )
        else:
            await _log(f"Processing all {total_files} files (no pre-classification)", agent="TRIAGE")
    
        saved_assets = await db.batch_save_assets(project_uuid, db_assets)
        asset_map = {a["source_path"]: (a.get("id") or a.get("object_id")) for a in saved_assets}

        # SPRINT 8.5: Extract Origin Analysis during Triage (not during code generation)
        await _log("Extracting origin analysis from SSIS assets...", agent="TRIAGE")
        origin_count = 0
        for asset in saved_assets:
            try:
                metadata = asset.get("metadata", {})
                medulla = metadata.get("logical_medulla")
                connections = metadata.get("connections", [])
                
                if not medulla:
                    continue  # Skip assets without medulla (non-SSIS files)
                
                object_id = asset.get("object_id") or asset.get("id")
                
                # Extract origin analysis from medulla
                origin_analysis = await _extract_origin_from_medulla(medulla, connections)
                transformations = await _extract_transformations_from_medulla(medulla)
                queries = await _extract_queries_from_medulla(medulla)
                complexity = _calculate_complexity(transformations)
                
                # Persist to utm_objects Sprint 8.5 columns
                db.client.table("utm_objects").update({
                    "source_connection": json.dumps(origin_analysis.get("connections", [])),
                    "source_type": origin_analysis.get("source_type"),
                    "source_query": queries[0].get("query") if queries else None,
                    "transformations": json.dumps(transformations),
                    "complexity_score": complexity,
                    "data_flow_analysis": json.dumps({
                        "origin": origin_analysis,
                        "queries": queries,
                        "transformations_count": len(transformations)
                    })
                }).eq("object_id", object_id).execute()
                
                origin_count += 1
                
            except Exception as e:
                logger.warning(f"Failed to extract origin analysis for {asset.get('filename')}: {e}")
        
        if origin_count > 0:
            await _log(f"✅ Extracted origin analysis from {origin_count} SSIS asset(s)", agent="TRIAGE")

        # Phase C: Analyze table impacts after assets are persisted
        await _log("Analyzing table impacts (Phase C)...", agent="TABLE_IMPACT")
        try:
            impact_service = TableImpactService(
                project_id=project_uuid,
                tenant_id=db.tenant_id,
                client_id=db.client_id
            )
            
            impact_result = await impact_service.analyze_impacts()
            
            await _log(
                f"Table impact analysis complete: {impact_result.get('total_impacts', 0)} impacts detected, "
                f"{impact_result.get('unique_tables', 0)} unique tables",
                agent="TABLE_IMPACT"
            )
            
            # Build dependency DAG
            dag = await impact_service.build_dependency_dag()
            
            if dag.cycles:
                await _log(
                    f"⚠️ Warning: {len(dag.cycles)} circular dependencies detected in asset flow",
                    agent="TABLE_IMPACT"
                )
            
            # Store in project settings for later retrieval
            await db.update_project_settings(project_uuid, {
                "table_impacts_summary": {
                    "total_impacts": impact_result.get("total_impacts", 0),
                    "unique_tables": impact_result.get("unique_tables", 0),
                    "has_cycles": len(dag.cycles) > 0
                },
                "dependency_dag": {
                    "nodes": dag.nodes,
                    "edges_count": len(dag.edges),
                    "execution_levels": len(dag.execution_order),
                    "has_cycles": len(dag.cycles) > 0
                }
            })
            
        except Exception as e:
            await _log(f"Warning: Table impact analysis failed (non-critical): {e}", agent="TABLE_IMPACT")

        # Transform Agent Nodes to ReactFlow Nodes
        final_nodes = []
        # FIX: Only CORE assets go to the graph. SUPPORT assets provide context but are NOT migrated.
        graph_eligible = [n for n in rf_nodes if n.get("category") == "CORE"]
    
        for i, n in enumerate(graph_eligible):
            n_id = n.get("id") or f"node_{i}" 
            n_uuid = asset_map.get(n_id, n_id)
        
            final_nodes.append({
                "id": n_uuid,
                "type": "custom", 
                "position": {"x": 200 + (i % 5 * 250), "y": 100 + (i // 5 * 150)},
                "data": { 
                    "label": n.get("label") or n.get("id") or f"Node {i}", 
                    "category": n.get("category", "CORE"),
                    "complexity": n.get("complexity", "LOW"),
                    "status": "pending"
                }
            })
        
        final_edges = []
        for e in rf_edges:
            e_from = e.get('from') or e.get('source')
            e_to = e.get('to') or e.get('target')
        
            if not e_from or not e_to: continue
        
            src_uid = asset_map.get(e_from, e_from)
            tgt_uid = asset_map.get(e_to, e_to)
        
            final_edges.append({
                "id": f"e{src_uid}-{tgt_uid}",
                "source": src_uid,
                "target": tgt_uid,
                "label": e.get('type') or e.get('label') or 'SEQUENTIAL'
            })
        
        await db.save_project_layout(project_uuid, {"nodes": final_nodes, "edges": final_edges})
    
        # Release 3.7: Persist Support Intelligence and Total Lines for reports/dashboard
        total_lines = sum(item.get("lines", 0) for item in manifest["file_inventory"])
    
        settings_update = {
            "lines_generated": total_lines # Map input lines to this field for the dashboard
        }
        if manifest.get("support_intelligence"):
            settings_update["support_intelligence"] = manifest["support_intelligence"]
        
        # Phase D: Store enriched manifest metadata (no more scout_report)
        if manifest.get("knowledge_summary"):
            settings_update["knowledge_summary"] = manifest["knowledge_summary"]
        
        await db.update_project_settings(project_uuid, settings_update)
    
        await _log(f"Graph and Assets saved to database. Total Lines: {total_lines}", agent="DATABASE")
        
        # At the end, update project status to TRIAGED
        await db.update_project_status(project_uuid, "TRIAGED")
        await _log("✅ Triage completed successfully", agent="TRIAGE")
        
    except Exception as e:
        # Log error to DB
        try:
            await db.log_execution(
                project_uuid, "TRIAGE",
                f"❌ Error: {str(e)}",
                step="ERROR"
            )
        except:
            pass
        print(f"[BACKGROUND TRIAGE ERROR]: {e}")
        
    finally:
        # === ALWAYS: Release lock ===
        if lock_id:
            try:
                await lock_service.release_lock(lock_id=lock_id, user_id=tenant_id)
                print(f"[TRIAGE] Lock {lock_id} released")
            except Exception as e:
                print(f"WARNING: Failed to release lock {lock_id}: {e}")


# --- Triage Endpoint ---

@router.post("/projects/{project_id}/triage")
async def run_triage(
    project_id: str, 
    params: TriageParams, 
    background_tasks: BackgroundTasks,
    request: Request,
    identity: dict = Depends(get_identity),
    db: SupabasePersistence = Depends(get_db)
):
    """Re-runs the triage (discovery) process using agentic reasoning (ASYNC - returns immediately)."""
    
    # === PERMISSION CHECK ===
    # Only COLLABORATOR, MANAGER, and ADMIN can execute phases
    role = identity.get("role", "VIEWER")
    if role == "VIEWER":
        raise HTTPException(
            status_code=403,
            detail="VIEWER users have read-only access. Only COLLABORATOR, MANAGER, and ADMIN can execute project phases."
        )
    
    # === PROCESS LOCKING ===
    lock_service = LockService(tenant_id=identity.get("tenant_id"), client_id=identity.get("client_id"))
    
    # Get username for lock
    tenant_id = identity.get("tenant_id")
    username = identity.get("username", "Unknown User")
    if not username or username == "Unknown User":
        # Fetch from database if not in identity
        try:
            tenant = await db.get_tenant_by_id(tenant_id)
            username = tenant.get("username", "Unknown User") if tenant else "Unknown User"
        except:
            username = "Unknown User"
    
    # Generate or get session ID
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Try to acquire lock
    lock_id = None
    try:
        lock = await lock_service.acquire_lock(
            project_id=project_id,
            process_type="triage",
            user_id=tenant_id,
            username=username,
            session_id=session_id,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.headers.get("x-forwarded-for") or "unknown"
        )
        lock_id = lock['lock_id']
        
    except ProcessLockError as e:
        # Process is locked by another user/session
        raise HTTPException(
            status_code=423,  # 423 Locked
            detail={
                "error": "Process already running",
                "message": e.message,
                "locked_by": e.locked_by
            }
        )
    
    # === UPDATE STATUS TO PROCESSING ===
    try:
        project_uuid = project_id
        if "-" not in project_id:  # If name, get UUID
            project_uuid = await db.get_project_id_by_name(project_id) or project_id
        
        await db.update_project_status(project_uuid, "PROCESSING")
    except Exception as e:
        print(f"WARNING: Could not update status to PROCESSING: {e}")
    
    # === LAUNCH BACKGROUND TASK ===
    db_config = {
        "tenant_id": db.tenant_id,
        "client_id": db.client_id
    }
    
    background_tasks.add_task(
        _run_triage_background,
        project_id=project_id,
        params=params,
        lock_id=lock_id,
        lock_service=lock_service,
        tenant_id=tenant_id,
        username=username,
        db_config=db_config
    )
    
    return {
        "status": "RUNNING",
        "message": "Triage process started in background. Check execution logs for progress.",
        "project_id": project_id
    }


# --- Graph Sync ---

@router.post("/projects/{project_id}/sync-graph")
async def sync_project_graph(project_id: str, db: SupabasePersistence = Depends(get_db)):
    """Rebuilds the graph layout based on assets currently marked as 'selected'."""
    project_uuid = project_id
    if len(project_id) < 32:
        project_uuid = await db.get_project_id_by_name(project_id)

    if not project_uuid:
        raise HTTPException(status_code=404, detail="Project not found")

    # 1. Fetch assets marked as selected
    assets = await db.get_project_assets(project_uuid)
    selected_assets = [a for a in assets if a.get("selected")]

    # 2. Fetch current layout to preserve positions for existing nodes
    current_layout = await db.get_project_layout(project_uuid)
    existing_nodes = {n["id"]: n for n in current_layout.get("nodes", [])}
    existing_edges = current_layout.get("edges", [])

    # 3. Build new node list
    final_nodes = []
    for i, asset in enumerate(selected_assets):
        asset_id = asset["id"]
        
        if asset_id in existing_nodes:
            final_nodes.append(existing_nodes[asset_id])
        else:
            final_nodes.append({
                "id": asset_id,
                "type": "custom",
                "position": {"x": 200 + (len(final_nodes) % 5 * 250), "y": 100 + (len(final_nodes) // 5 * 150)},
                "data": {
                    "label": asset["filename"],
                    "category": asset.get("type", "CORE"),
                    "complexity": asset.get("metadata", {}).get("complexity", "LOW"),
                    "status": "pending"
                }
            })

    # 4. Filter edges
    node_ids = {n["id"] for n in final_nodes}
    final_edges = [e for e in existing_edges if e["source"] in node_ids and e["target"] in node_ids]

    # 5. Save and return
    new_layout = {"nodes": final_nodes, "edges": final_edges}
    await db.save_project_layout(project_uuid, new_layout)

    return {
        "success": True,
        "nodes": final_nodes,
        "edges": final_edges
    }


# --- Asset Context ---

@router.patch("/projects/{project_id}/prompt")
async def update_project_prompt(project_id: str, payload: Dict[str, str], db: SupabasePersistence = Depends(get_db)):
    """Updates the customized system prompt for a project."""
    success = await db.update_project_prompt(project_id, payload.get("prompt"))
    return {"success": success}


@router.patch("/assets/{asset_id}")
async def patch_asset(asset_id: str, updates: Dict[str, Any], db: SupabasePersistence = Depends(get_db)):
    """Updates asset metadata (type, selected status)."""
    success = await db.update_asset_metadata(asset_id, updates)
    return {"success": success}


@router.post("/projects/{project_id}/context")
async def save_context(project_id: str, payload: AssetContextPayload, db: SupabasePersistence = Depends(get_db)):
    """Saves human context for an asset."""
    project_uuid = project_id
    if "-" not in project_id:
        u = await db.get_project_id_by_name(project_id)
        if u: 
            project_uuid = u

    success = await db.save_asset_context(
        project_uuid,
        payload.source_path,
        payload.notes,
        payload.rules
    )
    return {"success": success}


@router.get("/projects/{project_id}/context")
async def get_context(project_id: str, db: SupabasePersistence = Depends(get_db)):
    """Retrieves all context entries for a project."""
    project_uuid = project_id
    if "-" not in project_id:
        u = await db.get_project_id_by_name(project_id)
        if u: 
            project_uuid = u
            
    context = await db.get_project_context(project_uuid)
    return {"contexts": context}


# --- Sprint 7: Deep Forensic Triage (Column-Level Analysis) ---

@router.post("/assets/{asset_id}/analyze-columns")
async def analyze_asset_columns(
    asset_id: str,
    columns_metadata: List[Dict[str, Any]],
    db: SupabasePersistence = Depends(get_db)
):
    """
    Sprint 7: Deep column-level analysis for a specific asset.
    
    Performs:
    - Cardinality analysis
    - PII detection  
    - Partition recommendations
    - Data quality scoring
    
    Args:
        asset_id: UUID of the asset (utm_objects.object_id)
        columns_metadata: List of column definitions with sample data
            Example:
            [
                {
                    "column_name": "CustomerID",
                    "data_type": "INT",
                    "sample_values": [1, 2, 3, ...],
                    "is_nullable": false,
                    "is_primary_key": true,
                    "is_indexed": true
                },
                ...
            ]
    
    Returns:
        {
            'asset_id': str,
            'project_id': str,
            'columns_profiled': int,
            'pii_detected': int,
            'partition_candidates': int,
            'columns': [...],
            'summary': {...}
        }
    """
    # Get asset to verify project_id
    asset = await db.get_object_by_id(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
    
    project_id = asset.get('project_id')
    if not project_id:
        raise HTTPException(status_code=400, detail="Asset missing project_id")
    
    # Run Agent A column analysis
    agent_a = AgentAService(tenant_id=db.tenant_id, client_id=db.client_id)
    
    try:
        result = await agent_a.analyze_columns_deep(
            asset_id=asset_id,
            project_id=project_id,
            columns_metadata=columns_metadata,
            use_llm=False  # Set to True for LLM-enhanced PII detection (future)
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Column analysis failed: {str(e)}")


@router.get("/assets/{asset_id}/columns")
async def get_asset_columns(
    asset_id: str,
    db: SupabasePersistence = Depends(get_db)
):
    """
    Sprint 7: Retrieve profiled columns for an asset.
    
    Returns:
        {
            'asset_id': str,
            'columns': [
                {
                    'column_name': str,
                    'data_type': str,
                    'cardinality_ratio': float,
                    'null_percentage': float,
                    'is_pii': bool,
                    'pii_category': str,
                    'partition_candidate': bool,
                    ...
                },
                ...
            ]
        }
    """
    from apps.api.services.column_profiling_service import ColumnProfilingService
    
    profiler = ColumnProfilingService(tenant_id=db.tenant_id, client_id=db.client_id)
    
    try:
        columns = await profiler.get_asset_columns(asset_id)
        
        return {
            'asset_id': asset_id,
            'columns': columns,
            'total_columns': len(columns)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve columns: {str(e)}")


@router.get("/projects/{project_id}/pii-heatmap")
async def get_pii_heatmap(
    project_id: str,
    db: SupabasePersistence = Depends(get_db)
):
    """
    Sprint 7: Generate PII heatmap data for entire project.
    
    Returns:
        {
            'total_columns': int,
            'pii_columns': int,
            'pii_percentage': float,
            'pii_by_category': {'EMAIL': 5, 'SSN': 2, ...},
            'high_risk_assets': [asset_ids with 3+ PII columns],
            'asset_pii_counts': {asset_id: pii_count}
        }
    """
    from apps.api.services.column_profiling_service import ColumnProfilingService
    
    profiler = ColumnProfilingService(tenant_id=db.tenant_id, client_id=db.client_id)
    
    try:
        heatmap = await profiler.get_project_pii_heatmap(project_id)
        
        return heatmap
    
    except Exception as e:
        error_msg = str(e)
        # If table doesn't exist, return empty heatmap instead of 500
        if "does not exist" in error_msg or "PGRST" in error_msg or "utm_asset_columns" in error_msg:
            logger.warning(f"PII heatmap table not found, returning empty data: {e}")
            return {
                "total_columns": 0,
                "pii_columns": 0,
                "pii_percentage": 0.0,
                "pii_by_category": {},
                "high_risk_assets": [],
                "asset_pii_counts": {}
            }
        raise HTTPException(status_code=500, detail=f"Failed to generate PII heatmap: {str(e)}")


@router.get("/projects/{project_id}/partition-recommendations")
async def get_partition_recommendations(
    project_id: str,
    min_score: float = 0.5,
    db: SupabasePersistence = Depends(get_db)
):
    """
    Sprint 7: Get partition key recommendations for all assets in project.
    
    Args:
        project_id: UUID of the project
        min_score: Minimum partition score threshold (0.0-1.0, default 0.5)
    
    Returns:
        {
            'project_id': str,
            'recommendations': [
                {
                    'asset_id': str,
                    'column_name': str,
                    'partition_score': float,
                    'partition_reason': str,
                    'data_type': str,
                    'cardinality_ratio': float
                },
                ...
            ],
            'total_candidates': int
        }
    """
    try:
        # Query utm_asset_columns for partition candidates
        result = db.client.table('utm_asset_columns') \
            .select('asset_id, column_name, partition_score, partition_reason, data_type, cardinality_ratio') \
            .eq('project_id', project_id) \
            .eq('partition_candidate', True) \
            .gte('partition_score', min_score) \
            .order('partition_score', desc=True) \
            .execute()
        
        recommendations = result.data if result.data else []
        
        return {
            'project_id': project_id,
            'recommendations': recommendations,
            'total_candidates': len(recommendations)
        }
    
    except Exception as e:
        error_msg = str(e)
        # If table doesn't exist, return empty recommendations instead of 500
        if "does not exist" in error_msg or "PGRST" in error_msg or "utm_asset_columns" in error_msg:
            logger.warning(f"Partition recommendations table not found, returning empty data: {e}")
            return {
                "project_id": project_id,
                "recommendations": [],
                "total_candidates": 0
            }
        raise HTTPException(status_code=500, detail=f"Failed to get partition recommendations: {str(e)}")


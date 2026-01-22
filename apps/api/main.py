from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import shutil
from typing import Dict, Any, List, Optional

from services.agent_a_service import AgentAService
from services.graph_service import GraphService
from services.agent_c_service import AgentCService
from services.agent_f_service import AgentFService
from services.agent_g_service import AgentGService
from services.persistence_service import PersistenceService, SupabasePersistence
from services.discovery_service import DiscoveryService
from services.refinement.governance_service import GovernanceService
from supabase import create_client, Client

load_dotenv()

from apps.api.routers import config

app = FastAPI(title="Legacy2Lake API")

from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    err_msg = traceback.format_exc()
    print(f"GLOBAL ERROR: {err_msg}")
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "traceback": err_msg},
        headers={
            "Access-Control-Allow-Origin": "http://localhost:3005",
            "Access-Control-Allow-Credentials": "true"
        }
    )

app.include_router(config.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3005", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/prompts/agent-a")
async def get_agent_a_prompt():
    """Returns the current default system prompt for Agent A."""
    agent_a = AgentAService()
    return {"prompt": agent_a._load_prompt()}

@app.get("/prompts/agent-c")
async def get_agent_c_prompt():
    agent_c = AgentCService()
    return {"prompt": agent_c._load_prompt()}

@app.get("/prompts/agent-f")
async def get_agent_f_prompt():
    agent_f = AgentFService()
    return {"prompt": agent_f._load_prompt()}

@app.get("/prompts/agent-g")
async def get_agent_g_prompt():
    agent_g = AgentGService()
    return {"prompt": agent_g._load_prompt()}

@app.get("/ping")
async def ping():
    return {"status": "ok"}

# --- Prompt Management (Release 3.5 Phase 2) ---

class PromptUpdate(BaseModel):
    prompt: str

@app.post("/prompts/agent-a")
async def update_agent_a_prompt(payload: PromptUpdate):
    agent = AgentAService()
    agent.save_prompt(payload.prompt)
    return {"success": True}

@app.post("/prompts/agent-c")
async def update_agent_c_prompt(payload: PromptUpdate):
    agent = AgentCService()
    agent.save_prompt(payload.prompt)
    return {"success": True}

@app.post("/prompts/agent-f")
async def update_agent_f_prompt(payload: PromptUpdate):
    agent = AgentFService()
    agent.save_prompt(payload.prompt)
    return {"success": True}

@app.post("/prompts/agent-g")
async def update_agent_g_prompt(payload: PromptUpdate):
    agent = AgentGService()
    agent.save_prompt(payload.prompt)
    return {"success": True}

# --- Cartridges & Global Config ---

@app.get("/cartridges")
async def list_cartridges():
    """Returns available cartridges and their status."""
    db = SupabasePersistence()
    config = await db.get_global_config("cartridges")
    
    # Defaults
    defaults = {
        "pyspark": {"id": "pyspark", "name": "PySpark (Databricks)", "version": "v3.2", "desc": "Generates PySpark code optimized for Databricks Photon engine.", "enabled": True, "beta": False},
        "dbt": {"id": "dbt", "name": "dbt Core (Snowflake)", "version": "v1.8", "desc": "Generates dbt models, sources.yml, and generic tests.", "enabled": True, "beta": False},
        "sql": {"id": "sql", "name": "Pure SQL (Postgres/Redshift)", "version": "v1.0", "desc": "Generates Standard SQL scripts for ELT pipelines.", "enabled": False, "beta": True}
    }
    
    if not config:
        return list(defaults.values())
        
    # Merge defaults with config
    merged = []
    for key, default in defaults.items():
        saved = config.get(key, {})
        # Ensure deep merge for enabled status
        item = default.copy()
        if "enabled" in saved: item["enabled"] = saved["enabled"]
        merged.append(item)
    
    return merged

class CartridgeUpdate(BaseModel):
    id: str
    enabled: bool

@app.post("/cartridges/update")
async def update_cartridge_status(payload: CartridgeUpdate):
    """Updates the enabled status of a cartridge."""
    db = SupabasePersistence()
    config = await db.get_global_config("cartridges") or {}
    
    if payload.id not in config:
        config[payload.id] = {}
        
    config[payload.id]["enabled"] = payload.enabled
    await db.set_global_config("cartridges", config)
    return {"success": True}

# --- Provider Config ---

@app.get("/providers")
async def list_providers():
    """Returns available LLM providers and their status."""
    db = SupabasePersistence()
    config = await db.get_global_config("provider_settings")
    
    defaults = {
        "azure": {"id": "azure", "name": "Azure OpenAI", "model": "gpt-4", "enabled": True, "connected": False},
        "anthropic": {"id": "anthropic", "name": "Anthropic (Claude)", "model": "claude-3-5-sonnet", "enabled": False, "connected": False},
        "groq": {"id": "groq", "name": "Groq (Llama)", "model": "llama-3.1-70b", "enabled": False, "connected": False}
    }
    
    if not config:
        # Check env for connection status
        defaults["azure"]["connected"] = bool(os.getenv("AZURE_OPENAI_API_KEY"))
        return list(defaults.values())
        
    merged = []
    for key, default in defaults.items():
        saved = config.get(key, {})
        item = default.copy()
        item.update(saved)
        
        # Determine "Connected" status.
        # If saved has API key -> Connected.
        # If not, check Env.
        # Special case naming for Azure
        env_key_var = f"{key.upper()}_API_KEY"
        if key == "azure": env_key_var = "AZURE_OPENAI_API_KEY"
            
        has_key = bool(saved.get("api_key")) or bool(os.getenv(env_key_var))
             
        item["connected"] = has_key
        # Don't return API key
        if "api_key" in item: del item["api_key"]
            
        merged.append(item)
    
    return merged

class ProviderUpdate(BaseModel):
    id: str
    enabled: bool
    model: str = None
    api_key: str = None
    endpoint: str = None

@app.post("/providers/update")
async def update_provider(payload: ProviderUpdate):
    """Updates provider configuration."""
    db = SupabasePersistence()
    config = await db.get_global_config("provider_settings") or {}
    
    if payload.id not in config:
        config[payload.id] = {}
        
    config[payload.id]["enabled"] = payload.enabled
    if payload.model: config[payload.id]["model"] = payload.model
    if payload.endpoint: config[payload.id]["endpoint"] = payload.endpoint
    if payload.api_key: config[payload.id]["api_key"] = payload.api_key 
    
    await db.set_global_config("provider_settings", config)
    return {"success": True}






# --- Source & Generator Config (Release 4.1) ---

@app.get("/config/sources")
async def list_sources():
    """Returns configured source profiles (Knowledge Context)."""
    db = SupabasePersistence()
    
    # 1. Fetch available source technologies from metadata
    tech_res = supabase.table("utm_supported_techs").select("tech_id, label, description, version").eq("role", "SOURCE").eq("is_active", True).execute()
    tech_map = {t["tech_id"]: t for t in tech_res.data}
    
    # 2. Fetch configured profiles
    config = await db.get_global_config("sources") or {}
    
    # 3. Merge profile data with tech metadata
    results = []
    for sid, profile in config.items():
        tech_type = profile.get("type", "").upper()
        tech_info = tech_map.get(tech_type, {})
        results.append({
            **profile,
            "tech_label": tech_info.get("label", profile["type"]),
            "tech_description": tech_info.get("description"),
            "tech_version": tech_info.get("version")
        })
        
    return results

class SourceConfig(BaseModel):
    id: str
    name: str # e.g. "Legacy CRM"
    type: str # sqlserver, mysql, oracle, datastage
    version: Optional[str] = None # e.g. "2008 R2"
    description: Optional[str] = None 
    context_prompt: Optional[str] = None # Instructions for Agent A

@app.post("/config/sources")
async def save_source(payload: SourceConfig):
    """Saves a source profile."""
    db = SupabasePersistence()
    config = await db.get_global_config("sources") or {}
    
    # Store
    config[payload.id] = payload.dict()
    await db.set_global_config("sources", config)
    return {"success": True}

@app.delete("/config/sources/{source_id}")
async def delete_source(source_id: str):
    """Deletes a source profile."""
    db = SupabasePersistence()
    config = await db.get_global_config("sources") or {}
    
    if source_id in config:
        del config[source_id]
        await db.set_global_config("sources", config)
        return {"success": True}
    return {"success": False, "error": "Source not found"}

class GeneratorConfig(BaseModel):
    type: str # 'spark' or 'snowflake'
    instruction_prompt: Optional[str] = None # User override for system prompt

class GeneratorDefault(BaseModel):
    default: str # 'spark' or 'snowflake'

@app.get("/config/generators")
async def get_generator_config():
    """Returns generator configuration including defaults and overrides from DB metadata."""
    db = SupabasePersistence()
    
    # 1. Fetch config from global store (internal overrides like instruction_prompt)
    config = await db.get_global_config("generators") or {}
    default_gen_type = config.get("default", "DATABRICKS") # Default to Databricks ID

    # 2. Fetch all valid target technologies from metadata table
    res = supabase.table("utm_supported_techs").select("tech_id, label, description, version").eq("role", "TARGET").eq("is_active", True).execute()
    
    # 3. Transform and Merge with user overrides
    result_generators = []
    for tech in res.data:
        gen_type = tech["tech_id"]
        # Check if specific user override exists for this type
        gen_config = config.get(gen_type, {})
        
        result_generators.append({
            "id": f"gen_{gen_type.lower()}",
            "name": tech["label"],
            "type": gen_type,
            "version": tech["version"] or "Latest",
            "description": tech["description"],
            "instruction_prompt": gen_config.get("instruction_prompt", ""),
            "status": "active" if gen_type == default_gen_type else "inactive"
        })

    return {
        "default": default_gen_type,
        "generators": result_generators
    }

@app.post("/config/generators/update")
async def update_generator_config(payload: GeneratorConfig):
    """Updates specific generator instructions."""
    db = SupabasePersistence()
    config = await db.get_global_config("generators") or {}
    
    # Update specific generator config
    if payload.type not in config: config[payload.type] = {}
    
    # Ensure it's a dict
    if not isinstance(config[payload.type], dict):
        config[payload.type] = {}

    config[payload.type]["instruction_prompt"] = payload.instruction_prompt

    await db.set_global_config("generators", config)
    return {"success": True}

@app.post("/config/generators/default")
async def set_default_generator(payload: GeneratorDefault):
    """Sets the default code generation engine."""
    db = SupabasePersistence()
    config = await db.get_global_config("generators") or {}
    config["default"] = payload.default
    await db.set_global_config("generators", config)
    return {"success": True}

# Supabase Setup
url: str = os.getenv("SUPABASE_URL", "").strip()
key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
supabase: Client = create_client(url, key)

@app.get("/")
async def root():
    return {"message": "Welcome to Legacy2Lake API"}

@app.post("/ingest/dtsx")
async def ingest_dtsx(file: UploadFile = File(...)):
    """Ingest, analyze (Agent A), and build mesh (Agent B) for an SSIS package."""
    content = await file.read()
    content_str = content.decode('utf-8')
    
    # 1. Parse DTSX
    parser = SSISParser(content_str)
    summary = parser.get_summary()
    execs = parser.extract_executables()
    summary["executables"] = execs
    
    # 2. Agent A Discovery (Optional: background or async)
    agent_a = AgentAService()
    agent_a_report = await agent_a.analyze_package(summary)
    
    # 3. Agent B Graph Construction
    constraints = parser.extract_precedence_constraints()
    mesh = GraphService.build_mesh(execs, constraints)
    
    # 4. Persistence (Supabase)
    db = SupabasePersistence()
    project_id = await db.get_or_create_project(file.filename)
    asset_id = await db.save_asset(
        project_id, 
        file.filename, 
        content_str, 
        "DTSX", 
        parser.get_hash(content_str)
    )
    
    return {
        "filename": file.filename,
        "hash": parser.get_hash(content_str),
        "agent_a": agent_a_report,
        "mesh": mesh,
        "asset_id": asset_id
    }

class TranspileRequest(BaseModel):
    node_data: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None

class RegistryEntry(BaseModel):
    category: str
    key: str
    value: Any

@app.post("/transpile/task")
async def transpile_task(payload: TranspileRequest):
    """Chain Agent C (Interpreter) and Agent F (Critic) for a robust result."""
    node_data = payload.node_data
    context = payload.context or {}
    # 1. Generate initial code (Agent C)
    agent_c = AgentCService()
    c_result = await agent_c.transpile_task(node_data, context)
    
    if "error" in c_result:
        return c_result

    # 2. Audit and Optimize (Agent F)
    agent_f = AgentFService()
    f_result = await agent_f.review_code(node_data, c_result["pyspark_code"])
    
    # 3. Persistence (Local & Supabase)
    solution_name = context.get("solution_name", "DefaultProject")
    task_name = node_data.get("name", "UnnamedTask")
    
    local_path = PersistenceService.save_transformation(
        solution_name, 
        task_name, 
        f_result.get("optimized_code") or c_result["pyspark_code"]
    )
    
    # 4. Persistence (Supabase)
    asset_id = context.get("asset_id")
    if asset_id:
        db = SupabasePersistence()
        await db.save_transformation(
            asset_id,
            node_data.get("description", ""), # source info
            f_result.get("optimized_code") or c_result["pyspark_code"]
        )

    return {
        "interpreter": c_result,
        "critic": f_result,
        "final_code": f_result.get("optimized_code") or c_result["pyspark_code"],
        "saved_at": local_path
    }

@app.post("/transpile/all")
async def transpile_all(nodes: List[Dict[str, Any]], context: Dict[str, Any] = None):
    """Iteratively transpile all nodes in a mesh."""
    results = []
    agent_c = AgentCService()
    agent_f = AgentFService()
    db = SupabasePersistence()
    
    solution_name = context.get("solution_name", "BulkProject")
    asset_id = context.get("asset_id")

    for node in nodes:
        node_data = node.get("data", {})
        # Skip purely decorative or empty nodes
        if not node_data.get("label"):
            continue
            
        # 1. Generate
        c_res = await agent_c.transpile_task(node_data, context)
        if "error" in c_res:
            results.append({"node": node_data.get("label"), "status": "FAILED", "error": c_res["error"]})
            continue
            
        # 2. Audit
        f_res = await agent_f.review_code(node_data, c_res["pyspark_code"])
        final_code = f_res.get("optimized_code") or c_res["pyspark_code"]
        
        # 3. Save Local
        local_path = PersistenceService.save_transformation(
            solution_name,
            node_data.get("name", node_data.get("label")),
            final_code
        )
        
        # 4. Save Supabase
        if asset_id:
            await db.save_transformation(
                asset_id,
                node_data.get("description", ""), # source info
                final_code
            )
        
        results.append({
            "node": node_data.get("label"),
            "status": "SUCCESS",
            "score": f_res.get("score"),
            "path": local_path
        })
        
    return {"summary": results, "solution_path": os.path.join(PersistenceService.BASE_DIR, solution_name)}

@app.post("/governance/document")
async def generate_governance(project_name: str, mesh: Dict[str, Any], context: Dict[str, Any] = None):
    """Generates and persists technical/governance documentation."""
    # 1. Fetch transformations for this project from Supabase
    db = SupabasePersistence()
    asset_id = context.get("asset_id") if context else None
    
    transformations = []
    if asset_id:
        res = db.client.table("transformations").select("target_code").eq("asset_id", asset_id).execute()
        transformations = res.data

    # 2. Invoke Agent G
    agent_g = AgentGService()
    doc_content = await agent_g.generate_documentation(project_name, mesh, transformations)
    
    # 3. Save Local
    solution_name = context.get("solution_name", "GovernanceProject") if context else "GovernanceProject"
    local_path = PersistenceService.save_documentation(solution_name, "GOVERNANCE", doc_content)
    
    return {
        "status": "success",
        "documentation": doc_content,
        "saved_at": local_path
    }

@app.post("/projects/{project_id}/stage")
async def update_stage(project_id: str, payload: Dict[str, str]):
    db = SupabasePersistence()
    success = await db.update_project_stage(project_id, payload.get("stage"))
    return {"success": success}

@app.patch("/projects/{project_id}/settings")
async def update_project_settings(project_id: str, settings: Dict[str, Any]):
    """Updates project-level settings (e.g. Source/Target Tech)."""
    db = SupabasePersistence()
    success = await db.update_project_settings(project_id, settings)
    return {"success": success}

@app.post("/projects/{project_id}/layout")
async def save_layout(project_id: str, layout: Dict[str, Any]):
    db = SupabasePersistence()
    asset_id = await db.save_project_layout(project_id, layout)
    return {"success": True, "asset_id": asset_id}

@app.get("/projects/{project_id}/layout")
async def get_layout(project_id: str):
    db = SupabasePersistence()
    layout = await db.get_project_layout(project_id)
    return layout or {}

@app.get("/projects")
async def list_projects():
    """Returns a list of all projects."""
    db = SupabasePersistence()
    return await db.list_projects()

@app.get("/projects/{project_id}")
async def get_project(project_id: str):
    """Returns project details, handling both UUID and Name."""
    db = SupabasePersistence()
    
    # 1. Try to find by UUID first
    metadata = await db.get_project_metadata(project_id)
    if metadata:
        return metadata
    
    # 2. Fallback: maybe the string passed is the project Name?
    uuid = await db.get_project_id_by_name(project_id)
    if uuid:
        metadata = await db.get_project_metadata(uuid)
        if metadata:
            return metadata
        
    return {"error": "Project not found"}

@app.get("/discovery/project/{project_id}")
async def get_discovery_project(project_id: str):
    """Returns all assets and the system prompt for a project."""
    db = SupabasePersistence()
    project_uuid = project_id
    if "-" not in project_id:
        u = await db.get_project_id_by_name(project_id)
        if u: project_uuid = u
        
    assets = await db.get_project_assets(project_uuid)
    meta = await db.get_project_metadata(project_uuid)
    
    # Fallback to default Triage prompt if not customized for project
    prompt = meta.get("prompt") if meta else None
    if not prompt:
        agent_a = AgentAService()
        prompt = agent_a._load_prompt()
        
    return {
        "assets": assets,
        "prompt": prompt
    }

@app.patch("/projects/{project_id}/prompt")
async def update_project_prompt(project_id: str, payload: Dict[str, str]):
    """Updates the customized system prompt for a project."""
    db = SupabasePersistence()
    success = await db.update_project_prompt(project_id, payload.get("prompt"))
    return {"success": success}

@app.patch("/assets/{asset_id}")
async def patch_asset(asset_id: str, updates: Dict[str, Any]):
    """Updates asset metadata (type, selected status)."""
    db = SupabasePersistence()
    success = await db.update_asset_metadata(asset_id, updates)
    return {"success": success}

@app.get("/projects/{project_id}/assets")
async def get_project_assets(project_id: str):
    """Returns a scanned inventory of project assets."""
    db = SupabasePersistence()
    # We return the PERSISTED assets from the DB.
    resolved_uuid = project_id
    if "-" not in project_id: # Heuristic for UUID
        u = await db.get_project_id_by_name(project_id)
        if u: resolved_uuid = u
            
    assets = await db.get_project_assets(resolved_uuid)
    return {"assets": assets}

class TriageParams(BaseModel):
    system_prompt: Optional[str] = None
    user_context: Optional[str] = None

@app.post("/projects/{project_id}/triage")
async def run_triage(project_id: str, params: TriageParams):
    """Re-runs the triage (discovery) process using agentic reasoning."""
    db = SupabasePersistence()
    
    # Resolve UUID and Name correctly
    project_uuid = project_id
    project_folder = project_id
    
    if "-" in project_id: # Heuristic: if UUID, get name for folder
        resolved_name = await db.get_project_name_by_id(project_id)
        if resolved_name:
            project_folder = resolved_name
    else: # If name, get UUID for DB operations
        resolved_uuid = await db.get_project_id_by_name(project_id)
        if resolved_uuid:
            project_uuid = resolved_uuid

    # GOVERNANCE CHECK: TRIAGE is only allowed in TRIAGE mode.
    current_status = await db.get_project_status(project_uuid)
    if current_status == "DRAFTING":
        return {
            "assets": [],
            "log": "[ERROR] Project is in DRAFTING mode. Triage is locked. Unlock project to modify scope.",
            "error": "Project is in DRAFTING mode"
        }

    log_lines = []
    log_lines.append(f"[Start] Initializing Shift-T Triage Agent for Project: {project_id} (Folder: {project_folder})")
    
    # Helper to persist log incrementally
    def _log(msg: str):
        log_lines.append(msg)
        try:
            path = PersistenceService.ensure_solution_dir(project_folder)
            with open(os.path.join(path, "triage.log"), "a", encoding="utf-8") as f:
                f.write(f"{msg}\n")
        except:
            pass
            
    # Clear previous log
    try:
        path = PersistenceService.ensure_solution_dir(project_folder)
        with open(os.path.join(path, "triage.log"), "w", encoding="utf-8") as f:
            f.write(f"--- Triage Started for {project_id} ---\n")
    except:
        pass
    
    _log(f"[Start] Initializing Shift-T Triage Agent for Project: {project_id}")

    # 1. Deep Scan (The Scanner / Pre-processing)
    _log("[Step 1] Running Deep Scanner (Python Engine)...")
    
    # NEW: Fetch persistent human context
    user_context = await db.get_project_context(project_uuid)
    if user_context:
        _log(f"   > Found {len(user_context)} human context overrides. Injecting into scanner...")
        
    manifest = DiscoveryService.generate_manifest(project_folder, user_context=user_context)
    manifest["project_id"] = project_uuid # Ensure UUID is used for DB lookups in agents
    
    file_count = len(manifest["file_inventory"])
    tech_stats = manifest["tech_stats"]
    _log(f"   > Scanned {file_count} files.")
    _log(f"   > Tech Stack Detected: {tech_stats}")
    
    # 2. Agent A Analysis (The Detective)
    _log("[Step 2] Invoking Agent A (Mesh Architect)...")
    if params.system_prompt:
        _log("   > Applying custom System Prompt override.")
    
    agent_a = AgentAService()
    try:
        # Pass user_context as part of the system prompt or prepend to user message? 
        # Ideally we prepend it to the prompt.
        prompt = params.system_prompt
        if params.user_context:
            prompt = (prompt or "") + f"\n\n[USER CONTEXT CONSTRAINTS]:\n{params.user_context}"
            
        result = await agent_a.analyze_manifest(manifest, system_prompt_override=prompt)
        
        if "error" in result:
             _log(f"[ERROR] Agent A failed: {result['error']}")
             return {"log": "\n".join(log_lines), "error": result['error']}
             
        rf_nodes = result.get("mesh_graph", {}).get("nodes", [])
        rf_edges = result.get("mesh_graph", {}).get("edges", [])
        
        # Auto-Promotion Fallback: Ensure CORE-likely physical assets are in the graph
        for item in manifest["file_inventory"]:
             # Explicitly exclude system files from being promoted as nodes
             if item["name"].lower() in ['triage.log', 'thumbs.db', '.ds_store', 'desktop.ini']:
                 continue
                 
             if not any(n["id"] == item["path"] for n in rf_nodes):
                 ext = item["name"].split('.')[-1].lower() if '.' in item["name"] else ''
                 # We promote SSIS, SQL and Python/Spark files to nodes by default
                 # BUT only if they are likely CORE logic (as requested by user)
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
        
        _log(f"   > Analysis Complete. Total Nodes (AI + Inferred): {len(rf_nodes)}")
        
    except Exception as e:
        _log(f"[CRITICAL] Architecture Analysis Failed: {e}")
        return {"log": "\n".join(log_lines), "error": str(e)}

    # 3. Persistence (Supabase)
    _log("[Step 3] Persisting Mesh Graph and Discovered Assets...")
    
    # NEW: Persist the scanner inventory to DB
    db_assets = []
    for item in manifest["file_inventory"]:
        # Find agent info for this file in Agent A nodes
        agent_node = next((n for n in rf_nodes if n["id"] == item["path"]), None)
        
        # Determine category (type in DB)
        category = agent_node["category"] if agent_node else "IGNORED" 
        if not agent_node:
            # Fallback for files not analyzed by Agent A
            category = DiscoveryService._map_extension_to_type(item["name"].split('.')[-1].lower() if '.' in item["name"] else 'none')

        db_assets.append({
            "filename": item["name"],
            "type": category,
            "source_path": item["path"],
            "metadata": {**item.get("metadata", {}), "size": item["size"]},
            "selected": True if category != "IGNORED" else False
        })
    
    saved_assets = await db.batch_save_assets(project_uuid, db_assets)
    # Create lookup map for UUIDs: source_path -> id
    asset_map = { a["source_path"]: (a.get("id") or a.get("object_id")) for a in saved_assets }

    # Transform Agent Nodes to ReactFlow Nodes
    final_nodes = []
    # Filter for graph: Only show CORE and SUPPORT nodes.
    graph_eligible = [n for n in rf_nodes if n.get("category") != "IGNORED"]
    
    for i, n in enumerate(graph_eligible):
        # Resolve UUID for this node
        n_uuid = asset_map.get(n["id"], n["id"])
        
        final_nodes.append({
            "id": n_uuid,
            "type": "custom", 
            "position": {"x": 200 + (i % 5 * 250), "y": 100 + (i // 5 * 150)},
            "data": { 
                "label": n["label"], 
                "category": n.get("category", "CORE"),
                "complexity": n.get("complexity", "LOW"),
                "status": "pending"
            }
        })
        
    final_edges = []
    for e in rf_edges:
        src_uid = asset_map.get(e['from'], e['from'])
        tgt_uid = asset_map.get(e['to'], e['to'])
        
        final_edges.append({
            "id": f"e{src_uid}-{tgt_uid}",
            "source": src_uid,
            "target": tgt_uid,
            "label": e.get('type', 'SEQUENTIAL')
        })
        
    await db.save_project_layout(project_uuid, {"nodes": final_nodes, "edges": final_edges})
    _log("[Success] Graph and Assets saved to database.")
    
    # Map back to assets list for the frontend
    final_assets = []
    for item in manifest["file_inventory"]:
        agent_node = next((n for n in rf_nodes if n["id"] == item["path"]), None)
        item_uuid = asset_map.get(item["path"])
        
        if item_uuid:
            final_assets.append({
                "id": item_uuid,
                "name": item["name"],
                "type": agent_node["category"] if agent_node else "CORE",
                "status": "analyzed" if agent_node else "unlinked",
                "tags": str(item["signatures"]),
                "selected": True if (agent_node and agent_node["category"] != "IGNORED") else False,
                "dependencies": []
            })

    return {
        "assets": final_assets,
        "nodes": final_nodes,
        "edges": final_edges,
        "log": "\n".join(log_lines)
    }

@app.get("/discovery/status/{project_id}")
async def get_discovery_status(project_id: str):
    """Returns the discovery/triage status for a project."""
    db = SupabasePersistence()
    metadata = await db.get_project_metadata(project_id)
    if not metadata:
        # Fallback to name
        uuid = await db.get_project_id_by_name(project_id)
        if uuid: metadata = await db.get_project_metadata(uuid)

    if not metadata:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # If the project is in stage 1, discovery is either in progress or done but not approved.
    # If status is TRIAGE and it has logs, it's 'active'.
    # If it has assets, we can say it's 'complete'.
    return {
        "status": metadata.get("status", "TRIAGE"),
        "stage": metadata.get("stage", "1"),
        "is_ready": metadata.get("status") != "TRIAGE" or metadata.get("stage") != "1"
    }

@app.post("/projects/{project_id}/sync-graph")
async def sync_project_graph(project_id: str):
    """Rebuilds the graph layout based on assets currently marked as 'selected'."""
    db = SupabasePersistence()
    project_uuid = project_id
    if len(project_id) < 32:
        project_uuid = await db.get_project_id_by_name(project_id)

    if not project_uuid:
        raise HTTPException(status_code=404, detail="Project not found")

    # 1. Fetch assets marked as selected
    assets = await db.get_project_assets(project_uuid)
    selected_assets = [a for a in assets if a.get("selected")]

    # 2. Fetch current layout to preserve positions for existing nodes if possible
    current_layout = await db.get_project_layout(project_uuid)
    existing_nodes = {n["id"]: n for n in current_layout.get("nodes", [])}
    existing_edges = current_layout.get("edges", [])

    # 3. Build new node list
    final_nodes = []
    for i, asset in enumerate(selected_assets):
        asset_id = asset["id"]
        
        if asset_id in existing_nodes:
            # Preserve existing node
            final_nodes.append(existing_nodes[asset_id])
        else:
            # Create new node
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

    # 4. Filter edges: Only keep edges where BOTH source and target exist in final_nodes
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

@app.post("/transpile/optimize")
async def optimize_task_code(payload: Dict[str, Any]):
    """Re-runs Agent F with specific optimization flags."""
    code = payload.get("code")
    optimizations = payload.get("optimizations", [])
    
    agent_f = AgentFService()
    result = await agent_f.optimize_code(code, optimizations)
    
    # 3. Persistence (If context provided, we could save, but for refinement loop usually we wait for 'Approve')
    # For R2 demo, we just return the result.
    
    return result

@app.get("/solutions/{id}/export")
async def export_solution(id: str):
    """Zips the solution folder and returns it."""
    # ... (existing code) ...
    from fastapi.responses import FileResponse
    # ...
    return FileResponse(final_zip, media_type='application/zip', filename=f"{zip_filename}.zip")

# Consolidated Routes handled above

@app.post("/projects/create")
async def create_project(
    name: str = Form(...),
    project_id: str = Form(...),
    source_type: str = Form(...),
    github_url: str = Form(None),
    overwrite: bool = Form(False),
    file: UploadFile = File(None)
):
    """Creates a new project and initializes it from source."""
    
    # 1. Register in Database (Supabase)
    db = SupabasePersistence()
    real_id = await db.get_or_create_project(name, github_url) # Pass github_url
    # Note: get_or_create_project returns ID based on name. 
    # For this demo, we assume the user-generated 'project_id' matches or we just use the ID returned by DB for folder.
    
    # 2. Handle File Upload (Save temporarily)
    temp_zip_path = None
    if source_type == "zip" and file:
        temp_zip_path = os.path.join(PersistenceService.BASE_DIR, f"{project_id}_temp.zip")
        with open(temp_zip_path, "wb") as buffer:
            import shutil
            shutil.copyfileobj(file.file, buffer)
            
    # 3. Initialize Directory
    success = PersistenceService.initialize_project_from_source(
        project_id=project_id,
        source_type=source_type,
        file_path=temp_zip_path,
        github_url=github_url,
        overwrite=overwrite
    )
    
    if success:
        return {"success": True, "project_id": project_id}
    else:
        return {"success": False, "error": "Failed to initialize project"}

@app.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """Deletes a project from both DB and Filesystem."""
    db = SupabasePersistence()
    
    # 1. Fetch Project Name for Folder Deletion
    project_name = await db.get_project_name_by_id(project_id)
    
    # 2. Delete from DB
    db_success = await db.delete_project(project_id)
    
    # 3. Delete from FS
    fs_success = False
    if project_name:
        fs_success = PersistenceService.delete_project_directory(project_name)
    else:
        # Fallback: maybe the ID passed IS the name (if simplified elsewhere)
        fs_success = PersistenceService.delete_project_directory(project_id)
    
    return {
        "success": True, 
        "details": {
            "db_deleted": db_success,
            "fs_deleted": fs_success
        }
    }

@app.get("/projects/{project_id}/files")
async def list_project_files(project_id: str):
    """Returns the file tree for the project's output directory."""
    # Release 3.5: DB First Inventory
    db = SupabasePersistence()
    
    # get_project_files_from_db checks DB, if empty syncs from Project Name/ID
    tree = await db.get_project_files_from_db(project_id)
    
    # We need to determine the root folder name. 
    # If project_id is a UUID, we might want the friendly name back for the root node.
    project_name = project_id
    if "-" in project_id:
        n = await db.get_project_name_by_id(project_id)
        if n: project_name = n
        
    # Wrap in a root node for the frontend FileExplorer
    return {
        "name": project_name,
        "type": "folder",
        "path": project_name,
        "children": tree
    }

@app.get("/projects/{project_id}/files/content")
async def get_file_content(project_id: str, path: str):
    """Returns the content of a specific file."""
    # Resolve Project Name if ID is UUID
    db = SupabasePersistence()
    project_name = project_id
    if "-" in project_id:
        n = await db.get_project_name_by_id(project_id)
        if n: project_name = n
        
    try:
        content = PersistenceService.read_file_content(project_name, path)
        return {"content": content}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to read file: {e}"}

from services.migration_orchestrator import MigrationOrchestrator

@app.post("/transpile/orchestrate")
async def trigger_orchestration(payload: Dict[str, Any]):
    """Triggers the full Migration Orchestrator (Agents C -> F -> G)."""
    print(f"DEBUG: Entering trigger_orchestration with payload: {payload}")
    project_id = payload.get("project_id")
    limit = payload.get("limit", 0)
    
    if not project_id:
        return {"error": "project_id is required"}
        
    # 1. Resolve Project Name (Orchestrator expects Name/Folder currently)
    db = SupabasePersistence()
    project_name = project_id
    if "-" in project_id:
        print(f"DEBUG: Resolving project name for ID: {project_id}")
        n = await db.get_project_name_by_id(project_id)
        print(f"DEBUG: Resolved project name: {n}")
        if n: project_name = n

    print(f"DEBUG: Instantiating MigrationOrchestrator for {project_name} (UUID: {project_id})")
    orchestrator = MigrationOrchestrator(project_name, project_uuid=project_id)
    print("DEBUG: Running full migration...")
    result = await orchestrator.run_full_migration(limit=limit)
    print("DEBUG: Migration complete.")
    return result

@app.get("/projects/{project_id}/logs")
async def get_project_logs(project_id: str):
    """Returns the orchestration logs for the project."""
    db = SupabasePersistence()
    project_name = project_id
    if "-" in project_id:
        n = await db.get_project_name_by_id(project_id)
        if n: project_name = n
        
    try:
        content = PersistenceService.read_file_content(project_name, "migration.log")
        return {"logs": content}
    except Exception:
        return {"logs": ""}

@app.post("/projects/{project_id}/reset")
async def reset_project(project_id: str):
    """Clears triage results for a project, resetting it to stage 1."""
    db = SupabasePersistence()
    success = await db.reset_project_data(project_id)
    return {"success": success}

@app.post("/projects/{project_id}/approve")
async def approve_triage(project_id: str):
    """Locks the project scope and transitions to DRAFTING state."""
    db = SupabasePersistence()
    
    # Heuristic: verify UUID vs Name
    project_uuid = project_id
    if "-" not in project_id:
        u = await db.get_project_id_by_name(project_id)
        if u: project_uuid = u

    # Check validation rules? (e.g. must have assets selected)
    # For now, just transition.
    success_status = await db.update_project_status(project_uuid, "DRAFTING")
    success_stage = await db.update_project_stage(project_uuid, "2")
    return {"success": success_status and success_stage, "status": "DRAFTING"}

@app.post("/projects/{project_id}/unlock")
async def unlock_triage(project_id: str):
    """Unlocks the project scope and transitions back to TRIAGE state."""
    db = SupabasePersistence()
    
    project_uuid = project_id
    if "-" not in project_id:
        u = await db.get_project_id_by_name(project_id)
        if u: project_uuid = u

    success = await db.update_project_status(project_uuid, "TRIAGE")
    return {"success": success, "status": "TRIAGE"}

@app.get("/projects/{project_id}/logs")
async def get_project_logs(project_id: str, type: str = "Triage"):
    """
    Fetches execution logs from the database.
    Release 3.5: Moved to 'utm_execution_logs'.
    """
    db = SupabasePersistence()
    
    # Map frontend type to DB phase
    phase_map = {
        "triage": "TRIAGE", 
        "migration": "MIGRATION", 
        "refinement": "REFINEMENT"
    }
    phase = phase_map.get(type.lower(), "TRIAGE")
    
    logs = await db.get_execution_logs(project_id, phase)
    
    log_lines = []
    for log in logs:
        timestamp = log.get("created_at", "")
        step = log.get("step", "System")
        msg = log.get("message", "")
        # Format: [Timestamp] [Step] Message
        log_lines.append(f"[{timestamp}] [{step}] {msg}")
        
    return {"logs": "\n".join(log_lines)}


# --- Phase 3: Refinement Endpoints ---
from services.refinement.refinement_orchestrator import RefinementOrchestrator

@app.post("/refine/start")
async def start_refinement(payload: dict):
    """Triggers the Refinement Phase (Profiler -> Architect -> Refactor -> Ops)."""
    project_id = payload.get("project_id")
    if not project_id:
        return {"error": "Project ID required"}
    
    # Resolve Project Name for File System Access
    db = SupabasePersistence()
    project_name = project_id
    if "-" in project_id:
        # Resolve UUID to Name (e.g. "c522..." -> "base")
        n = await db.get_project_name_by_id(project_id)
        if n: project_name = n

    print(f"DEBUG: Starting Refinement for {project_id} (Resolved Folder: {project_name})")
    
    # Orchestrator is now natively async (Release 2.0)
    orchestrator = RefinementOrchestrator()
    result = await orchestrator.start_pipeline(project_name)
    
    print(f"DEBUG: Refinement Complete for {project_id}")
    return result


@app.get("/projects/{project_id}/refinement/state")
async def get_refinement_state(project_id: str):
    """Returns the persisted state of Phase 3 (logs and profile)."""
    db = SupabasePersistence()
    project_name = project_id
    if "-" in project_id:
        n = await db.get_project_name_by_id(project_id)
        if n: project_name = n

    state = {
        "log": [],
        "profile": None
    }

    try:
        # 1. Fetch Logs
        log_content = PersistenceService.read_file_content(project_name, "refinement.log")
        if log_content:
            state["log"] = log_content.split("\n")
    except:
        pass

    try:
        # 2. Fetch Profile Metadata
        profile_content = PersistenceService.read_file_content(project_name, "Refined/profile_metadata.json")
        if profile_content:
            import json
            state["profile"] = json.loads(profile_content)
    except:
        pass

    return state


@app.get("/projects/{project_id}/status")
async def get_project_status(project_id: str):
    """Returns the current governance status."""
    db = SupabasePersistence()
    
    project_uuid = project_id
    if "-" not in project_id:
        u = await db.get_project_id_by_name(project_id)
        if u: project_uuid = u
        
    status = await db.get_project_status(project_uuid)
    return {"status": status}


@app.get("/projects/{project_id}/governance")
async def get_governance(project_id: str):
    """Returns the certification report and lineage for the project."""
    db = SupabasePersistence()
    project_name = project_id
    if "-" in project_id:
        n = await db.get_project_name_by_id(project_id)
        if n: project_name = n

    service = GovernanceService()
    try:
        report = service.get_certification_report(project_name)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Release 1.1: Context Injection Endpoints ---

class AssetContextPayload(BaseModel):
    source_path: str
    notes: str
    rules: Optional[Dict[str, Any]] = None

@app.post("/projects/{project_id}/context")
async def save_context(project_id: str, payload: AssetContextPayload):
    """Saves human context for an asset."""
    db = SupabasePersistence()
    project_uuid = project_id
    if "-" not in project_id:
        u = await db.get_project_id_by_name(project_id)
        if u: project_uuid = u
        
    success = await db.save_asset_context(
        project_uuid, 
        payload.source_path, 
        payload.notes, 
        payload.rules
    )
    return {"success": success}

@app.get("/projects/{project_id}/context")
async def get_context(project_id: str):
    """Retrieves all context entries for a project."""
    db = SupabasePersistence()
    project_uuid = project_id
    if "-" not in project_id:
        u = await db.get_project_id_by_name(project_id)
        if u: project_uuid = u
        
    context_entries = await db.get_project_context(project_uuid)
    return {"context": context_entries}


@app.get("/projects/{project_id}/export")
async def export_project(project_id: str):
    """Streams the project solution as a ZIP bundle."""
    db = SupabasePersistence()
    project_name = project_id
    if "-" in project_id:
        n = await db.get_project_name_by_id(project_id)
        if n: project_name = n

    service = GovernanceService()
    try:
        zip_buffer = service.create_export_bundle(project_name)
        filename = f"ShiftT_Solution_{project_name}.zip"
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/x-zip-compressed",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
@app.get("/projects/{project_id}/registry")
async def get_project_registry(project_id: str):
    """Retrieves all global design rules for a project."""
    db = SupabasePersistence()
    registry = await db.get_design_registry(project_id)
    return {"registry": registry}

@app.post("/projects/{project_id}/registry")
async def update_project_registry(project_id: str, entry: RegistryEntry):
    """Upserts a specific design rule."""
    db = SupabasePersistence()
    success = await db.update_design_registry(
        project_id, 
        entry.category, 
        entry.key, 
        entry.value
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update registry")
    return {"status": "success"}

@app.post("/projects/{project_id}/registry/initialize")
async def initialize_project_registry(project_id: str):
    """Seeds default design standards for a new project."""
    db = SupabasePersistence()
    success = await db.initialize_design_registry(project_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to initialize registry")
    return {"status": "success"}

# --- Release v1.5: Executable Governance (Design Registry) ---
from services.knowledge_service import KnowledgeService

@app.get("/projects/{project_id}/registry")
async def get_project_registry(project_id: str):
    """Fetches the Design Registry (Governance Rules) for a project."""
    db = SupabasePersistence()
    
    # Resolve Name -> ID if needed (Endpoints usually take ID, but robust handling is good)
    # The get_design_registry function in DB handles robust lookup if we pass strictly UUID?
    # Actually DB methods usually handle "ID or Name" if implemented that way, 
    # but let's check get_design_registry implementation in PersistenceService. 
    # It seems to handle it.
    
    registry = await db.get_design_registry(project_id)
    
    # Merge with Defaults (Release 3.0 Migration Logic)
    # Ensure new keys (e.g. target_stack) appear for existing projects
    defaults = KnowledgeService.get_default_registry_entries(project_id)
    
    # Create a lookup for existing keys to avoid duplicates
    existing_keys = set()
    for r in registry:
        # Handle if r is dict or object
        cat = r.get('category') if isinstance(r, dict) else r.category
        key = r.get('key') if isinstance(r, dict) else r.key
        existing_keys.add((cat, key))
        
    missing_defaults = []
    for d in defaults:
        if (d['category'], d['key']) not in existing_keys:
            missing_defaults.append(d)
            
    if missing_defaults:
        print(f"[DEBUG] Merging {len(missing_defaults)} missing defaults for {project_id}: {[d['key'] for d in missing_defaults]}")
        registry.extend(missing_defaults)
        
    return {"registry": registry}
    
    # (Removed redundant empty check block previously here)
        
    return {"registry": registry}

@app.post("/projects/{project_id}/registry")
async def update_project_registry(project_id: str, payload: dict):
    """Updates a specific Design Rule."""
    db = SupabasePersistence()
    
    category = payload.get("category")
    key = payload.get("key")
    value = payload.get("value")
    
    if not category or not key:
        return {"success": False, "error": "Category and Key are required"}
        
    # Resolve Name -> ID for update
    # update_design_registry takes project_id. 
    # Let's ensure we find the UUID first to be safe, as DB method might expect UUID for FKs?
    # The DB method `update_design_registry` takes project_id and internally upserts.
    # It doesn't seem to have name resolution inside. Let's do it here.
    
    project_uuid = project_id
    if "-" not in project_id:
         u = await db.get_project_id_by_name(project_id)
         if u: project_uuid = u
         
    success = await db.update_design_registry(project_uuid, category, key, value)
    return {"success": success}

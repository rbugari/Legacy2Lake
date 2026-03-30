from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
import time
import asyncio
import warnings
import ssl
import traceback
from datetime import datetime
import logging

# Ensure apps/api is on sys.path for legacy imports (services.*, routers.*)
api_root = os.path.dirname(os.path.abspath(__file__))
if api_root not in sys.path:
    sys.path.insert(0, api_root)

# CRITICAL: Disable SSL verification BEFORE any imports
os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''

from dotenv import load_dotenv

# Suppress SSL warnings for development (Supabase self-signed certs)
warnings.filterwarnings('ignore', message='Unverified HTTPS request')
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Create unverified SSL context globally for development
ssl._create_default_https_context = ssl._create_unverified_context

# Monkey-patch httpcore to disable SSL verification at the lowest level
try:
    import httpcore
    import httpcore._backends.sync
    
    _original_start_tls = httpcore._backends.sync.SyncStream.start_tls
    
    def _patched_start_tls(self, *args, **kwargs):
        # Force SSL context without verification
        import ssl
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        kwargs['ssl_context'] = ssl_context
        return _original_start_tls(self, *args, **kwargs)
    
    httpcore._backends.sync.SyncStream.start_tls = _patched_start_tls
    print("[OK] SSL verification disabled via httpcore monkey-patch")
except Exception as e:
    print(f"[WARN] Could not monkey-patch httpcore: {e}")

# Fix for Windows asyncio subprocess support
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Environment & Logging
load_dotenv()
from apps.api.utils.logger import logger
from apps.api.services.persistence_service import SupabasePersistence

# Sprint 6: Security enhancements
from apps.api.middleware.rate_limiter import RateLimitMiddleware
from apps.api.services.audit_log_service import init_audit_service
from apps.api.routers.dependencies import get_supabase_client

# Import Routers
from apps.api.routers import system, config # Standardize path
from apps.api.routers.auth import router as auth_router
from apps.api.routers.agents import router as agents_router
from apps.api.routers.projects import router as projects_router
from apps.api.routers.project_members import router as project_members_router
from apps.api.routers.triage import router as triage_router
from apps.api.routers.transpile import router as transpile_router
from apps.api.routers.governance import router as governance_router
from apps.api.routers.lab import router as lab_router
from apps.api.routers.reports import router as reports_router
from apps.api.routers.locks import router as locks_router
from apps.api.routers.visualization import router as visualization_router  # Sprint 13: Visualization endpoints
from apps.api.routers.prompts import router as prompts_router  # v4.0: Zero-Hardcode Core
from apps.api.routers.gaps import router as gaps_router  # Sprint 3: Gap & Decision Workspace
from apps.api.routers.dependencies import get_db

app = FastAPI(
    title="Legacy2Lake API", 
    version="3.9.0",  # Sprint 13: Visualization + Full Debug Logging
    description="Refactored Core API for Cloud-Native Multi-Tenant Architecture with Formalized Governance"
)

# --- STARTUP INITIALIZATION (Sprint 6) ---

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("\n" + "=" * 60)
    print("🚀 Legacy2Lake API Starting...")
    print("=" * 60)
    
    # Check if DEBUG_MODE is enabled
    debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
    print(f"🔍 DEBUG_MODE: {'ENABLED ✅' if debug_mode else 'DISABLED ❌'}")
    
    if debug_mode:
        print("   • All LLM calls will be logged")
        print("   • Agent inputs/outputs visible")
        print("   • DB queries tracked")
        print("   • Full request/response details")
    else:
        print("   ⚠️  Set DEBUG_MODE=true for verbose logging")
    
    print("=" * 60 + "\n")
    sys.stdout.flush()
    
    # Test logger writes to file
    logger.info("🚀 BACKEND STARTED - Logger Active", "Startup")
    logger.info(f"📁 Log file: {logger.log_file if hasattr(logger, 'log_file') else 'N/A'}", "Startup")
    
    # Initialize audit log service with Supabase client
    try:
        supabase_client = get_supabase_client()
        init_audit_service(supabase_client)
        logger.info("✅ API startup complete - Audit log and rate limiter active")
    except Exception as e:
        logger.error(f"⚠️  Failed to initialize audit service: {e}")

# --- MIDDLEWARES ---

# Sprint 6: Rate limiting (BEFORE request logging)
app.add_middleware(RateLimitMiddleware)

@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    # Skip logging for OPTIONS requests (CORS preflight)
    if request.method == "OPTIONS":
        return await call_next(request)
    
    # Log incoming request with custom logger
    logger.info(f"→ {request.method} {request.url.path}", "HTTP")
    
    start_time = time.perf_counter()
    client_id = request.headers.get("X-Client-ID", "anonymous")
    tenant_id = request.headers.get("X-Tenant-ID", "none")
    
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"ERROR in {request.method} {request.url.path}: {str(e)}", "HTTP")
        logger.error(traceback.format_exc(), "HTTP")
        raise
    
    duration_ms = (time.perf_counter() - start_time) * 1000
    
    # Log response with custom logger
    status_icon = "✅" if response.status_code < 400 else "❌"
    logger.info(f"{status_icon} {response.status_code} ({duration_ms:.0f}ms) [tenant:{tenant_id[:8]}...]", "HTTP")
    
    # Also use structured logger for non-health endpoints
    if request.url.path not in ["/health", "/ping"]:
        logger.http_log(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            client_id=client_id
        )
    
    return response

# Configure CORS as the OUTERMOST middleware (Added last)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permissive for local development stability
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# --- EXCEPTION HANDLERS (with CORS Support) ---

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": exc.detail},
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Credentials": "true",
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", component="FastAPI", exc=exc)
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal Server Error", "detail": str(exc)},
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Credentials": "true",
        }
    )

# --- ROUTER INCLUSIONS ---

app.include_router(auth_router, prefix="/auth")
app.include_router(projects_router)
app.include_router(project_members_router)
app.include_router(triage_router)
app.include_router(transpile_router)
app.include_router(governance_router)
app.include_router(agents_router)
app.include_router(lab_router)
app.include_router(reports_router)
app.include_router(locks_router)
app.include_router(visualization_router)  # Sprint 13: Visualization endpoints
app.include_router(prompts_router)  # v4.0: Zero-Hardcode Core - Prompt management
app.include_router(gaps_router)  # Sprint 3: Gap & Decision Workspace
app.include_router(config.router)
app.include_router(system.router, prefix="/system")

# --- LEGACY LOGIN SUPPORT ---
# Maintain /login at root for older frontend components
@app.post("/login")
async def root_login(request: Request):
    from apps.api.routers import auth
    return await auth.login(request)

# --- CORE ENDPOINTS ---

@app.get("/ping")
async def ping():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/health", tags=["System"])
async def health_check():
    """Health check (Liveness). Connectivity check moved inside."""
    db_status = "unknown"
    try:
        from apps.api.routers.dependencies import get_supabase_client
        client = get_supabase_client()
        # Ping Supabase projects table as a connectivity check
        res = client.table("utm_projects").select("count", count="exact").limit(1).execute()
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected ({str(e)})"
        
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "db_connection": db_status,
        "timestamp": datetime.now().isoformat(),
        "version": app.version
    }

@app.get("/")
async def root():
    return {
        "message": "Welcome to Legacy2Lake API v3.7",
        "docs": "/docs",
        "status": "operational"
    }

if __name__ == "__main__":
    import uvicorn
    # Use 8085 to match frontend config
    uvicorn.run(app, host="0.0.0.0", port=8085)

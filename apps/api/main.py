from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
import time
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Fix for Windows asyncio subprocess support
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Environment & Logging
load_dotenv()
from apps.api.utils.logger import logger
from services.persistence_service import SupabasePersistence

# Import Routers
from routers import config, system
from routers.auth import router as auth_router
from routers.agents import router as agents_router
from routers.projects import router as projects_router
from routers.triage import router as triage_router
from routers.transpile import router as transpile_router
from routers.governance import router as governance_router
from routers.lab import router as lab_router
from routers.reports import router as reports_router
from routers.dependencies import get_db

app = FastAPI(
    title="Legacy2Lake API", 
    version="3.7.0",
    description="Refactored Core API for Cloud-Native Multi-Tenant Architecture"
)

# --- MIDDLEWARES ---

@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    # Skip logging for OPTIONS requests (CORS preflight)
    if request.method == "OPTIONS":
        return await call_next(request)
    
    start_time = time.perf_counter()
    client_id = request.headers.get("X-Client-ID", "anonymous")
    
    response = await call_next(request)
    
    duration_ms = (time.perf_counter() - start_time) * 1000
    if request.url.path != "/health" and request.url.path != "/ping":
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

app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(triage_router)
app.include_router(transpile_router)
app.include_router(governance_router)
app.include_router(agents_router)
app.include_router(lab_router)
app.include_router(reports_router)
app.include_router(config.router)
app.include_router(system.router)

# --- CORE ENDPOINTS ---

@app.get("/ping")
async def ping():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/health", tags=["System"])
async def health_check(db: SupabasePersistence = Depends(get_db)):
    """Health check with DB connectivity verification."""
    db_status = "connected"
    try:
        await db.client.table("utm_projects").select("count", count="exact").limit(1).execute()
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

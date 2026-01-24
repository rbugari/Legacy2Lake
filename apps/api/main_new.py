"""
Legacy2Lake API - Main Entry Point
Refactored Version: Routes organized into modular routers.

This is the main FastAPI application that orchestrates all routers.
Most endpoint logic has been moved to individual router modules.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Import routers
from apps.api.routers import (
    config,
    system,
)
from apps.api.routers.auth import router as auth_router
from apps.api.routers.projects import router as projects_router
from apps.api.routers.agents import router as agents_router
from apps.api.routers.triage import router as triage_router
from apps.api.routers.transpile import router as transpile_router
from apps.api.routers.governance import router as governance_router


# --- Application Setup ---

app = FastAPI(
    title="Legacy2Lake API",
    description="AI-powered legacy code migration platform",
    version="2.0.0"
)


# --- Global Exception Handler ---

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    err_msg = traceback.format_exc()
    print(f"GLOBAL ERROR: {err_msg}")
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "traceback": err_msg},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true"
        }
    )


# --- CORS Middleware ---

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3005", "http://localhost:3000", "http://127.0.0.1:3005", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)


# --- Include Routers ---

# Core routers (refactored)
app.include_router(auth_router)           # /login, /ping-antigravity
app.include_router(projects_router)       # /projects/*
app.include_router(agents_router)         # /prompts/*
app.include_router(triage_router)         # /discovery/*, /projects/*/triage
app.include_router(transpile_router)      # /transpile/*
app.include_router(governance_router)     # /projects/*/governance, /projects/*/refinement

# Legacy routers (from before refactoring)
app.include_router(config.router)         # /config/*
app.include_router(system.router)         # /system/*


# --- Root Endpoint ---

@app.get("/")
async def root():
    return {
        "message": "Welcome to Legacy2Lake API",
        "version": "2.0.0",
        "status": "operational"
    }


@app.get("/ping")
async def ping():
    return {"status": "ok"}


# --- Backward Compatibility ---
# Note: Some endpoints may still be duplicated between old routes and new routers.
# During migration, both versions work. After testing, remove duplicates from main.py.


# --- Entry Point ---

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)

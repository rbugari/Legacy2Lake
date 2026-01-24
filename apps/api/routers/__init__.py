"""
Routers Package
Exports all API routers for easy inclusion in main.py.
"""
from routers.config import router as config_router
from routers.system import router as system_router
from routers.auth import router as auth_router
from routers.projects import router as projects_router
from routers.agents import router as agents_router
from routers.triage import router as triage_router
from routers.transpile import router as transpile_router
from routers.governance import router as governance_router

# Legacy compatibility - direct router access
from routers import config, system

__all__ = [
    "config_router",
    "system_router", 
    "auth_router",
    "projects_router",
    "agents_router",
    "triage_router",
    "transpile_router",
    "governance_router",
    # Legacy
    "config",
    "system",
]

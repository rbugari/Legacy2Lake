"""
Routers Package
Exports all API routers for easy inclusion in main.py.
"""
from .config import router as config_router
from .system import router as system_router
from .auth import router as auth_router
from .projects import router as projects_router
from .agents import router as agents_router
from .triage import router as triage_router
from .transpile import router as transpile_router
from .governance import router as governance_router

# Legacy compatibility - direct router access
from . import config, system

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

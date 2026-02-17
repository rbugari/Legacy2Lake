from fastapi import APIRouter, HTTPException, Depends
from apps.api.services.persistence_service import SupabasePersistence
from apps.api.routers.dependencies import get_db
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/config", tags=["Configuration"])

class SupportedTech(BaseModel):
    tech_id: str
    role: str
    label: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: bool
    config_schema: Optional[Dict[str, Any]] = None

@router.get("/technologies", response_model=List[SupportedTech])
async def get_supported_technologies(db: SupabasePersistence = Depends(get_db)):
    """
    Returns valid source/target technologies from unified catalog.
    """
    try:
        # Use centralized list_system_catalog (v3.6 Consistency)
        data = await db.list_system_catalog()
        
        # Map for backward compatibility if needed
        for item in data:
            if "role" not in item:
                item["role"] = "SOURCE" if item["type"] == "origin" else "TARGET"
            if "label" not in item:
                item["label"] = item["name"]
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

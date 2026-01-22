from fastapi import APIRouter, HTTPException
from supabase import create_client, Client
import os
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

router = APIRouter(prefix="/config", tags=["Configuration"])

# Supabase Setup (Duplicate from main for now, ideal refactor: shared dependency)
url: str = os.getenv("SUPABASE_URL", "").strip()
key: str = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY") or "").strip()
supabase: Client = create_client(url, key)

class SupportedTech(BaseModel):
    tech_id: str
    role: str
    label: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: bool
    config_schema: Optional[Dict[str, Any]] = None

@router.get("/technologies", response_model=List[SupportedTech])
async def get_supported_technologies():
    """
    Returns valid source/target technologies from metadata store.
    """
    try:
        response = supabase.table("utm_supported_techs").select("*").eq("is_active", True).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

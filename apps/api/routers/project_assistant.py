"""
Router: Project Assistant Chat - v4.5 Sprint 2
POST   /projects/{project_id}/assistant/chat
GET    /projects/{project_id}/assistant/history
DELETE /projects/{project_id}/assistant/history
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, List

try:
    from apps.api.routers.dependencies import get_db
    from apps.api.services.persistence_service import SupabasePersistence
    from apps.api.services.project_assistant_service import ProjectAssistantService
except ImportError:
    from routers.dependencies import get_db
    from services.persistence_service import SupabasePersistence
    from services.project_assistant_service import ProjectAssistantService

router = APIRouter(tags=["assistant"])


class AssistantChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


class AssistantChatResponse(BaseModel):
    answer: str
    intent: str
    confidence: str
    triage_ready: bool


def _get_svc(project_id: str, db: SupabasePersistence) -> ProjectAssistantService:
    tenant_id = db.tenant_id
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant context required.")
    return ProjectAssistantService(tenant_id=tenant_id, project_id=project_id)


@router.post(
    "/projects/{project_id}/assistant/chat",
    response_model=AssistantChatResponse,
    summary="Ask the project source-analysis assistant",
)
async def project_assistant_chat(
    project_id: str,
    body: AssistantChatRequest,
    db: SupabasePersistence = Depends(get_db),
) -> Dict[str, Any]:
    """
    Sends a question to the project assistant.
    The assistant is scoped to legacy source analysis data collected during Triage.
    Returns a grounded answer with intent classification and confidence label.
    If Triage has not been executed the assistant returns a gate message.
    """
    svc = _get_svc(project_id, db)
    return await svc.chat(body.message)


@router.get(
    "/projects/{project_id}/assistant/history",
    summary="Get chat history for this project",
)
async def project_assistant_history(
    project_id: str,
    db: SupabasePersistence = Depends(get_db),
) -> List[Dict[str, Any]]:
    """
    Returns all assistant exchanges in the current chat thread.
    Each item: { role, intent, question, answer, confidence, created_at }
    """
    svc = _get_svc(project_id, db)
    return svc.get_history()


@router.delete(
    "/projects/{project_id}/assistant/history",
    summary="Clear chat history for this project",
)
async def project_assistant_clear_history(
    project_id: str,
    db: SupabasePersistence = Depends(get_db),
) -> Dict[str, Any]:
    """
    Deletes all messages in the current thread and starts a new one.
    Returns { cleared: int, new_thread_id: str }
    """
    svc = _get_svc(project_id, db)
    return svc.clear_history()

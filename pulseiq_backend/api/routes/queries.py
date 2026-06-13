from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from pulseiq_backend.core.database import get_db
from pulseiq_backend.core.security import get_current_user
from pulseiq_backend.models.user import User
from pulseiq_backend.schemas.query import QueryResponse
from pulseiq_backend.services.query.orchestrator import QueryOrchestrator
from pydantic import BaseModel

router = APIRouter(prefix="/query", tags=["query"])


class QuestionRequest(BaseModel):
    question: str


@router.post("", response_model=QueryResponse)
async def owner_query(
    body: QuestionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from pulseiq_backend.schemas.query import QueryRequest
    request = QueryRequest(
        tenant_id=current_user.tenant_id,
        question=body.question,
        user_id=current_user.id,
    )
    return await QueryOrchestrator(db).answer(request)

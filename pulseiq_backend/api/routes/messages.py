import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from pulseiq_backend.core.database import get_db, AsyncSessionFactory
from pulseiq_backend.core.security import get_current_user
from pulseiq_backend.models.user import User
from pulseiq_backend.repositories.message_repo import MessageRepository
from pulseiq_backend.schemas.message import MessageCreate, MessageResponse
from pulseiq_backend.services.event_extraction.extractor import EventExtractor

router = APIRouter(prefix="/messages", tags=["messages"])
logger = logging.getLogger(__name__)


class MessageSubmit(MessageCreate):
    pass


class MessageSubmitRequest:
    def __init__(self, content: str):
        self.content = content


from pydantic import BaseModel

class MessageRequest(BaseModel):
    content: str


async def _extract_in_background(tenant_id, message_id, content) -> None:
    async with AsyncSessionFactory() as db:
        try:
            await EventExtractor(db).process_message(tenant_id, message_id, content)
        except Exception:
            logger.exception("Event extraction failed for message %s", message_id)


@router.post("", response_model=MessageResponse, status_code=201)
async def submit_message(
    body: MessageRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.must_reset_password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must reset your password before submitting messages",
        )

    msg = await MessageRepository(db).create(
        current_user.tenant_id, body.content, current_user.id
    )
    background_tasks.add_task(_extract_in_background, msg.tenant_id, msg.id, msg.content)
    return msg


@router.get("", response_model=list[MessageResponse])
async def list_messages(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await MessageRepository(db).list_by_tenant(current_user.tenant_id)

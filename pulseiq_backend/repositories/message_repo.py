import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from pulseiq_backend.models.message import Message


class MessageRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, tenant_id: uuid.UUID, content: str, user_id: uuid.UUID | None = None) -> Message:
        msg = Message(tenant_id=tenant_id, content=content, user_id=user_id)
        self._db.add(msg)
        await self._db.commit()
        await self._db.refresh(msg)
        return msg

    async def get_by_id(self, tenant_id: uuid.UUID, message_id: uuid.UUID) -> Message | None:
        result = await self._db.execute(
            select(Message).where(Message.tenant_id == tenant_id, Message.id == message_id)
        )
        return result.scalar_one_or_none()

    async def list_by_tenant(self, tenant_id: uuid.UUID, limit: int = 50) -> list[Message]:
        result = await self._db.execute(
            select(Message)
            .where(Message.tenant_id == tenant_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_ids(self, tenant_id: uuid.UUID, message_ids: list[uuid.UUID]) -> list[Message]:
        result = await self._db.execute(
            select(Message).where(Message.tenant_id == tenant_id, Message.id.in_(message_ids))
        )
        return list(result.scalars().all())

    async def get_by_ids_with_user(self, tenant_id: uuid.UUID, message_ids: list[uuid.UUID]) -> list[Message]:
        """Fetch messages with user relationship eagerly loaded for submitted_by display."""
        result = await self._db.execute(
            select(Message)
            .where(Message.tenant_id == tenant_id, Message.id.in_(message_ids))
            .options(joinedload(Message.user))
        )
        return list(result.unique().scalars().all())

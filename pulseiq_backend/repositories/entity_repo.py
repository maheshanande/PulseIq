import uuid

from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from pulseiq_backend.models.entity import Entity, EntityMention


class EntityRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, tenant_id: uuid.UUID, entity_type: str, name: str, aliases: list[str]) -> Entity:
        entity = Entity(tenant_id=tenant_id, entity_type=entity_type, name=name, aliases=aliases)
        self._db.add(entity)
        await self._db.commit()
        await self._db.refresh(entity)
        return entity

    async def find_by_name_or_alias(self, tenant_id: uuid.UUID, name: str) -> Entity | None:
        """Exact match on name or aliases array — used for entity resolution."""
        result = await self._db.execute(
            select(Entity).where(
                Entity.tenant_id == tenant_id,
                or_(
                    func.lower(Entity.name) == name.lower(),
                    Entity.aliases.any(func.lower(name)),  # type: ignore[arg-type]
                ),
            )
        )
        return result.scalar_one_or_none()

    async def find_by_type(self, tenant_id: uuid.UUID, entity_type: str) -> list[Entity]:
        result = await self._db.execute(
            select(Entity).where(Entity.tenant_id == tenant_id, Entity.entity_type == entity_type)
        )
        return list(result.scalars().all())

    async def add_alias(self, entity: Entity, alias: str) -> Entity:
        if alias not in entity.aliases:
            entity.aliases = [*entity.aliases, alias]
            await self._db.commit()
            await self._db.refresh(entity)
        return entity

    async def add_mention(
        self,
        tenant_id: uuid.UUID,
        message_id: uuid.UUID,
        mention_text: str,
        entity_type: str,
        confidence: float | None = None,
        entity_id: uuid.UUID | None = None,
    ) -> None:
        mention = EntityMention(
            tenant_id=tenant_id,
            entity_id=entity_id,
            message_id=message_id,
            mention_text=mention_text,
            entity_type=entity_type,
            confidence=confidence,
        )
        self._db.add(mention)
        await self._db.commit()

    async def get_by_id(self, tenant_id: uuid.UUID, entity_id: uuid.UUID) -> Entity | None:
        result = await self._db.execute(
            select(Entity).where(Entity.tenant_id == tenant_id, Entity.id == entity_id)
        )
        return result.scalar_one_or_none()

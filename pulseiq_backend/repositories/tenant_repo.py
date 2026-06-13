import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pulseiq_backend.models.tenant import Tenant


class TenantRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, name: str, slug: str) -> Tenant:
        tenant = Tenant(name=name, slug=slug)
        self._db.add(tenant)
        await self._db.commit()
        await self._db.refresh(tenant)
        return tenant

    async def get_by_id(self, tenant_id: uuid.UUID) -> Tenant | None:
        result = await self._db.execute(select(Tenant).where(Tenant.id == tenant_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Tenant | None:
        result = await self._db.execute(select(Tenant).where(Tenant.name == name))
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Tenant | None:
        result = await self._db.execute(select(Tenant).where(Tenant.slug == slug))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Tenant]:
        result = await self._db.execute(select(Tenant).order_by(Tenant.created_at))
        return list(result.scalars().all())

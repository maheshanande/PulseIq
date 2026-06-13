from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from pulseiq_backend.core.database import get_db
from pulseiq_backend.core.security import ROLE_SUPER_ADMIN, require_role
from pulseiq_backend.repositories.tenant_repo import TenantRepository
from pulseiq_backend.schemas.tenant import TenantCreate, TenantResponse

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post(
    "",
    response_model=TenantResponse,
    status_code=201,
    responses={409: {"description": "Facility name or slug already exists"}},
)
async def create_tenant(
    body: TenantCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role(ROLE_SUPER_ADMIN)),
):
    repo = TenantRepository(db)
    name = body.name.strip()
    slug = body.slug.strip().lower()

    if await repo.get_by_name(name):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Facility name already exists")
    if await repo.get_by_slug(slug):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Facility slug already exists")

    try:
        return await repo.create(name, slug)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Facility already exists")


@router.get("", response_model=list[TenantResponse])
async def list_tenants(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role(ROLE_SUPER_ADMIN)),
):
    return await TenantRepository(db).list_all()

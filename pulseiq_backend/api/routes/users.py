import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pulseiq_backend.core.database import get_db
from pulseiq_backend.core.security import (
    ROLE_EMPLOYEE,
    ROLE_FACILITY_ADMIN,
    ROLE_SUPER_ADMIN,
    generate_temp_password,
    hash_password,
    require_role,
)
from pulseiq_backend.models.user import User
from pulseiq_backend.repositories.tenant_repo import TenantRepository
from pulseiq_backend.schemas.user import (
    EMPLOYEE_DEPARTMENT_OPTIONS,
    EmployeeCreate,
    EmployeeCreatedResponse,
    EmployeeDepartmentOption,
    EmployeeUpdate,
    FacilityAdminCreate,
    FacilityAdminCreatedResponse,
    UserResponse,
)

router = APIRouter(prefix="/users", tags=["users"])


async def _ensure_email_available(db: AsyncSession, email: str) -> None:
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")


@router.post("/facility-admins", response_model=FacilityAdminCreatedResponse, status_code=201)
async def add_facility_admin(
    body: FacilityAdminCreate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_role(ROLE_SUPER_ADMIN)),
):
    tenant = await TenantRepository(db).get_by_id(body.tenant_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility not found")

    await _ensure_email_available(db, body.email)

    temp_password = generate_temp_password()
    user = User(
        tenant_id=body.tenant_id,
        email=body.email,
        hashed_password=hash_password(temp_password),
        role=ROLE_FACILITY_ADMIN,
        is_active=True,
        must_reset_password=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return FacilityAdminCreatedResponse(
        user=UserResponse.model_validate(user),
        temporary_password=temp_password,
        message=f"Share this temporary password with facility admin {body.email}. They must reset it on first login.",
    )


@router.get("/employee-departments", response_model=list[EmployeeDepartmentOption])
async def list_employee_departments(
    _current_user: User = Depends(require_role(ROLE_SUPER_ADMIN, ROLE_FACILITY_ADMIN)),
):
    return EMPLOYEE_DEPARTMENT_OPTIONS


@router.post("/employees", response_model=EmployeeCreatedResponse, status_code=201)
async def add_employee(
    body: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(ROLE_FACILITY_ADMIN)),
):
    await _ensure_email_available(db, body.email)

    temp_password = generate_temp_password()
    user = User(
        tenant_id=current_user.tenant_id,
        email=body.email,
        hashed_password=hash_password(temp_password),
        role=ROLE_EMPLOYEE,
        department=body.department,
        is_active=True,
        must_reset_password=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return EmployeeCreatedResponse(
        user=UserResponse.model_validate(user),
        temporary_password=temp_password,
        message=f"Share this temporary password with {body.email}. They must reset it on first login.",
    )


@router.post("", response_model=EmployeeCreatedResponse, status_code=201)
async def add_employee_legacy(
    body: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(ROLE_FACILITY_ADMIN)),
):
    return await add_employee(body, db, current_user)


@router.get("", response_model=list[UserResponse])
async def list_employees(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(ROLE_FACILITY_ADMIN)),
):
    result = await db.execute(
        select(User)
        .where(User.tenant_id == current_user.tenant_id)
        .order_by(User.created_at)
    )
    return result.scalars().all()


@router.patch("/employees/{user_id}", response_model=UserResponse)
async def update_employee(
    user_id: uuid.UUID,
    body: EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(ROLE_FACILITY_ADMIN)),
):
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.tenant_id == current_user.tenant_id,
            User.role == ROLE_EMPLOYEE,
        )
    )
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    employee.department = body.department
    await db.commit()
    await db.refresh(employee)
    return employee

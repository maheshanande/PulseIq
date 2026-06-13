import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr

EmployeeDepartment = Literal[
    "operations",
    "sales",
    "engineering",
    "customer_support",
    "customer_success",
    "product",
    "marketing",
    "finance",
    "human_resources",
    "administration",
    "procurement",
    "logistics",
    "production",
    "quality_assurance",
    "security",
    "legal",
    "other",
]

EMPLOYEE_DEPARTMENT_OPTIONS: list[dict[str, str]] = [
    {"value": "operations", "label": "Operations"},
    {"value": "sales", "label": "Sales"},
    {"value": "engineering", "label": "Engineering"},
    {"value": "customer_support", "label": "Customer Support"},
    {"value": "customer_success", "label": "Customer Success"},
    {"value": "product", "label": "Product"},
    {"value": "marketing", "label": "Marketing"},
    {"value": "finance", "label": "Finance"},
    {"value": "human_resources", "label": "Human Resources"},
    {"value": "administration", "label": "Administration"},
    {"value": "procurement", "label": "Procurement"},
    {"value": "logistics", "label": "Logistics"},
    {"value": "production", "label": "Production"},
    {"value": "quality_assurance", "label": "Quality Assurance"},
    {"value": "security", "label": "Security"},
    {"value": "legal", "label": "Legal"},
    {"value": "other", "label": "Other"},
]


class EmployeeCreate(BaseModel):
    email: EmailStr
    department: EmployeeDepartment


class EmployeeUpdate(BaseModel):
    department: EmployeeDepartment


class EmployeeDepartmentOption(BaseModel):
    value: EmployeeDepartment
    label: str


class FacilityAdminCreate(BaseModel):
    tenant_id: uuid.UUID
    email: EmailStr


class SuperAdminBootstrapRequest(BaseModel):
    email: EmailStr
    password: str
    setup_token: str


class UserResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID | None
    email: str
    role: str
    department: str | None
    is_active: bool
    must_reset_password: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class EmployeeCreatedResponse(BaseModel):
    user: UserResponse
    temporary_password: str
    message: str


class FacilityAdminCreatedResponse(BaseModel):
    user: UserResponse
    temporary_password: str
    message: str


class ResetPasswordRequest(BaseModel):
    current_password: str
    new_password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    must_reset_password: bool

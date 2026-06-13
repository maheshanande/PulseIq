"""rename tenant admin role to facility admin

Revision ID: a1b2c3d4e5f6
Revises: 4ffb66cc6815
Create Date: 2026-06-13 04:05:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "4ffb66cc6815"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE users SET role = 'facility_admin' WHERE role = 'tenant_admin'")


def downgrade() -> None:
    op.execute("UPDATE users SET role = 'tenant_admin' WHERE role = 'facility_admin'")

"""preserve raw entity mentions

Revision ID: c9d0e1f2a3b4
Revises: b7c8d9e0f1a2
Create Date: 2026-06-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c9d0e1f2a3b4"
down_revision: Union[str, None] = "b7c8d9e0f1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "entity_aliases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column("alias_text", sa.String(length=255), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["entity_id"], ["entities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "entity_id", "alias_text", name="uq_entity_aliases_tenant_entity_alias"),
    )
    op.create_index(op.f("ix_entity_aliases_alias_text"), "entity_aliases", ["alias_text"], unique=False)
    op.create_index(op.f("ix_entity_aliases_entity_id"), "entity_aliases", ["entity_id"], unique=False)
    op.create_index(op.f("ix_entity_aliases_tenant_id"), "entity_aliases", ["tenant_id"], unique=False)

    op.add_column("entity_mentions", sa.Column("mention_text", sa.String(length=255), nullable=True))
    op.add_column("entity_mentions", sa.Column("entity_type", sa.String(length=50), nullable=True))
    op.add_column("entity_mentions", sa.Column("confidence", sa.Float(), nullable=True))

    op.execute(
        """
        UPDATE entity_mentions
        SET mention_text = entities.name,
            entity_type = entities.entity_type
        FROM entities
        WHERE entity_mentions.entity_id = entities.id
        """
    )
    op.execute("UPDATE entity_mentions SET mention_text = 'unknown' WHERE mention_text IS NULL")
    op.execute("UPDATE entity_mentions SET entity_type = 'unknown' WHERE entity_type IS NULL")

    op.alter_column("entity_mentions", "mention_text", nullable=False)
    op.alter_column("entity_mentions", "entity_type", nullable=False)
    op.alter_column("entity_mentions", "entity_id", nullable=True)
    op.drop_constraint("entity_mentions_entity_id_fkey", "entity_mentions", type_="foreignkey")
    op.create_foreign_key(
        "entity_mentions_entity_id_fkey",
        "entity_mentions",
        "entities",
        ["entity_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_entity_mentions_mention_text"), "entity_mentions", ["mention_text"], unique=False)
    op.create_index(op.f("ix_entity_mentions_entity_type"), "entity_mentions", ["entity_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_entity_mentions_entity_type"), table_name="entity_mentions")
    op.drop_index(op.f("ix_entity_mentions_mention_text"), table_name="entity_mentions")
    op.drop_constraint("entity_mentions_entity_id_fkey", "entity_mentions", type_="foreignkey")
    op.create_foreign_key(
        "entity_mentions_entity_id_fkey",
        "entity_mentions",
        "entities",
        ["entity_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.alter_column("entity_mentions", "entity_id", nullable=False)
    op.drop_column("entity_mentions", "confidence")
    op.drop_column("entity_mentions", "entity_type")
    op.drop_column("entity_mentions", "mention_text")

    op.drop_index(op.f("ix_entity_aliases_tenant_id"), table_name="entity_aliases")
    op.drop_index(op.f("ix_entity_aliases_entity_id"), table_name="entity_aliases")
    op.drop_index(op.f("ix_entity_aliases_alias_text"), table_name="entity_aliases")
    op.drop_table("entity_aliases")

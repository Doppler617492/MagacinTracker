"""scheduler log

Revision ID: 2024050601
Revises: 2024050501
Create Date: 2025-10-06
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "2024050601"
down_revision = "2024050501"
branch_labels = None
depends_on = None


_status_values = ("suggested", "accepted", "override")

scheduler_status_enum = sa.Enum(*_status_values, name="schedulerlogstatus")


def upgrade() -> None:
    op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'scheduler.suggested'")
    op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'scheduler.accepted'")
    op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'scheduler.override'")
    op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'catalog.sync'")
    op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'catalog.enriched'")
    op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'catalog.manual_update'")

    op.add_column(
        "artikal",
        sa.Column("aktivan", sa.Boolean(), nullable=False, server_default=sa.text("true"))
    )
    op.alter_column("artikal", "aktivan", server_default=None)

    op.add_column(
        "trebovanje_stavka",
        sa.Column("needs_barcode", sa.Boolean(), nullable=False, server_default=sa.text("false"))
    )
    op.alter_column("trebovanje_stavka", "needs_barcode", server_default=None)

    bind = op.get_bind()
    scheduler_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "scheduler_log",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("trebovanje_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("magacioner_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", scheduler_status_enum, nullable=False, server_default=_status_values[0]),
        sa.Column("score", sa.Numeric(12, 6), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("lock_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("timezone('utc', now())"), nullable=False),
        sa.Column("created_by_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("metadata", sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["trebovanje_id"], ["trebovanje.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["magacioner_id"], ["user_account.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["user_account.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_scheduler_log_trebovanje_id", "scheduler_log", ["trebovanje_id"])
    op.create_index("ix_scheduler_log_magacioner_id", "scheduler_log", ["magacioner_id"])

    op.create_table(
        "catalog_sync_status",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("payload_hash", sa.String(length=128), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=True),
        sa.Column("executed_by_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deactivated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_ms", sa.Numeric(14, 3), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="success"),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["executed_by_id"], ["user_account.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_catalog_sync_status_finished_at", "catalog_sync_status", ["finished_at"])


def downgrade() -> None:
    op.drop_index("ix_catalog_sync_status_finished_at", table_name="catalog_sync_status")
    op.drop_table("catalog_sync_status")

    op.drop_column("trebovanje_stavka", "needs_barcode")
    op.drop_column("artikal", "aktivan")

    op.drop_index("ix_scheduler_log_magacioner_id", table_name="scheduler_log")
    op.drop_index("ix_scheduler_log_trebovanje_id", table_name="scheduler_log")
    op.drop_table("scheduler_log")
    bind = op.get_bind()
    scheduler_status_enum.drop(bind, checkfirst=True)
    # note: removing enum values from audit_action is not supported in downgrade

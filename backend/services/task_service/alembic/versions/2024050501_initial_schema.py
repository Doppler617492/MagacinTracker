"""Initial schema for Sprint 1."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "2024050501"
down_revision = None
branch_labels = None
depends_on = None


user_role_enum = sa.Enum(
    "komercijalista", "sef", "magacioner", "menadzer", name="user_role_enum"
)
trebovanje_status = sa.Enum(
    "new", "assigned", "in_progress", "done", "failed", name="trebovanje_status"
)
trebovanje_stavka_status = sa.Enum(
    "new", "assigned", "in_progress", "done", name="trebovanje_stavka_status"
)
magacin_task_priority = sa.Enum("low", "normal", "high", name="task_priority")
zaduznica_status = sa.Enum(
    "assigned", "in_progress", "done", "blocked", name="zaduznica_status"
)
zaduznica_stavka_status = sa.Enum(
    "assigned", "in_progress", "done", name="zaduznica_stavka_status"
)
import_status = sa.Enum("pending", "processing", "done", "failed", name="import_status")
scan_result = sa.Enum("match", "mismatch", "duplicate", name="scan_result")
audit_action = sa.Enum(
    "import.created",
    "trebovanje.imported",
    "zaduznica.assigned",
    "zaduznica.reassigned",
    "scan.recorded",
    "manual.complete",
    name="audit_action",
)


def upgrade() -> None:  # noqa: C901
    bind = op.get_bind()
    user_role_enum.create(bind, checkfirst=True)
    trebovanje_status.create(bind, checkfirst=True)
    trebovanje_stavka_status.create(bind, checkfirst=True)
    magacin_task_priority.create(bind, checkfirst=True)
    zaduznica_status.create(bind, checkfirst=True)
    zaduznica_stavka_status.create(bind, checkfirst=True)
    import_status.create(bind, checkfirst=True)
    scan_result.create(bind, checkfirst=True)
    audit_action.create(bind, checkfirst=True)

    op.create_table(
        "user_account",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("timezone('utc', now())"),
            nullable=False,
        ),
    )

    op.create_table(
        "user_role",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", user_role_enum, nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user_account.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_user_role_user_id", "user_role", ["user_id"], unique=False)

    op.create_table(
        "magacin",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pantheon_id", sa.String(length=64), nullable=False, unique=True),
        sa.Column("naziv", sa.String(length=255), nullable=False),
    )
    op.create_index("ix_magacin_pantheon_id", "magacin", ["pantheon_id"], unique=True)

    op.create_table(
        "radnja",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pantheon_id", sa.String(length=64), nullable=False, unique=True),
        sa.Column("naziv", sa.String(length=255), nullable=False),
    )
    op.create_index("ix_radnja_pantheon_id", "radnja", ["pantheon_id"], unique=True)

    op.create_table(
        "artikal",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("sifra", sa.String(length=64), nullable=False),
        sa.Column("naziv", sa.String(length=255), nullable=False),
        sa.Column(
            "jedinica_mjere",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'kom'"),
        ),
    )
    op.create_index("ix_artikal_sifra", "artikal", ["sifra"], unique=True)

    op.create_table(
        "trebovanje",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("dokument_broj", sa.String(length=64), nullable=False),
        sa.Column("datum", sa.DateTime(timezone=True), nullable=False),
        sa.Column("magacin_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("radnja_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", trebovanje_status, nullable=False, server_default="new"),
        sa.Column(
            "meta",
            sa.dialects.postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("created_by_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("timezone('utc', now())"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("timezone('utc', now())"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["created_by_id"], ["user_account.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["magacin_id"], ["magacin.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["radnja_id"], ["radnja.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_trebovanje_dokument_broj", "trebovanje", ["dokument_broj"], unique=True)

    op.create_table(
        "artikal_barkod",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("artikal_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("barkod", sa.String(length=64), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(["artikal_id"], ["artikal.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_artikal_barkod_artikal_id", "artikal_barkod", ["artikal_id"], unique=False)
    op.create_index("uq_artikal_barkod", "artikal_barkod", ["barkod"], unique=True)

    op.create_table(
        "trebovanje_stavka",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("trebovanje_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("artikal_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("artikl_sifra", sa.String(length=64), nullable=False),
        sa.Column("naziv", sa.String(length=255), nullable=False),
        sa.Column("kolicina_trazena", sa.Numeric(12, 3), nullable=False),
        sa.Column(
            "kolicina_uradjena",
            sa.Numeric(12, 3),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("status", trebovanje_stavka_status, nullable=False, server_default="new"),
        sa.ForeignKeyConstraint(["trebovanje_id"], ["trebovanje.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["artikal_id"], ["artikal.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "kolicina_trazena > 0", name="ck_trebovanje_stavka_kolicina_trazena_gt_zero"
        ),
        sa.CheckConstraint(
            "kolicina_uradjena <= kolicina_trazena",
            name="ck_trebovanje_stavka_kolicina_uradjena_le_trazena",
        ),
    )
    op.create_index(
        "ix_trebovanje_stavka_trebovanje_id",
        "trebovanje_stavka",
        ["trebovanje_id"],
        unique=False,
    )

    op.create_table(
        "zaduznica",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("trebovanje_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("magacioner_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("prioritet", magacin_task_priority, nullable=False, server_default="normal"),
        sa.Column("rok", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", zaduznica_status, nullable=False, server_default="assigned"),
        sa.Column(
            "progress",
            sa.Numeric(5, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.ForeignKeyConstraint(["trebovanje_id"], ["trebovanje.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["magacioner_id"], ["user_account.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_zaduznica_trebovanje_id", "zaduznica", ["trebovanje_id"], unique=False)
    op.create_index("ix_zaduznica_magacioner_id", "zaduznica", ["magacioner_id"], unique=False)

    op.create_table(
        "zaduznica_stavka",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("zaduznica_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trebovanje_stavka_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trazena_kolicina", sa.Numeric(12, 3), nullable=False),
        sa.Column(
            "obradjena_kolicina",
            sa.Numeric(12, 3),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "status",
            zaduznica_stavka_status,
            nullable=False,
            server_default="assigned",
        ),
        sa.ForeignKeyConstraint(["zaduznica_id"], ["zaduznica.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["trebovanje_stavka_id"], ["trebovanje_stavka.id"], ondelete="CASCADE"),
        sa.CheckConstraint("trazena_kolicina > 0", name="ck_zaduznica_stavka_trazena_gt_zero"),
        sa.CheckConstraint(
            "obradjena_kolicina <= trazena_kolicina",
            name="ck_zaduznica_stavka_obradjena_le_trazena",
        ),
    )
    op.create_index(
        "ix_zaduznica_stavka_zaduznica_id",
        "zaduznica_stavka",
        ["zaduznica_id"],
        unique=False,
    )
    op.create_index(
        "ix_zaduznica_stavka_trebovanje_stavka_id",
        "zaduznica_stavka",
        ["trebovanje_stavka_id"],
        unique=False,
    )

    op.create_table(
        "import_job",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_hash", sa.String(length=128), nullable=False),
        sa.Column("status", import_status, nullable=False, server_default="pending"),
        sa.Column("error_message", sa.String(length=512), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("initiated_by_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("trebovanje_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["initiated_by_id"], ["user_account.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["trebovanje_id"], ["trebovanje.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_import_job_file_hash", "import_job", ["file_hash"], unique=True)

    op.create_table(
        "scan_log",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("zaduznica_stavka_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("barcode", sa.String(length=64), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 3), nullable=False, server_default=sa.text("1")),
        sa.Column("result", scan_result, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.ForeignKeyConstraint(["zaduznica_stavka_id"], ["zaduznica_stavka.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user_account.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_scan_log_zaduznica_stavka_id", "scan_log", ["zaduznica_stavka_id"], unique=False
    )

    op.create_table(
        "manual_override",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("zaduznica_stavka_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.ForeignKeyConstraint(["zaduznica_stavka_id"], ["zaduznica_stavka.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user_account.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_manual_override_zaduznica_stavka_id",
        "manual_override",
        ["zaduznica_stavka_id"],
        unique=False,
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", audit_action, nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column(
            "payload",
            sa.dialects.postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.ForeignKeyConstraint(["actor_id"], ["user_account.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_audit_log_entity", "audit_log", ["entity_type", "entity_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_audit_log_entity", table_name="audit_log")
    op.drop_table("audit_log")

    op.drop_index("ix_manual_override_zaduznica_stavka_id", table_name="manual_override")
    op.drop_table("manual_override")

    op.drop_index("ix_scan_log_zaduznica_stavka_id", table_name="scan_log")
    op.drop_table("scan_log")

    op.drop_index("ix_import_job_file_hash", table_name="import_job")
    op.drop_table("import_job")

    op.drop_index("ix_zaduznica_stavka_trebovanje_stavka_id", table_name="zaduznica_stavka")
    op.drop_index("ix_zaduznica_stavka_zaduznica_id", table_name="zaduznica_stavka")
    op.drop_table("zaduznica_stavka")

    op.drop_index("ix_zaduznica_magacioner_id", table_name="zaduznica")
    op.drop_index("ix_zaduznica_trebovanje_id", table_name="zaduznica")
    op.drop_table("zaduznica")

    op.drop_index("ix_trebovanje_stavka_trebovanje_id", table_name="trebovanje_stavka")
    op.drop_table("trebovanje_stavka")

    op.drop_index("uq_artikal_barkod", table_name="artikal_barkod")
    op.drop_index("ix_artikal_barkod_artikal_id", table_name="artikal_barkod")
    op.drop_table("artikal_barkod")

    op.drop_index("ix_trebovanje_dokument_broj", table_name="trebovanje")
    op.drop_table("trebovanje")

    op.drop_index("ix_artikal_sifra", table_name="artikal")
    op.drop_table("artikal")

    op.drop_index("ix_radnja_pantheon_id", table_name="radnja")
    op.drop_table("radnja")

    op.drop_index("ix_magacin_pantheon_id", table_name="magacin")
    op.drop_table("magacin")

    op.drop_index("ix_user_role_user_id", table_name="user_role")
    op.drop_table("user_role")

    op.drop_table("user_account")

    audit_action.drop(op.get_bind(), checkfirst=True)
    scan_result.drop(op.get_bind(), checkfirst=True)
    import_status.drop(op.get_bind(), checkfirst=True)
    zaduznica_stavka_status.drop(op.get_bind(), checkfirst=True)
    zaduznica_status.drop(op.get_bind(), checkfirst=True)
    magacin_task_priority.drop(op.get_bind(), checkfirst=True)
    trebovanje_stavka_status.drop(op.get_bind(), checkfirst=True)
    trebovanje_status.drop(op.get_bind(), checkfirst=True)
    user_role_enum.drop(op.get_bind(), checkfirst=True)

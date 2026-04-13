"""initial schema

Revision ID: 20260413_0001
Revises: 
Create Date: 2026-04-13
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260413_0001"
down_revision = None
branch_labels = None
depends_on = None


role_enum = sa.Enum("admin", "dispatcher", "driver", name="role")
shift_status_enum = sa.Enum("active", "ended", name="shiftstatus")
visit_status_enum = sa.Enum("pending", "checked_in", "checked_out", "missed", name="visitstatus")
alert_type_enum = sa.Enum("delay", "long_stop", "missed_visit", "route_deviation", name="alerttype")


def upgrade() -> None:
    role_enum.create(op.get_bind(), checkfirst=True)
    shift_status_enum.create(op.get_bind(), checkfirst=True)
    visit_status_enum.create(op.get_bind(), checkfirst=True)
    alert_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("full_name", sa.String(length=140), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", role_enum, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_phone", "users", ["phone"], unique=True)
    op.create_index("ix_users_role", "users", ["role"])

    op.create_table(
        "shifts",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("driver_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", shift_status_enum, nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_shifts_driver_id", "shifts", ["driver_id"])
    op.create_index("ix_shifts_status", "shifts", ["status"])
    op.create_index("idx_shift_driver_started", "shifts", ["driver_id", sa.text("started_at DESC")])

    op.create_table(
        "location_points",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("shift_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("shifts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("speed_kmh", sa.Float(), nullable=True),
        sa.Column("captured_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_location_points_shift_id", "location_points", ["shift_id"])
    op.create_index("ix_location_points_captured_at", "location_points", ["captured_at"])
    op.create_index("idx_location_shift_time", "location_points", ["shift_id", sa.text("captured_at DESC")])

    op.create_table(
        "visits",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("driver_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("customer_name", sa.String(length=120), nullable=False),
        sa.Column("planned_at", sa.DateTime(), nullable=False),
        sa.Column("status", visit_status_enum, nullable=False),
        sa.Column("check_in_at", sa.DateTime(), nullable=True),
        sa.Column("check_out_at", sa.DateTime(), nullable=True),
        sa.Column("check_in_latitude", sa.Float(), nullable=True),
        sa.Column("check_in_longitude", sa.Float(), nullable=True),
        sa.Column("check_out_latitude", sa.Float(), nullable=True),
        sa.Column("check_out_longitude", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_visits_driver_id", "visits", ["driver_id"])
    op.create_index("ix_visits_planned_at", "visits", ["planned_at"])
    op.create_index("ix_visits_status", "visits", ["status"])
    op.create_index("idx_visit_driver_planned", "visits", ["driver_id", "planned_at"])

    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("driver_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("shift_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("shifts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("type", alert_type_enum, nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("is_resolved", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("alerts")
    op.drop_table("visits")
    op.drop_table("location_points")
    op.drop_table("shifts")
    op.drop_table("users")

    alert_type_enum.drop(op.get_bind(), checkfirst=True)
    visit_status_enum.drop(op.get_bind(), checkfirst=True)
    shift_status_enum.drop(op.get_bind(), checkfirst=True)
    role_enum.drop(op.get_bind(), checkfirst=True)

from __future__ import annotations
from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Enum as SqlEnum, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Role(str, Enum):
    admin = "admin"
    dispatcher = "dispatcher"
    driver = "driver"


class ShiftStatus(str, Enum):
    active = "active"
    ended = "ended"


class VisitStatus(str, Enum):
    pending = "pending"
    checked_in = "checked_in"
    checked_out = "checked_out"
    missed = "missed"


class AlertType(str, Enum):
    delay = "delay"
    long_stop = "long_stop"
    missed_visit = "missed_visit"
    route_deviation = "route_deviation"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    full_name: Mapped[str] = mapped_column(String(140), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[Role] = mapped_column(SqlEnum(Role), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Shift(Base):
    __tablename__ = "shifts"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    driver_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    status: Mapped[ShiftStatus] = mapped_column(SqlEnum(ShiftStatus), default=ShiftStatus.active, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    driver: Mapped[User] = relationship()
    points: Mapped[list[LocationPoint]] = relationship(back_populates="shift")


class LocationPoint(Base):
    __tablename__ = "location_points"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    shift_id: Mapped[str] = mapped_column(ForeignKey("shifts.id", ondelete="CASCADE"), index=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    speed_kmh: Mapped[float | None] = mapped_column(Float, nullable=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)

    shift: Mapped[Shift] = relationship(back_populates="points")


class Visit(Base):
    __tablename__ = "visits"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    driver_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    customer_name: Mapped[str] = mapped_column(String(120), nullable=False)
    planned_at: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=False)
    status: Mapped[VisitStatus] = mapped_column(SqlEnum(VisitStatus), default=VisitStatus.pending, index=True)
    check_in_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    check_out_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    check_in_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    check_in_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    check_out_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    check_out_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    driver_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    shift_id: Mapped[str | None] = mapped_column(ForeignKey("shifts.id", ondelete="SET NULL"), nullable=True)
    type: Mapped[AlertType] = mapped_column(SqlEnum(AlertType), index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(120), index=True)
    entity_type: Mapped[str] = mapped_column(String(80), index=True)
    entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


Index("idx_shift_driver_started", Shift.driver_id, Shift.started_at.desc())
Index("idx_location_shift_time", LocationPoint.shift_id, LocationPoint.captured_at.desc())
Index("idx_visit_driver_planned", Visit.driver_id, Visit.planned_at)

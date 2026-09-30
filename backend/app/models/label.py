"""Entity label and label change log models."""

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class EntityLabel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "entity_labels"

    entity_name: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    chain: Mapped[str] = mapped_column(String(32), default="ethereum", nullable=False)
    address: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    cluster_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    label_origin: Mapped[str] = mapped_column(String(32), default="observed_label", nullable=False)
    source_name: Mapped[str] = mapped_column(String(128), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_reference: Mapped[str] = mapped_column(String(512), nullable=False)
    verification_level: Mapped[str] = mapped_column(String(32), nullable=False)
    observed_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_verified_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    scope_notes: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_shared_infrastructure: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("chain", "address", "source_name", name="uq_entity_labels_addr_source"),
    )


class LabelChangeLog(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "label_change_log"

    label_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entity_labels.id", ondelete="CASCADE"), nullable=False
    )
    change_type: Mapped[str] = mapped_column(String(32), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    changed_by: Mapped[str] = mapped_column(String(128), nullable=False)
    previous_value: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    new_value: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

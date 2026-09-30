"""Case database models."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Case(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "cases"

    case_reference: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    access_token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    chain: Mapped[str] = mapped_column(String(32), default="ethereum", nullable=False)
    reported_address: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    reported_tx_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    incident_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    incident_date_precision: Mapped[str] = mapped_column(String(32), default="unknown", nullable=False)
    reported_amount: Mapped[Decimal | None] = mapped_column(Numeric(38, 18), nullable=True)
    reported_asset: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    data_snapshot_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    code_version: Mapped[str] = mapped_column(String(32), default="0.1.0", nullable=False)
    model_version: Mapped[str] = mapped_column(String(32), default="0.1.0", nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    analysis_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    analysis_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(String(512), nullable=True)

    private_details: Mapped["CasePrivateDetails | None"] = relationship(
        "CasePrivateDetails", back_populates="case", uselist=False, cascade="all, delete-orphan"
    )


class CasePrivateDetails(Base, TimestampMixin):
    __tablename__ = "case_private_details"

    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), primary_key=True
    )
    narrative_ciphertext: Mapped[str | None] = mapped_column(String(8192), nullable=True)
    contact_ciphertext: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    consent_recorded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    retention_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    case: Mapped[Case] = relationship("Case", back_populates="private_details")

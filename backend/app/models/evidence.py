"""Case evidence, paths, attributions, signals, and links models."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.types import JSONType, UUIDType


class CasePath(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "case_paths"

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    path_index: Mapped[int] = mapped_column(Integer, nullable=False)
    hop_count: Mapped[int] = mapped_column(Integer, nullable=False)
    start_address: Mapped[str] = mapped_column(String(128), nullable=False)
    end_address: Mapped[str] = mapped_column(String(128), nullable=False)
    first_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    elapsed_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    traced_value_amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    traced_value_asset: Mapped[str] = mapped_column(String(32), nullable=False)
    tracing_method: Mapped[str] = mapped_column(String(32), default="proportional", nullable=False)
    value_continuity_ratio: Mapped[float] = mapped_column(
        Numeric(10, 6), default=1.0, nullable=False
    )
    relevance_criteria: Mapped[dict[str, Any]] = mapped_column(
        JSONType, default=dict, nullable=False
    )
    has_break: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    break_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    edges: Mapped[list[dict[str, Any]]] = mapped_column(JSONType, default=list, nullable=False)


class CaseAttribution(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "case_attributions"

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    path_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("case_paths.id", ondelete="SET NULL"), nullable=True
    )
    label_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("entity_labels.id", ondelete="SET NULL"), nullable=True
    )
    connection_type: Mapped[str] = mapped_column(String(32), nullable=False)
    attribution_state: Mapped[str] = mapped_column(String(64), nullable=False)
    attribution_confidence_level: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence_factors: Mapped[dict[str, Any]] = mapped_column(
        JSONType, default=dict, nullable=False
    )
    label_is_stale: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    shared_infrastructure_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    explanation: Mapped[str] = mapped_column(String(2048), nullable=False)


class CaseSignal(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "case_signals"

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    path_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("case_paths.id", ondelete="SET NULL"), nullable=True
    )
    signal_key: Mapped[str] = mapped_column(String(64), nullable=False)
    level: Mapped[str] = mapped_column(String(32), nullable=False)
    evidence_tag: Mapped[str] = mapped_column(String(32), default="inferred", nullable=False)
    feature_values: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    explanation: Mapped[str] = mapped_column(String(1024), nullable=False)
    limitation_note: Mapped[str] = mapped_column(
        String(256),
        default="This pattern can also result from legitimate activity.",
        nullable=False,
    )


class CaseLink(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "case_links"

    case_a_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    case_b_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    strength: Mapped[str] = mapped_column(String(32), nullable=False)
    evidence_tag: Mapped[str] = mapped_column(String(32), default="derived", nullable=False)
    shared_addresses: Mapped[list[str]] = mapped_column(JSONType, default=list, nullable=False)
    shared_transactions: Mapped[list[str]] = mapped_column(JSONType, default=list, nullable=False)
    shared_path_segments: Mapped[list[str]] = mapped_column(JSONType, default=list, nullable=False)
    shared_infrastructure_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    temporal_notes: Mapped[str | None] = mapped_column(String(512), nullable=True)
    first_observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    change_history: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONType, default=list, nullable=False
    )

    __table_args__ = (UniqueConstraint("case_a_id", "case_b_id", name="uq_case_links_ab"),)

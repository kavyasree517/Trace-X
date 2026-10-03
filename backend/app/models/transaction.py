"""Transaction and case-transaction mapping models."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.types import UUIDType


class Transaction(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "transactions"

    chain: Mapped[str] = mapped_column(String(32), nullable=False)
    tx_hash: Mapped[str] = mapped_column(String(66), nullable=False)
    log_index: Mapped[int] = mapped_column(Integer, default=-1, nullable=False)
    transfer_kind: Mapped[str] = mapped_column(String(16), nullable=False)
    block_number: Mapped[int] = mapped_column(Integer, nullable=False)
    block_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sender: Mapped[str] = mapped_column(String(128), nullable=False)
    receiver: Mapped[str] = mapped_column(String(128), nullable=False)
    asset_id: Mapped[str] = mapped_column(String(128), nullable=False)
    asset_symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    asset_decimals: Mapped[int | None] = mapped_column(Integer, nullable=True)
    amount_raw: Mapped[Decimal] = mapped_column(Numeric(78, 0), nullable=False)
    amount_decimal: Mapped[Decimal | None] = mapped_column(Numeric(38, 18), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="success", nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "chain",
            "tx_hash",
            "log_index",
            "transfer_kind",
            "sender",
            "receiver",
            "asset_id",
            name="uq_transactions_event",
        ),
        Index("ix_transactions_sender_time", "sender", "block_timestamp"),
        Index("ix_transactions_receiver_time", "receiver", "block_timestamp"),
        Index("ix_transactions_tx_hash", "tx_hash"),
    )


class CaseTransaction(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "case_transactions"

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False
    )
    hop_depth: Mapped[int] = mapped_column(Integer, nullable=False)
    direction: Mapped[str] = mapped_column(String(16), nullable=False)
    included_reason: Mapped[str] = mapped_column(String(64), nullable=False)

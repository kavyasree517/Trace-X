"""Shared pytest fixtures for backend tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from app.adapters.base import NormalizedTransfer
from app.core.enums import TransferKind

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
FIXTURES_DIR = DATA_DIR / "fixtures"
LABEL_REGISTRY_DIR = DATA_DIR / "label_registry"

ADDRESS_A = "0x1111111111111111111111111111111111111111"
ADDRESS_B = "0x2222222222222222222222222222222222222222"
ADDRESS_C = "0x3333333333333333333333333333333333333333"
ADDRESS_D = "0x4444444444444444444444444444444444444444"
ADDRESS_EXCHANGE = "0x5555555555555555555555555555555555555555"
ADDRESS_MIXER = "0x6666666666666666666666666666666666666666"

BASE_TIME = datetime(2026, 3, 15, 12, 0, 0, tzinfo=UTC)


def make_transfer(
    sender: str,
    receiver: str,
    *,
    amount: str = "1.0",
    asset_id: str = "native",
    asset_symbol: str = "ETH",
    decimals: int | None = 18,
    minutes: int = 0,
    tx_hash: str | None = None,
    log_index: int = 0,
    transfer_kind: TransferKind = TransferKind.NATIVE,
    status: str = "success",
    block_number: int = 19_450_000,
) -> NormalizedTransfer:
    """Build a normalized transfer for tests with sensible defaults."""
    resolved_hash = tx_hash or f"0x{'ab' * 31}{log_index:02x}"
    raw = int(Decimal(amount) * (Decimal(10) ** (decimals if decimals is not None else 18)))
    return NormalizedTransfer(
        chain="ethereum",
        tx_hash=resolved_hash,
        log_index=log_index,
        transfer_kind=transfer_kind,
        block_number=block_number,
        block_timestamp=BASE_TIME + timedelta(minutes=minutes),
        sender=sender,
        receiver=receiver,
        asset_id=asset_id,
        asset_symbol=asset_symbol,
        asset_decimals=decimals,
        amount_raw=raw,
        amount_decimal=Decimal(amount),
        status=status,
        source="mock_fixture",
        retrieved_at=BASE_TIME,
    )


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def label_registry_dir() -> Path:
    return LABEL_REGISTRY_DIR

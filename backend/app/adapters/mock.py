"""Mock blockchain data adapter loading deterministic JSON fixtures."""

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from app.adapters.base import AdapterResult, ChainDataAdapter, NormalizedTransfer
from app.core.enums import EvidenceTag, TransferKind
from app.core.security import canonicalize_address


class MockDataAdapter(ChainDataAdapter):
    """Deterministic adapter reading synthetic JSON fixtures from disk."""

    def __init__(self, fixtures_dir: Path | None = None) -> None:
        if fixtures_dir is None:
            # Default to backend/data/fixtures
            self.fixtures_dir = Path(__file__).resolve().parent.parent.parent / "data" / "fixtures"
        else:
            self.fixtures_dir = fixtures_dir
        self._fixtures: dict[str, dict[str, Any]] = {}
        self._load_fixtures()

    def _load_fixtures(self) -> None:
        if not self.fixtures_dir.exists():
            return
        for file in self.fixtures_dir.glob("*.json"):
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                fixture_id = data.get("fixture_id", file.stem)
                self._fixtures[fixture_id] = data
            except Exception:
                continue

    def validate_address(self, address: str) -> bool:
        try:
            canonicalize_address(address)
            return True
        except ValueError:
            return False

    def _transfer_from_dict(self, item: dict[str, Any], chain: str) -> NormalizedTransfer:
        raw_amt = int(item["amount_raw"])
        dec_amt = Decimal(item["amount_decimal"]) if item.get("amount_decimal") else None
        ts = datetime.fromisoformat(item["block_timestamp"].replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=UTC)

        sender = canonicalize_address(item["sender"])
        receiver = canonicalize_address(item["receiver"])

        return NormalizedTransfer(
            chain=chain,
            tx_hash=item["tx_hash"].lower(),
            log_index=item.get("log_index", -1),
            transfer_kind=TransferKind(item.get("transfer_kind", "native")),
            block_number=item.get("block_number", 0),
            block_timestamp=ts,
            sender=sender,
            receiver=receiver,
            asset_id=item.get("asset_id", "native"),
            asset_symbol=item.get("asset_symbol", "ETH"),
            asset_decimals=item.get("asset_decimals", 18),
            amount_raw=raw_amt,
            amount_decimal=dec_amt,
            status=item.get("status", "success"),
            source="mock_fixture",
            retrieved_at=datetime.now(UTC),
            is_contract_creation=item.get("is_contract_creation", False),
            is_self_transfer=(sender == receiver),
            evidence_tag=EvidenceTag.OBSERVED,
        )

    async def get_native_transfers(
        self,
        address: str,
        start_block: int | None = None,
        end_block: int | None = None,
    ) -> AdapterResult:
        try:
            canonical_addr = canonicalize_address(address)
        except ValueError:
            return AdapterResult(errors=["invalid_address"])

        matched_transfers: list[NormalizedTransfer] = []
        for fixture in self._fixtures.values():
            chain = fixture.get("chain", "ethereum")
            for item in fixture.get("transfers", []):
                if item.get("transfer_kind") in ("native", "internal", None):
                    s = canonicalize_address(item["sender"])
                    r = canonicalize_address(item["receiver"])
                    if canonical_addr in (s, r):
                        matched_transfers.append(self._transfer_from_dict(item, chain))

        return AdapterResult(
            items=matched_transfers,
            source_name="mock_fixture",
            retrieved_at=datetime.now(UTC),
            request_count=1,
            truncated=False,
        )

    async def get_internal_transfers(
        self,
        address: str,
        start_block: int | None = None,
        end_block: int | None = None,
    ) -> AdapterResult:
        return AdapterResult(
            items=[],
            source_name="mock_fixture",
            retrieved_at=datetime.now(UTC),
            request_count=1,
            truncated=False,
        )

    async def get_token_transfers(
        self,
        address: str,
        contract_address: str | None = None,
        start_block: int | None = None,
        end_block: int | None = None,
    ) -> AdapterResult:
        try:
            canonical_addr = canonicalize_address(address)
        except ValueError:
            return AdapterResult(errors=["invalid_address"])

        matched_transfers: list[NormalizedTransfer] = []
        for fixture in self._fixtures.values():
            chain = fixture.get("chain", "ethereum")
            for item in fixture.get("transfers", []):
                if item.get("transfer_kind") == "token":
                    s = canonicalize_address(item["sender"])
                    r = canonicalize_address(item["receiver"])
                    if canonical_addr in (s, r):
                        matched_transfers.append(self._transfer_from_dict(item, chain))

        return AdapterResult(
            items=matched_transfers,
            source_name="mock_fixture",
            retrieved_at=datetime.now(UTC),
            request_count=1,
            truncated=False,
        )

    async def get_transaction(self, tx_hash: str) -> NormalizedTransfer | None:
        target_hash = tx_hash.lower()
        for fixture in self._fixtures.values():
            chain = fixture.get("chain", "ethereum")
            for item in fixture.get("transfers", []):
                if item.get("tx_hash", "").lower() == target_hash:
                    return self._transfer_from_dict(item, chain)
        return None

    async def block_for_timestamp(self, timestamp: datetime) -> int:
        return 19450000

    def describe(self) -> dict[str, str]:
        return {
            "adapter": "mock",
            "type": "synthetic_fixtures",
            "mode": "deterministic_offline",
        }

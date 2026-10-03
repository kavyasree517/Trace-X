"""Abstract base definitions for blockchain data adapters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal

from app.core.enums import EvidenceTag, TransferKind


@dataclass(frozen=True)
class NormalizedTransfer:
    """Normalized on-chain asset transfer representation."""

    chain: str
    tx_hash: str
    log_index: int
    transfer_kind: TransferKind
    block_number: int
    block_timestamp: datetime
    sender: str
    receiver: str
    asset_id: str
    asset_symbol: str
    asset_decimals: int | None
    amount_raw: int
    amount_decimal: Decimal | None
    status: str  # "success" or "failed"
    source: str
    retrieved_at: datetime
    is_contract_creation: bool = False
    is_self_transfer: bool = False
    evidence_tag: EvidenceTag = EvidenceTag.OBSERVED

    @property
    def edge_key(self) -> tuple[str, int]:
        """Return the graph edge key mandated by the engine."""
        return (self.tx_hash, self.log_index)

    @property
    def is_success(self) -> bool:
        return self.status == "success"


@dataclass
class AdapterResult:
    """Standardized response from adapter queries."""

    items: list[NormalizedTransfer] = field(default_factory=list)
    source_name: str = "unknown"
    retrieved_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    request_count: int = 1
    truncated: bool = False
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class ChainDataAdapter(ABC):
    """Abstract interface defining required blockchain query methods."""

    @abstractmethod
    def validate_address(self, address: str) -> bool:
        """Validate if an address conforms to chain standards."""
        pass

    @abstractmethod
    async def get_native_transfers(
        self,
        address: str,
        start_block: int | None = None,
        end_block: int | None = None,
    ) -> AdapterResult:
        """Fetch native currency (e.g. ETH) transfers for an address."""
        pass

    @abstractmethod
    async def get_internal_transfers(
        self,
        address: str,
        start_block: int | None = None,
        end_block: int | None = None,
    ) -> AdapterResult:
        """Fetch internal contract call transfers for an address."""
        pass

    @abstractmethod
    async def get_token_transfers(
        self,
        address: str,
        contract_address: str | None = None,
        start_block: int | None = None,
        end_block: int | None = None,
    ) -> AdapterResult:
        """Fetch standard token transfers for an address."""
        pass

    @abstractmethod
    async def get_transaction(self, tx_hash: str) -> NormalizedTransfer | None:
        """Fetch details for a specific transaction hash."""
        pass

    @abstractmethod
    async def block_for_timestamp(self, timestamp: datetime) -> int:
        """Resolve block number closest to given UTC timestamp."""
        pass

    @abstractmethod
    def describe(self) -> dict[str, str]:
        """Return metadata describing adapter identity and capabilities."""
        pass

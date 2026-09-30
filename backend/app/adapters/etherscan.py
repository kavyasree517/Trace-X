"""Etherscan adapter implementation stub."""

from datetime import datetime

from app.adapters.base import AdapterResult, ChainDataAdapter, NormalizedTransfer
from app.core.security import canonicalize_address


class EtherscanAdapter(ChainDataAdapter):
    """Etherscan-compatible HTTP API adapter. Full implementation deferred to Phase 2."""

    def __init__(self, api_key: str = "", base_url: str = "https://api.etherscan.io/api") -> None:
        self.api_key = api_key
        self.base_url = base_url

    def validate_address(self, address: str) -> bool:
        try:
            canonicalize_address(address)
            return True
        except ValueError:
            return False

    async def get_native_transfers(
        self,
        address: str,
        start_block: int | None = None,
        end_block: int | None = None,
    ) -> AdapterResult:
        raise NotImplementedError("Live Etherscan ingestion is scheduled for Phase 2.")

    async def get_internal_transfers(
        self,
        address: str,
        start_block: int | None = None,
        end_block: int | None = None,
    ) -> AdapterResult:
        raise NotImplementedError("Internal contract transfer extraction is scheduled for Phase 2.")

    async def get_token_transfers(
        self,
        address: str,
        contract_address: str | None = None,
        start_block: int | None = None,
        end_block: int | None = None,
    ) -> AdapterResult:
        raise NotImplementedError("ERC-20 token transfer extraction is scheduled for Phase 2.")

    async def get_transaction(self, tx_hash: str) -> NormalizedTransfer | None:
        raise NotImplementedError("Single transaction lookup is scheduled for Phase 2.")

    async def block_for_timestamp(self, timestamp: datetime) -> int:
        raise NotImplementedError("Timestamp block resolution is scheduled for Phase 2.")

    def describe(self) -> dict[str, str]:
        return {
            "adapter": "etherscan",
            "status": "deferred_phase_2",
            "base_url": self.base_url,
        }

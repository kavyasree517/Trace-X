"""Ethereum JSON-RPC adapter stub."""

from datetime import datetime

from app.adapters.base import AdapterResult, ChainDataAdapter, NormalizedTransfer
from app.core.security import canonicalize_address


class RpcAdapterStub(ChainDataAdapter):
    """Direct Ethereum JSON-RPC client adapter stub."""

    def __init__(self, endpoint_url: str = "") -> None:
        self.endpoint_url = endpoint_url

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
        raise NotImplementedError("Direct RPC node synchronization is deferred.")

    async def get_internal_transfers(
        self,
        address: str,
        start_block: int | None = None,
        end_block: int | None = None,
    ) -> AdapterResult:
        raise NotImplementedError("RPC debug_traceTransaction extraction is deferred.")

    async def get_token_transfers(
        self,
        address: str,
        contract_address: str | None = None,
        start_block: int | None = None,
        end_block: int | None = None,
    ) -> AdapterResult:
        raise NotImplementedError("RPC eth_getLogs token filtering is deferred.")

    async def get_transaction(self, tx_hash: str) -> NormalizedTransfer | None:
        raise NotImplementedError("RPC transaction lookup is deferred.")

    async def block_for_timestamp(self, timestamp: datetime) -> int:
        raise NotImplementedError("RPC timestamp block search is deferred.")

    def describe(self) -> dict[str, str]:
        return {
            "adapter": "rpc",
            "status": "documented_stub",
        }

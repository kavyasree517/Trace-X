"""Adapter registry and factory."""

from functools import lru_cache

from app.adapters.base import ChainDataAdapter
from app.adapters.etherscan import EtherscanAdapter
from app.adapters.mock import MockDataAdapter
from app.adapters.rpc_stub import RpcAdapterStub
from app.core.config import get_settings


@lru_cache(maxsize=1)
def get_data_adapter() -> ChainDataAdapter:
    """Return configured blockchain data adapter instance."""
    settings = get_settings()
    adapter_name = settings.DATA_ADAPTER.lower()

    if adapter_name == "mock":
        return MockDataAdapter()
    if adapter_name == "etherscan":
        return EtherscanAdapter(
            api_key=settings.EXPLORER_API_KEY,
            base_url=settings.EXPLORER_API_BASE_URL,
        )
    if adapter_name == "rpc":
        return RpcAdapterStub()

    raise ValueError(f"Unknown DATA_ADAPTER configured: {settings.DATA_ADAPTER}")

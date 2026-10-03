"""Constants and system defaults for TRACE-X."""

from typing import Final

# Supported blockchain networks
SUPPORTED_CHAINS: Final[list[str]] = ["ethereum"]

# Primary tracked assets on Ethereum mainnet
SUPPORTED_ASSET_SYMBOLS: Final[list[str]] = ["ETH", "USDT", "USDC", "DAI"]

# Ethereum mainnet token contract addresses (checksummed EIP-55)
TOKEN_CONTRACTS: Final[dict[str, str]] = {
    "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
}

# Standard token decimals
TOKEN_DECIMALS: Final[dict[str, int]] = {
    "ETH": 18,
    "USDT": 6,
    "USDC": 6,
    "DAI": 18,
}

# Standing disclosures
STANDING_STATEMENT: Final[str] = (
    "This output is an investigative lead for human review. "
    "It is not a legal finding and does not accuse any person or organization."
)

DEMO_NOTICE: Final[str] = (
    "Demonstration mode. This result uses simulated data or synthetic labels "
    "and does not describe a real investigation."
)

SIGNAL_LIMITATION_NOTE: Final[str] = "This pattern can also result from legitimate activity."

RELATED_REPORT_CAUTION: Final[str] = (
    "These cases share the on-chain evidence shown below. "
    "Shared addresses can result from common services, exchange deposit infrastructure, "
    "or coincidence, and do not by themselves indicate common ownership or coordination."
)

NOVELTY_STATEMENT: Final[str] = (
    "The contribution is an integrated, victim-report-conditioned, uncertainty-aware "
    "investigation workflow combining case-focused tracing, provenance-aware exchange "
    "attribution, and cross-report corroboration in one explainable output. "
    "Novelty is a hypothesis to be validated by literature review, baseline comparison, "
    "and ablation."
)

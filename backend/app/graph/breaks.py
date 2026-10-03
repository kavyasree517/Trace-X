"""Path break detection.

A break marks the point where the investigation can no longer follow value
with confidence. Breaks are recorded, never silently smoothed over, so that a
truncated path is reported as ``insufficient_data`` rather than presented as a
complete trace.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.core.enums import EntityType, PathBreakReason


class LabelLookup(Protocol):
    """Minimal label view required by break detection."""

    def entity_types(self, address: str) -> set[str]:
        """Return entity types recorded for an address."""
        ...


@dataclass(frozen=True)
class BreakResult:
    """Outcome of break evaluation for a single edge or node."""

    has_break: bool
    reason: PathBreakReason | None = None
    detail: str | None = None

    @classmethod
    def clear(cls) -> BreakResult:
        return cls(has_break=False)

    @classmethod
    def broken(cls, reason: PathBreakReason, detail: str) -> BreakResult:
        return cls(has_break=True, reason=reason, detail=detail)


_MIXER_TYPES = frozenset({EntityType.MIXER.value})
_BRIDGE_TYPES = frozenset({EntityType.BRIDGE.value})
_SUPPORTED_SERVICE_TYPES = frozenset(
    {
        EntityType.EXCHANGE.value,
        EntityType.EXCHANGE_HOT_WALLET.value,
        EntityType.EXCHANGE_DEPOSIT_ADDRESS.value,
        EntityType.PAYMENT_SERVICE.value,
        EntityType.DECENTRALIZED_EXCHANGE.value,
        EntityType.SMART_CONTRACT_SERVICE.value,
    }
)


def detect_node_break(address: str, entity_types: set[str]) -> BreakResult:
    """Return the break caused by entering an address with these label types."""
    if entity_types & _MIXER_TYPES:
        return BreakResult.broken(
            PathBreakReason.MIXER_INTERACTION,
            f"Address {address} is labelled as a mixer.",
        )
    if entity_types & _BRIDGE_TYPES:
        return BreakResult.broken(
            PathBreakReason.BRIDGE_INTERACTION,
            f"Address {address} is labelled as a bridge.",
        )
    if "privacy_protocol" in entity_types:
        return BreakResult.broken(
            PathBreakReason.PRIVACY_PROTOCOL,
            f"Address {address} appears in the maintained privacy protocol list.",
        )
    if entity_types and not entity_types & _SUPPORTED_SERVICE_TYPES:
        return BreakResult.broken(
            PathBreakReason.UNSUPPORTED_CONTRACT,
            f"Address {address} has a label type this tool does not trace through.",
        )
    return BreakResult.clear()


def detect_asset_change(previous_asset: str, next_asset: str, decoded: bool) -> BreakResult:
    """Return a break when the asset identity changes between hops.

    An asset change ends value tracing unless the swap was decoded, because a
    decoded swap preserves the traced value across assets.
    """
    if previous_asset == next_asset:
        return BreakResult.clear()
    if decoded:
        return BreakResult.clear()
    return BreakResult.broken(
        PathBreakReason.SWAP_ASSET_CHANGE,
        f"Asset changed from {previous_asset} to {next_asset} without a decoded swap.",
    )


def detect_limit_break(reason: PathBreakReason, detail: str) -> BreakResult:
    """Return a break recorded when an expansion budget was exhausted."""
    return BreakResult.broken(reason, detail)


def evaluate_edge(
    receiver: str,
    receiver_entity_types: set[str],
    previous_asset: str,
    next_asset: str,
    swap_decoded: bool = False,
) -> BreakResult:
    """Evaluate node and asset breaks for one edge, node break taking priority."""
    node_break = detect_node_break(receiver, receiver_entity_types)
    if node_break.has_break:
        return node_break
    return detect_asset_change(previous_asset, next_asset, swap_decoded)

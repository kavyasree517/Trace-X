"""Shared infrastructure detection.

An address that many unrelated parties send to, such as an exchange deposit
address, a bridge, or a service contract, cannot identify a single operator.
Reaching such an address shows that funds moved to infrastructure that others
also use. It does not establish common ownership, coordination, or involvement.

This module therefore always presents the flag as "possible shared
infrastructure" and never as evidence of a relationship between parties.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.attribution.registry import LabelRegistry
from app.core.enums import EntityType

# Entity types that are infrastructure by nature.
INFRASTRUCTURE_ENTITY_TYPES = frozenset(
    {
        EntityType.EXCHANGE_DEPOSIT_ADDRESS.value,
        EntityType.BRIDGE.value,
        EntityType.MIXER.value,
        EntityType.SMART_CONTRACT_SERVICE.value,
        EntityType.DECENTRALIZED_EXCHANGE.value,
    }
)

INFRASTRUCTURE_CAVEAT = (
    "This address is flagged as possibly shared infrastructure. Reaching it shows that "
    "funds moved to a service that other parties also use. It does not indicate common "
    "ownership, coordination, or involvement."
)


@dataclass(frozen=True)
class InfrastructureAssessment:
    """Whether an address should be treated as possibly shared infrastructure."""

    is_shared_infrastructure: bool
    reasons: tuple[str, ...] = ()

    @property
    def caveat(self) -> str | None:
        return INFRASTRUCTURE_CAVEAT if self.is_shared_infrastructure else None


def assess_address(
    chain: str,
    address: str,
    registry: LabelRegistry,
    high_degree_threshold: int,
    observed_degree: int = 0,
) -> InfrastructureAssessment:
    """Return the shared-infrastructure assessment for one address.

    An address is flagged when the registry marks it as shared infrastructure,
    when its entity type is infrastructure by nature, or when its observed
    degree in the traced graph exceeds the configured hub threshold.
    """
    labels = registry.lookup(chain, address)
    reasons: list[str] = []

    if any(label.is_shared_infrastructure for label in labels):
        reasons.append("Registry marks this address as shared infrastructure.")

    entity_types = {label.entity_type for label in labels}
    matching = entity_types & INFRASTRUCTURE_ENTITY_TYPES
    if matching:
        reasons.append(
            f"Entity type {', '.join(sorted(matching))} is infrastructure used by many parties."
        )

    if observed_degree > high_degree_threshold:
        reasons.append(
            f"Observed degree {observed_degree} exceeds the hub threshold "
            f"of {high_degree_threshold}."
        )

    return InfrastructureAssessment(
        is_shared_infrastructure=bool(reasons),
        reasons=tuple(reasons),
    )


def exclude_infrastructure_addresses(
    addresses: set[str],
    chain: str,
    registry: LabelRegistry,
    hub_exclusion_degree: int,
    degrees: dict[str, int] | None = None,
) -> set[str]:
    """Return the subset of addresses that count as specific, not infrastructure.

    Corroboration relies on this: an overlap made only of deposit addresses or
    hubs is not evidence that two cases involve the same destination.
    """
    degrees = degrees or {}
    kept: set[str] = set()

    for address in addresses:
        if address in registry.shared_infrastructure_addresses(chain):
            continue
        assessment = assess_address(
            chain,
            address,
            registry,
            high_degree_threshold=hub_exclusion_degree,
            observed_degree=degrees.get(address, 0),
        )
        if not assessment.is_shared_infrastructure:
            kept.add(address)

    return kept

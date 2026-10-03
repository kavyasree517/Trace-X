"""Path-to-label matching and explanation generation."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date

from app.attribution.confidence import (
    ConfidenceDecision,
    ConfidenceInput,
    decide_attribution_state,
    evaluate_confidence,
    is_label_stale,
)
from app.attribution.registry import EntityLabelRecord, LabelRegistry
from app.core.enums import (
    AttributionConfidenceLevel,
    AttributionState,
    ConnectionType,
    EntityType,
)
from app.graph.paths import CandidatePath

# Direct connection means the label sits on the first receiver of the seed
# transfer. Everything further along is indirect.
_EXCHANGE_TYPES = frozenset(
    {
        EntityType.EXCHANGE.value,
        EntityType.EXCHANGE_HOT_WALLET.value,
        EntityType.EXCHANGE_DEPOSIT_ADDRESS.value,
        EntityType.DECENTRALIZED_EXCHANGE.value,
        EntityType.PAYMENT_SERVICE.value,
        EntityType.OTHER_SERVICE.value,
        EntityType.SMART_CONTRACT_SERVICE.value,
    }
)


@dataclass(frozen=True)
class PathAttribution:
    """Attribution outcome for one path and one label."""

    address: str
    label: EntityLabelRecord
    connection_type: ConnectionType
    attribution_state: AttributionState
    confidence_level: AttributionConfidenceLevel
    confidence_factors: dict[str, object]
    label_is_stale: bool
    shared_infrastructure_flag: bool
    explanation: str
    hop_count: int

    @property
    def is_reported_entity(self) -> bool:
        """Return True when the match describes the entity the reporter named."""
        return self.label.entity_type in _EXCHANGE_TYPES


@dataclass
class AttributionResult:
    """All attributions produced for one case plus abstention information."""

    attributions: list[PathAttribution] = field(default_factory=list)
    unattributed_paths: int = 0
    synthetic_suppressed: int = 0


def classify_connection(path: CandidatePath, address: str) -> ConnectionType:
    """Return whether the labelled address is reached directly or indirectly."""
    if len(path.addresses) < 2:
        return ConnectionType.INDIRECT
    if address == path.addresses[1]:
        return ConnectionType.DIRECT
    return ConnectionType.INDIRECT


def match_path(
    path: CandidatePath,
    registry: LabelRegistry,
    chain: str,
    is_demo: bool,
    today: date,
    stale_after_days: int,
) -> list[PathAttribution]:
    """Return every attribution applicable to the terminal address of a path.

    Only the path terminal is matched. An unlabelled terminal produces no
    attribution, which the caller reports as
    ``no_match_in_current_references``.
    """
    if not path.addresses:
        return []

    terminal = path.addresses[-1]
    labels = registry.lookup(chain, terminal)
    if not labels:
        return []

    connection = classify_connection(path, terminal)
    path_intact = not path.has_break

    results: list[PathAttribution] = []
    for label in labels:
        stale = is_label_stale(label.last_verified_at, today, stale_after_days)
        source_count = len(registry.sources_for(chain, terminal))

        decision: ConfidenceDecision = evaluate_confidence(
            ConfidenceInput(
                verification_level=label.verification_level,
                label_origin=label.label_origin,
                independent_source_count=source_count,
                connection_type=connection,
                path_intact=path_intact,
                label_is_stale=stale,
                scope_match=label.scope_notes is not None,
                is_demo=is_demo,
            )
        )

        synthetic_suppressed = decision.is_synthetic and not is_demo
        state = decide_attribution_state(
            decision,
            has_label=True,
            is_synthetic_outside_demo=synthetic_suppressed,
        )

        results.append(
            PathAttribution(
                address=terminal,
                label=label,
                connection_type=connection,
                attribution_state=state,
                confidence_level=decision.level,
                confidence_factors=decision.factors_payload,
                label_is_stale=stale,
                shared_infrastructure_flag=label.is_shared_infrastructure,
                explanation=explain_attribution(
                    address=terminal,
                    label=label,
                    connection=connection,
                    confidence=decision,
                    stale=stale,
                    hop_count=path.hop_count,
                    state=state,
                ),
                hop_count=path.hop_count,
            )
        )

    return results


_STATE_SENTENCE: dict[AttributionState, str] = {
    AttributionState.VERIFIED_LABEL_MATCH: " This describes where funds moved.",
    AttributionState.POTENTIAL_ASSOCIATION: (
        " This is a potential connection based on observed transfers."
    ),
    AttributionState.INSUFFICIENT_DATA: (
        " The path contains a break, so the connection is not established."
    ),
    AttributionState.NO_MATCH_IN_CURRENT_REFERENCES: (
        " No usable match was found in current references."
    ),
}


def explain_attribution(
    *,
    address: str,
    label: EntityLabelRecord,
    connection: ConnectionType,
    confidence: ConfidenceDecision,
    stale: bool,
    hop_count: int,
    state: AttributionState,
) -> str:
    """Return a neutral explanation naming source, connection and verification.

    The text describes where funds moved and where the label came from. It
    never states or implies that the labelled service knew of or took part in
    any wrongdoing.
    """
    hop_word = "transfer" if hop_count == 1 else "transfers"
    base = (
        f"Address {address} is labelled {label.entity_name} by {label.source_name} "
        f"({label.verification_level}) and was reached after {hop_count} {hop_word} "
        f"by a {connection.value} connection."
    )

    base += _STATE_SENTENCE.get(
        state,
        " No usable match was found in current references.",
    )

    if stale:
        base += " The label has not been verified recently, so it may be out of date."
    if label.is_shared_infrastructure:
        base += (
            " This address is flagged as possibly shared infrastructure, so it may "
            "not identify a single operator."
        )
    if label.scope_notes:
        base += f" Scope note: {label.scope_notes}"

    return base + " This does not show that the service knew of or took part in any wrongdoing."


def best_confidence(attributions: Sequence[PathAttribution]) -> AttributionConfidenceLevel:
    """Return the strongest confidence level across all attributions."""
    order = [
        AttributionConfidenceLevel.NONE,
        AttributionConfidenceLevel.LOW,
        AttributionConfidenceLevel.MEDIUM,
        AttributionConfidenceLevel.HIGH,
    ]
    present = {a.confidence_level for a in attributions}
    for level in reversed(order):
        if level in present:
            return level
    return AttributionConfidenceLevel.NONE


def headline_state_from(attributions: Sequence[PathAttribution]) -> AttributionState | None:
    """Return the strongest attribution state present, or None when there are none."""
    if any(a.attribution_state is AttributionState.VERIFIED_LABEL_MATCH for a in attributions):
        return AttributionState.VERIFIED_LABEL_MATCH
    if any(a.attribution_state is AttributionState.POTENTIAL_ASSOCIATION for a in attributions):
        return AttributionState.POTENTIAL_ASSOCIATION
    return None

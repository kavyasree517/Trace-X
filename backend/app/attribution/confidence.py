"""Confidence rules for label attribution.

Confidence is expressed as a documented level, never as a percentage or a
probability. Every rule below returns all contributing factors so that the
level can be explained in the report.

Rules, in the order they are evaluated:

* ``high``: a level 3 primary source, or two or more independent level 2
  sources, on an observed label that is not stale, reached by a direct or
  indirect connection along an intact path.
* ``medium``: a single level 2 source, or a level 3 source whose label is
  stale, on an observed label along an intact path.
* ``low``: a level 1 community source only, an inferred cluster label, a
  stale single source, a path containing a break, or a synthetic label shown
  in demonstration mode.
* ``none``: no usable label, or a synthetic label outside demonstration mode.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta

from app.core.enums import (
    AttributionConfidenceLevel,
    AttributionState,
    ConnectionType,
    LabelOrigin,
    VerificationLevel,
)

_STRONG = frozenset({VerificationLevel.LEVEL_3_PRIMARY_SOURCE.value})
_REPUTABLE = frozenset({VerificationLevel.LEVEL_2_REPUTABLE_SECONDARY.value})
_COMMUNITY = frozenset({VerificationLevel.LEVEL_1_COMMUNITY_OR_UNVERIFIED.value})
_SYNTHETIC = frozenset({VerificationLevel.LEVEL_0_SYNTHETIC.value})


@dataclass(frozen=True)
class ConfidenceInput:
    """Inputs required to evaluate the confidence rule table."""

    verification_level: str
    label_origin: str
    independent_source_count: int
    connection_type: ConnectionType
    path_intact: bool
    label_is_stale: bool
    scope_match: bool
    is_demo: bool


@dataclass(frozen=True)
class ConfidenceDecision:
    """Confidence level plus the full factor list that produced it."""

    level: AttributionConfidenceLevel
    factors: dict[str, object]
    rule_applied: str
    is_synthetic: bool

    @property
    def factors_payload(self) -> dict[str, object]:
        """Return the factor dictionary stored with the attribution."""
        payload = dict(self.factors)
        payload["rule_applied"] = self.rule_applied
        return payload


def is_label_stale(last_verified_at: date | None, today: date, stale_after_days: int) -> bool:
    """Return True when a label has not been verified within the freshness window."""
    if last_verified_at is None:
        return True
    return (today - last_verified_at) > timedelta(days=stale_after_days)


def _build_factors(data: ConfidenceInput) -> dict[str, object]:
    """Return every input that contributed to a confidence level."""
    return {
        "verification_level": data.verification_level,
        "label_origin": data.label_origin,
        "label_is_stale": data.label_is_stale,
        "scope_match": data.scope_match,
        "independent_source_count": data.independent_source_count,
        "connection_type": data.connection_type.value,
        "path_intact": data.path_intact,
    }


def _by_source_strength(
    data: ConfidenceInput, factors: dict[str, object], synthetic: bool
) -> ConfidenceDecision | None:
    """Apply the rules keyed on verification level, ignoring staleness rules."""
    level_value = data.verification_level

    if level_value in _STRONG:
        if data.label_is_stale:
            return ConfidenceDecision(
                level=AttributionConfidenceLevel.MEDIUM,
                factors=factors,
                rule_applied="level_3_but_stale",
                is_synthetic=synthetic,
            )
        return ConfidenceDecision(
            level=AttributionConfidenceLevel.HIGH,
            factors=factors,
            rule_applied="level_3_primary_source",
            is_synthetic=synthetic,
        )

    if level_value in _REPUTABLE:
        if data.independent_source_count >= 2:
            return ConfidenceDecision(
                level=AttributionConfidenceLevel.HIGH,
                factors=factors,
                rule_applied="two_or_more_level_2_sources",
                is_synthetic=synthetic,
            )
        return ConfidenceDecision(
            level=AttributionConfidenceLevel.MEDIUM,
            factors=factors,
            rule_applied="single_level_2_source",
            is_synthetic=synthetic,
        )

    if level_value in _COMMUNITY:
        return ConfidenceDecision(
            level=AttributionConfidenceLevel.LOW,
            factors=factors,
            rule_applied="level_1_community_only",
            is_synthetic=synthetic,
        )

    return None


def evaluate_confidence(data: ConfidenceInput) -> ConfidenceDecision:
    """Apply the confidence rule table and return the level with all factors."""
    factors = _build_factors(data)
    synthetic = data.verification_level in _SYNTHETIC

    if synthetic and not data.is_demo:
        return ConfidenceDecision(
            level=AttributionConfidenceLevel.NONE,
            factors=factors,
            rule_applied="synthetic_outside_demo",
            is_synthetic=True,
        )

    if synthetic:
        return ConfidenceDecision(
            level=AttributionConfidenceLevel.LOW,
            factors=factors,
            rule_applied="synthetic_demo_only",
            is_synthetic=True,
        )

    if data.label_origin == LabelOrigin.INFERRED_CLUSTER.value:
        return ConfidenceDecision(
            level=AttributionConfidenceLevel.LOW,
            factors=factors,
            rule_applied="inferred_cluster",
            is_synthetic=False,
        )

    if not data.path_intact:
        return ConfidenceDecision(
            level=AttributionConfidenceLevel.LOW,
            factors=factors,
            rule_applied="path_break",
            is_synthetic=False,
        )

    if data.verification_level in _REPUTABLE and data.label_is_stale:
        return ConfidenceDecision(
            level=AttributionConfidenceLevel.LOW,
            factors=factors,
            rule_applied="single_level_2_stale",
            is_synthetic=False,
        )

    decision = _by_source_strength(data, factors, synthetic=False)
    if decision is not None:
        return decision

    return ConfidenceDecision(
        level=AttributionConfidenceLevel.NONE,
        factors=factors,
        rule_applied="unrecognised_verification_level",
        is_synthetic=False,
    )


def decide_attribution_state(
    confidence: ConfidenceDecision,
    has_label: bool,
    is_synthetic_outside_demo: bool = False,
) -> AttributionState:
    """Map a confidence decision onto the controlled attribution vocabulary.

    A path containing a break yields ``insufficient_data`` because the traced
    movement cannot be followed to a conclusion. A path that ends at an
    address absent from the registry yields
    ``no_match_in_current_references``, which is a valid outcome rather than
    a failure. A label that cannot be used at all, for example one with an
    unrecognised verification level, also yields
    ``no_match_in_current_references`` rather than an association.
    """
    if is_synthetic_outside_demo or not has_label:
        return AttributionState.NO_MATCH_IN_CURRENT_REFERENCES

    if not bool(confidence.factors.get("path_intact", True)):
        return AttributionState.INSUFFICIENT_DATA

    if (
        confidence.level in (AttributionConfidenceLevel.HIGH, AttributionConfidenceLevel.MEDIUM)
        and confidence.factors["label_origin"] == LabelOrigin.OBSERVED_LABEL.value
        and not confidence.is_synthetic
    ):
        return AttributionState.VERIFIED_LABEL_MATCH

    if confidence.level is AttributionConfidenceLevel.LOW:
        return AttributionState.POTENTIAL_ASSOCIATION

    return AttributionState.NO_MATCH_IN_CURRENT_REFERENCES


def best_level(levels: Sequence[AttributionConfidenceLevel]) -> AttributionConfidenceLevel:
    """Return the strongest level present, treating none as the weakest."""
    order = [
        AttributionConfidenceLevel.NONE,
        AttributionConfidenceLevel.LOW,
        AttributionConfidenceLevel.MEDIUM,
        AttributionConfidenceLevel.HIGH,
    ]
    present = [level for level in order if level in levels]
    return present[-1] if present else AttributionConfidenceLevel.NONE

"""Transparent path ranking.

Ranking orders the display order of paths only. It is never shown as a
probability, a score, or a risk figure. Every criterion and the weight it
contributed is returned so the ordering can be explained in the report.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.core.config import Settings
from app.graph.paths import CandidatePath, RankedPath

CRITERION_ANCHORED = "anchored_to_reported_tx"
CRITERION_CONTINUITY = "continuity_ratio"
CRITERION_TIME_PROXIMITY = "time_proximity_hours"
CRITERION_HOP_COUNT = "hop_count"
CRITERION_TERMINAL_LABELLED = "terminal_labelled"


@dataclass(frozen=True)
class RankCriterion:
    """One documented ranking criterion and its configuration weight."""

    key: str
    label: str
    weight: int
    description: str


def default_criteria(settings: Settings) -> list[RankCriterion]:
    """Return the ordered ranking criteria defined by configuration."""
    return [
        RankCriterion(
            key=CRITERION_ANCHORED,
            label="Anchored to the reported transaction",
            weight=settings.RANKING_WEIGHT_ANCHORED_TX,
            description="First edge is the transaction named in the report.",
        ),
        RankCriterion(
            key=CRITERION_CONTINUITY,
            label="Value continuity ratio",
            weight=settings.RANKING_WEIGHT_CONTINUITY,
            description="Share of the originating amount that continues along the path.",
        ),
        RankCriterion(
            key=CRITERION_TIME_PROXIMITY,
            label="Time proximity to the incident",
            weight=settings.RANKING_WEIGHT_TIME_PROXIMITY,
            description="Hours between the incident date and the first transfer.",
        ),
        RankCriterion(
            key=CRITERION_HOP_COUNT,
            label="Fewer hops",
            weight=settings.RANKING_WEIGHT_HOP_COUNT,
            description="Shorter paths are easier to verify manually.",
        ),
        RankCriterion(
            key=CRITERION_TERMINAL_LABELLED,
            label="Terminal address carries a label",
            weight=settings.RANKING_WEIGHT_TERMINAL_LABELLED,
            description="The path ends at an address present in the label registry.",
        ),
    ]


def _time_proximity_hours(path: CandidatePath, incident_date: datetime | None) -> float | None:
    if incident_date is None:
        return None
    delta = abs((path.first_timestamp - incident_date).total_seconds())
    return round(delta / 3600.0, 4)


def rank_paths(
    paths: Sequence[CandidatePath],
    settings: Settings,
    incident_date: datetime | None = None,
) -> list[RankedPath]:
    """Order paths by the configured criteria and attach the full breakdown."""
    criteria = default_criteria(settings)
    ranked: list[RankedPath] = []

    for index, path in enumerate(paths):
        proximity = _time_proximity_hours(path, incident_date)
        values: dict[str, float | bool | int] = {
            CRITERION_ANCHORED: path.anchored_to_reported_tx,
            CRITERION_CONTINUITY: float(path.continuity_ratio),
            CRITERION_TIME_PROXIMITY: proximity if proximity is not None else -1.0,
            CRITERION_HOP_COUNT: path.hop_count,
            CRITERION_TERMINAL_LABELLED: path.terminal_labelled,
        }

        breakdown: list[dict[str, object]] = []
        total = 0
        for criterion in criteria:
            raw = values[criterion.key]
            contribution = _contribution(criterion, raw, path)
            total += contribution
            breakdown.append(
                {
                    "key": criterion.key,
                    "label": criterion.label,
                    "description": criterion.description,
                    "weight": criterion.weight,
                    "observed_value": raw,
                    "contribution": contribution,
                }
            )

        ranked.append(
            RankedPath(
                path_index=index,
                path=path,
                criteria=values,
                ordering_value=total,
                criteria_breakdown=breakdown,
            )
        )

    ranked.sort(
        key=lambda r: (
            -r.ordering_value,
            r.path.hop_count,
            r.path.first_timestamp,
            r.path.start_address,
            r.path.end_address,
        )
    )

    for position, item in enumerate(ranked):
        item.path_index = position

    return ranked


def _contribution(
    criterion: RankCriterion, raw_value: float | bool | int, path: CandidatePath
) -> int:
    """Return the integer contribution of one criterion for one path."""
    if criterion.key == CRITERION_ANCHORED:
        return criterion.weight if bool(raw_value) else 0

    if criterion.key == CRITERION_CONTINUITY:
        return int(Decimal(str(raw_value)) * Decimal(criterion.weight))

    if criterion.key == CRITERION_TIME_PROXIMITY:
        proximity = float(raw_value)
        if proximity < 0:
            return 0
        if proximity <= 24:
            return criterion.weight
        if proximity <= 168:
            return criterion.weight // 2
        return 0

    if criterion.key == CRITERION_HOP_COUNT:
        if path.hop_count <= 1:
            return criterion.weight
        if path.hop_count <= 3:
            return criterion.weight // 2
        return 0

    return criterion.weight if bool(raw_value) else 0


def ordering_note() -> str:
    """Return the disclosure accompanying any displayed ordering."""
    return (
        "Paths are listed in a documented relevance order for review. "
        "This ordering is not a probability, a score, or an indicator of wrongdoing."
    )

"""Provenance-aware attribution of observed fund movement to labelled services."""

from app.attribution.confidence import (
    ConfidenceDecision,
    ConfidenceInput,
    best_level,
    decide_attribution_state,
    evaluate_confidence,
    is_label_stale,
)
from app.attribution.infrastructure import (
    InfrastructureAssessment,
    assess_address,
    exclude_infrastructure_addresses,
)
from app.attribution.matcher import (
    AttributionResult,
    PathAttribution,
    best_confidence,
    classify_connection,
    explain_attribution,
    headline_state_from,
    match_path,
)
from app.attribution.registry import (
    EntityLabelRecord,
    LabelRegistry,
    LabelRegistryError,
    default_registry_dir,
    label_from_dict,
    load_registry,
    registry_from_settings,
)

__all__ = [
    "AttributionResult",
    "ConfidenceDecision",
    "ConfidenceInput",
    "EntityLabelRecord",
    "InfrastructureAssessment",
    "LabelRegistry",
    "LabelRegistryError",
    "PathAttribution",
    "assess_address",
    "best_confidence",
    "best_level",
    "classify_connection",
    "decide_attribution_state",
    "default_registry_dir",
    "evaluate_confidence",
    "exclude_infrastructure_addresses",
    "explain_attribution",
    "headline_state_from",
    "is_label_stale",
    "label_from_dict",
    "load_registry",
    "match_path",
    "registry_from_settings",
]

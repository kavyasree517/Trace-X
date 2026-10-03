"""Attribution schemas conforming to P7 provenance requirements."""

from datetime import date

from pydantic import BaseModel, ConfigDict

from app.core.enums import (
    AttributionConfidenceLevel,
    AttributionState,
    ConnectionType,
    EvidenceTag,
    LabelOrigin,
    SourceType,
    VerificationLevel,
)


class LabelProvenance(BaseModel):
    """P7 Complete label metadata model."""

    model_config = ConfigDict(extra="forbid")

    entity_name: str
    entity_type: str
    chain: str
    address: str
    cluster_id: str | None = None
    label_origin: LabelOrigin
    source_name: str
    source_type: SourceType
    source_reference: str
    verification_level: VerificationLevel
    observed_at: date | None = None
    last_verified_at: date | None = None
    scope_notes: str | None = None
    is_shared_infrastructure: bool = False
    is_active: bool = True
    notes: str | None = None


class ConfidenceFactors(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verification_level: VerificationLevel
    label_origin: LabelOrigin
    label_is_stale: bool
    scope_match: bool
    independent_source_count: int
    connection_type: ConnectionType
    path_intact: bool


class AttributionItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path_id: int | None = None
    label: LabelProvenance
    connection_type: ConnectionType
    attribution_state: AttributionState
    confidence_level: AttributionConfidenceLevel
    confidence_factors: ConfidenceFactors
    label_is_stale: bool
    shared_infrastructure_flag: bool
    explanation: str
    evidence_tag: EvidenceTag = EvidenceTag.DERIVED


class AttributionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    attributions: list[AttributionItem]
    total: int

"""Cross-report corroboration schemas."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import CorroborationStrength, EvidenceTag


class RelatedCaseItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_reference: str
    strength: CorroborationStrength
    evidence_tag: EvidenceTag = EvidenceTag.DERIVED
    shared_addresses: list[str] = Field(default_factory=list)
    shared_transactions: list[str] = Field(default_factory=list)
    shared_path_segments: list[str] = Field(default_factory=list)
    shared_infrastructure_flag: bool
    temporal_notes: str | None = None
    caution_notice: str


class CorroborationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    related_cases: list[RelatedCaseItem]
    total_matches: int
    mandatory_caution: str

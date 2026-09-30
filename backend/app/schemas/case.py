"""Schemas for case creation and summary evaluation."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import CaseStatus, IncidentDatePrecision
from app.schemas.common import LimitationsBlock


class CaseParameters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_hops: int = Field(default=4, ge=1, le=6)
    time_window_days: int = Field(default=30, ge=1, le=180)
    max_nodes: int = Field(default=500, ge=10, le=2000)
    max_edges: int = Field(default=2000, ge=10, le=8000)


class CaseCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    address: str = Field(..., min_length=1, max_length=128)
    chain: str = Field(default="ethereum")
    tx_hash: str | None = None
    incident_date: datetime | None = None
    incident_date_precision: IncidentDatePrecision = IncidentDatePrecision.UNKNOWN
    reported_amount: Decimal | None = Field(default=None, ge=Decimal("0.0"))
    reported_asset: str | None = None
    parameters: CaseParameters = Field(default_factory=CaseParameters)
    narrative: str | None = Field(default=None, max_length=4000)
    consent_for_narrative_storage: bool = False

    @field_validator("consent_for_narrative_storage")
    @classmethod
    def validate_narrative_consent(cls, v: bool, info: Any) -> bool:
        narrative = info.data.get("narrative")
        if narrative and not v:
            raise ValueError("consent_for_narrative_storage is required when narrative is provided")
        return v


class CaseCreateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_reference: str
    access_token: str
    status: CaseStatus
    created_at: str


class ConfidencePanel(BaseModel):
    """P2 Four independent evaluation entries without probability score."""

    model_config = ConfigDict(extra="forbid")

    path_evidence: str
    attribution_confidence: str
    behavioral_signals: str
    corroboration_strength: str


class ProgressStages(BaseModel):
    model_config = ConfigDict(extra="forbid")

    retrieval: str  # pending, running, completed, failed
    graph: str
    attribution: str
    behavior: str
    corroboration: str
    assembly: str


class CaseSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_reference: str
    chain: str
    reported_address: str
    status: CaseStatus
    headline_state: str
    summary_text: str
    stages: ProgressStages
    confidence_panel: ConfidencePanel
    limitations: LimitationsBlock
    demo_notice: str | None = None
    created_at: str
    completed_at: str | None = None

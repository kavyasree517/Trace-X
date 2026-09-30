"""Case evidence package and forensic audit schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.attribution import AttributionItem
from app.schemas.behavior import SignalItem
from app.schemas.case import CaseParameters, ConfidencePanel
from app.schemas.common import LimitationsBlock
from app.schemas.corroboration import RelatedCaseItem
from app.schemas.path import PathItem


class CaseEvidencePackage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_reference: str
    chain: str
    reported_address: str
    reported_tx_hash: str | None
    incident_date: str | None
    parameters: CaseParameters
    sources: list[str]
    retrieval_times: list[str]
    snapshot_id: str
    ranked_paths: list[PathItem]
    attributions: list[AttributionItem]
    signals: list[SignalItem]
    related_cases: list[RelatedCaseItem]
    limitations: LimitationsBlock
    confidence_panel: ConfidencePanel
    summary_text: str
    code_version: str
    model_version: str
    label_registry_snapshot_hash: str


class AuditEventItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str
    case_reference: str | None
    event_type: str
    occurred_at: datetime
    actor: str
    payload_hash: str
    prev_hash: str | None
    is_valid_chain: bool = True


class AuditTrailResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    events: list[AuditEventItem]
    chain_intact: bool
    total_events: int

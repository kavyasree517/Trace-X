"""Path extraction schemas and relevance criteria."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import EvidenceTag, PathBreakReason, TracingMethod
from app.schemas.transaction import TransactionItem


class PathEdge(TransactionItem):
    pass


class RelevanceCriteria(BaseModel):
    model_config = ConfigDict(extra="forbid")

    anchored_to_reported_tx: bool
    continuity_ratio: float
    time_proximity_hours: float
    hop_count: int
    terminal_labelled: bool


class PathItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path_index: int
    hop_count: int
    start_address: str
    end_address: str
    first_timestamp: datetime
    last_timestamp: datetime
    elapsed_seconds: int
    traced_value_amount: Decimal
    traced_value_asset: str
    tracing_method: TracingMethod
    value_continuity_ratio: float
    relevance_criteria: RelevanceCriteria
    has_break: bool
    break_reason: PathBreakReason | None = None
    edges: list[PathEdge] = Field(default_factory=list)
    evidence_tag: EvidenceTag = EvidenceTag.DERIVED


class PathResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paths: list[PathItem]
    total_found: int
    omitted_count: int

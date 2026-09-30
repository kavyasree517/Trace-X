"""Common schemas and response wrappers."""

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import EvidenceTag


class EvidenceItem(BaseModel):
    """Base schema for data points carrying evidence tag and audit metadata."""

    model_config = ConfigDict(extra="forbid")

    evidence_tag: EvidenceTag = Field(
        ...,
        description="P1 evidence provenance tag: observed, derived, or inferred.",
    )


class PaginationMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int
    offset: int
    limit: int


class LimitationsBlock(BaseModel):
    """P10 explicit limitations block required on all investigative responses."""

    model_config = ConfigDict(extra="forbid")

    standing_statement: str
    analysis_timestamp: str
    is_demo: bool
    data_snapshot_id: str | None = None
    notes: list[str] = Field(default_factory=list)

"""Behavioral signals schemas."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import EvidenceTag, SignalLevel


class SignalItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    signal_key: str
    level: SignalLevel
    evidence_tag: EvidenceTag = EvidenceTag.INFERRED
    feature_values: dict[str, Any] = Field(default_factory=dict)
    explanation: str
    limitation_note: str = Field(default="This pattern can also result from legitimate activity.")


class SignalResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    signals: list[SignalItem]
    total: int

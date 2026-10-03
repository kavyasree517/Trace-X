"""Graph topology visualization schemas."""

from pydantic import BaseModel, ConfigDict

from app.core.enums import EvidenceTag


class GraphNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    is_contract: bool = False
    is_hub: bool = False
    is_terminal: bool = False
    entity_name: str | None = None
    entity_type: str | None = None


class GraphEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    source: str
    target: str
    tx_hash: str
    asset_symbol: str
    amount_decimal: str
    timestamp: str


class GraphTopologyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nodes: list[GraphNode]
    edges: list[GraphEdge]
    total_nodes: int
    total_edges: int
    evidence_tag: EvidenceTag = EvidenceTag.DERIVED

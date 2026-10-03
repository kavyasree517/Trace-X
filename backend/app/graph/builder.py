"""Graph construction from normalized transfers.

Nodes are canonical addresses. Edges are keyed by ``(tx_hash, log_index)`` so
that two transfers in the same transaction remain distinguishable. A
MultiDiGraph is used because a transaction can contain several transfers
between the same pair of addresses.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime

import networkx as nx

from app.adapters.base import NormalizedTransfer
from app.core.security import canonicalize_address

NEG_INF = float("-inf")
POS_INF = float("inf")

NODE_FIRST_SEEN = "first_seen"
NODE_LAST_SEEN = "last_seen"
NODE_IN_DEGREE = "in_degree"
NODE_OUT_DEGREE = "out_degree"
NODE_IS_CONTRACT = "is_contract"
NODE_LABEL_IDS = "label_ids"
NODE_ENTITY_TYPES = "entity_types"
EDGE_TRANSFER = "transfer"
EDGE_IS_SUCCESS = "is_success"

DedupeKey = tuple[str, str, int, str, str, str, str]


class TraceGraph(nx.MultiDiGraph):
    """MultiDiGraph keyed by canonical address strings."""


@dataclass
class GraphBuildResult:
    """Graph plus the provenance of the transfers that produced it."""

    graph: TraceGraph
    transfers: list[NormalizedTransfer] = field(default_factory=list)
    skipped_addresses: list[str] = field(default_factory=list)
    self_transfers: list[str] = field(default_factory=list)
    contract_creations: list[str] = field(default_factory=list)
    failed_transfers: list[str] = field(default_factory=list)

    @property
    def node_count(self) -> int:
        return int(self.graph.number_of_nodes())

    @property
    def edge_count(self) -> int:
        return int(self.graph.number_of_edges())


def _to_canonical(address: str) -> str | None:
    try:
        return canonicalize_address(address)
    except ValueError:
        return None


def _new_node_attrs(address: str) -> dict[str, object]:
    return {
        NODE_FIRST_SEEN: POS_INF,
        NODE_LAST_SEEN: NEG_INF,
        NODE_IN_DEGREE: 0,
        NODE_OUT_DEGREE: 0,
        NODE_IS_CONTRACT: False,
        NODE_LABEL_IDS: set(),
        NODE_ENTITY_TYPES: set(),
        "address": address,
    }


def _update_time_window(graph: TraceGraph, address: str, timestamp: datetime) -> None:
    attrs = graph.nodes[address]
    current_first = float(attrs.get(NODE_FIRST_SEEN, POS_INF))
    current_last = float(attrs.get(NODE_LAST_SEEN, NEG_INF))
    epoch = timestamp.timestamp()
    attrs[NODE_FIRST_SEEN] = min(current_first, epoch)
    attrs[NODE_LAST_SEEN] = max(current_last, epoch)


def _ensure_node(graph: TraceGraph, address: str) -> str:
    if address not in graph:
        graph.add_node(address, **_new_node_attrs(address))
    return address


def add_transfer(graph: TraceGraph, transfer: NormalizedTransfer) -> bool:
    """Insert one transfer into the graph. Returns False if unusable."""
    sender = _to_canonical(transfer.sender)
    receiver = _to_canonical(transfer.receiver)
    if sender is None or receiver is None:
        return False

    _ensure_node(graph, sender)
    _ensure_node(graph, receiver)

    if transfer.is_contract_creation:
        graph.nodes[receiver][NODE_IS_CONTRACT] = True

    _update_time_window(graph, sender, transfer.block_timestamp)
    _update_time_window(graph, receiver, transfer.block_timestamp)

    graph.add_edge(
        sender,
        receiver,
        key=transfer.log_index,
        **{
            EDGE_TRANSFER: transfer,
            EDGE_IS_SUCCESS: transfer.is_success,
        },
    )
    graph.nodes[sender][NODE_OUT_DEGREE] = int(graph.nodes[sender][NODE_OUT_DEGREE]) + 1
    graph.nodes[receiver][NODE_IN_DEGREE] = int(graph.nodes[receiver][NODE_IN_DEGREE]) + 1
    return True


def build_graph(transfers: Iterable[NormalizedTransfer]) -> GraphBuildResult:
    """Build a TraceGraph from normalized transfers, deduplicating duplicates."""
    graph = TraceGraph()
    result = GraphBuildResult(graph=graph)
    seen: set[DedupeKey] = set()

    for transfer in transfers:
        dedupe_key = (
            transfer.chain,
            transfer.tx_hash.lower(),
            transfer.log_index,
            transfer.transfer_kind.value,
            transfer.sender,
            transfer.receiver,
            transfer.asset_id,
        )
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        if not _to_canonical(transfer.sender) or not _to_canonical(transfer.receiver):
            result.skipped_addresses.extend([transfer.sender, transfer.receiver])
            continue

        result.transfers.append(transfer)

        if transfer.is_contract_creation:
            result.contract_creations.append(transfer.tx_hash)
        if transfer.is_self_transfer:
            result.self_transfers.append(transfer.tx_hash)
        if not transfer.is_success:
            result.failed_transfers.append(transfer.tx_hash)

        add_transfer(graph, transfer)

    return result


def iter_edge_transfers(
    graph: TraceGraph, source: str, target: str, include_failed: bool = False
) -> list[NormalizedTransfer]:
    """Return the transfers on every edge between two addresses.

    MultiDiGraph stores edge attributes as ``{edge_key: attrs}``, so this
    helper keeps the traversal shape in one place. Results are deduplicated by
    ``(tx_hash, log_index)`` and ordered by time so that walks are
    deterministic.
    """
    bundles = graph.get_edge_data(source, target) or {}
    seen: set[tuple[str, int]] = set()
    collected: list[NormalizedTransfer] = []

    for attrs in bundles.values():
        if not include_failed and not attrs.get(EDGE_IS_SUCCESS, True):
            continue
        transfer: NormalizedTransfer = attrs[EDGE_TRANSFER]
        key = (transfer.tx_hash, transfer.log_index)
        if key in seen:
            continue
        seen.add(key)
        collected.append(transfer)

    return sorted(collected, key=lambda t: (t.block_timestamp, t.log_index))


def all_successful_transfers(graph: TraceGraph) -> list[NormalizedTransfer]:
    """Return every successful transfer in the graph, deduplicated and ordered.

    Value tracing needs the full onward pool at each hop so that a split
    can be attributed proportionally rather than assumed to be a single flow.
    """
    seen: set[tuple[str, int]] = set()
    collected: list[NormalizedTransfer] = []

    for _, _, attrs in graph.edges(data=True):
        if not attrs.get(EDGE_IS_SUCCESS, True):
            continue
        transfer: NormalizedTransfer = attrs[EDGE_TRANSFER]
        key = (transfer.tx_hash, transfer.log_index)
        if key in seen:
            continue
        seen.add(key)
        collected.append(transfer)

    return sorted(
        collected,
        key=lambda t: (t.block_timestamp, t.block_number, t.tx_hash, t.log_index),
    )


def node_degree(graph: TraceGraph, address: str) -> int:
    """Return the combined in and out degree of an address."""
    if address not in graph:
        return 0
    return int(graph.in_degree(address)) + int(graph.out_degree(address))

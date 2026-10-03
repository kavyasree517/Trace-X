"""Breadth-first graph expansion under explicit budgets.

Expansion starts from a reported address, or from the addresses touched by the
reported transaction when one is supplied. Budgets on hops, nodes, edges and
wall-clock time are enforced. Hubs and labelled service addresses are never
expanded: they are retained as terminal nodes so that attribution can apply
there.
"""

from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from app.adapters.base import NormalizedTransfer
from app.core.config import Settings
from app.core.enums import EntityType, PathBreakReason
from app.graph.builder import (
    EDGE_TRANSFER,
    NODE_ENTITY_TYPES,
    TraceGraph,
    iter_edge_transfers,
    node_degree,
)

# Entity types that terminate expansion instead of being expanded through.
TERMINAL_ENTITY_TYPES = frozenset(
    {
        EntityType.EXCHANGE.value,
        EntityType.EXCHANGE_HOT_WALLET.value,
        EntityType.EXCHANGE_DEPOSIT_ADDRESS.value,
        EntityType.MIXER.value,
        EntityType.BRIDGE.value,
        EntityType.DECENTRALIZED_EXCHANGE.value,
        EntityType.PAYMENT_SERVICE.value,
    }
)


@dataclass(frozen=True)
class ExpansionLimits:
    """Hard budgets applied to a single expansion run."""

    max_hops: int
    max_nodes: int
    max_edges: int
    time_window_days: int
    deadline_seconds: int
    high_degree_threshold: int
    allow_incoming_expansion: bool = False

    @classmethod
    def from_settings(cls, settings: Settings, **overrides: int | bool | None) -> ExpansionLimits:
        """Build limits from application settings with optional overrides."""
        base: dict[str, int | bool] = {
            "max_hops": settings.GRAPH_MAX_HOPS_DEFAULT,
            "max_nodes": settings.GRAPH_MAX_NODES_DEFAULT,
            "max_edges": settings.GRAPH_MAX_EDGES_DEFAULT,
            "time_window_days": settings.GRAPH_TIME_WINDOW_DAYS_DEFAULT,
            "deadline_seconds": settings.GRAPH_DEADLINE_SECONDS,
            "high_degree_threshold": settings.GRAPH_HIGH_DEGREE_THRESHOLD,
            "allow_incoming_expansion": settings.GRAPH_INCOMING_EXPANSION_DEFAULT,
        }
        base.update({k: v for k, v in overrides.items() if v is not None})
        return cls(**base)  # type: ignore[arg-type]


@dataclass
class ExpansionOutcome:
    """Result of an expansion run including any budget interruptions."""

    graph: TraceGraph
    seed_addresses: list[str] = field(default_factory=list)
    anchor_time: datetime | None = None
    retained_transfers: list[NormalizedTransfer] = field(default_factory=list)
    terminal_addresses: set[str] = field(default_factory=set)
    expanded_addresses: set[str] = field(default_factory=set)
    truncated: bool = False
    truncation_reason: PathBreakReason | None = None
    truncation_detail: str | None = None
    max_hop_reached: int = 0
    duration_ms: int = 0

    @property
    def is_partial(self) -> bool:
        return self.truncated


@dataclass(frozen=True)
class _FrontierItem:
    address: str
    hop: int
    window_start: datetime
    window_end: datetime


def is_terminal_address(graph: TraceGraph, address: str, limits: ExpansionLimits) -> bool:
    """Return True when an address must not be expanded further."""
    if address not in graph:
        return False

    entity_types = graph.nodes[address].get(NODE_ENTITY_TYPES) or set()
    if entity_types & TERMINAL_ENTITY_TYPES:
        return True

    return node_degree(graph, address) > limits.high_degree_threshold


def _within_window(timestamp: datetime, start: datetime, end: datetime) -> bool:
    return start <= timestamp <= end


def _edge_transfers(graph: TraceGraph, source: str, target: str) -> list[NormalizedTransfer]:
    """Return deduplicated successful transfers between two adjacent nodes."""
    return iter_edge_transfers(graph, source, target)


def _neighbours_within_window(
    graph: TraceGraph,
    item: _FrontierItem,
    limits: ExpansionLimits,
    include_incoming: bool,
) -> list[tuple[str, list[NormalizedTransfer]]]:
    """Return adjacent addresses with in-window transfers, sorted deterministically."""
    neighbours: list[tuple[str, list[NormalizedTransfer]]] = []

    for target in sorted(graph.successors(item.address)):
        transfers = [
            t
            for t in _edge_transfers(graph, item.address, target)
            if _within_window(t.block_timestamp, item.window_start, item.window_end)
        ]
        if transfers:
            neighbours.append((target, transfers))

    if include_incoming:
        for source in sorted(graph.predecessors(item.address)):
            if is_terminal_address(graph, source, limits):
                continue
            transfers = [
                t
                for t in _edge_transfers(graph, source, item.address)
                if _within_window(t.block_timestamp, item.window_start, item.window_end)
            ]
            if transfers:
                neighbours.append((source, transfers))

    return neighbours


def _next_frontier(
    item: _FrontierItem, transfers: Sequence[NormalizedTransfer], time_window_days: int
) -> _FrontierItem:
    """Center the next hop window on the arrival time of traced value."""
    earliest = min(t.block_timestamp for t in transfers)
    delta = timedelta(days=time_window_days)
    return _FrontierItem(
        address=item.address,
        hop=item.hop + 1,
        window_start=earliest - delta,
        window_end=earliest + delta,
    )


def default_anchor(graph: TraceGraph, seed_addresses: Sequence[str]) -> datetime:
    """Return the newest successful transfer time across seeds.

    Used when the report carries no incident date. Falls back to the newest
    transfer anywhere in the graph, then to the Unix epoch in UTC.
    """
    timestamps: list[datetime] = []
    for address in seed_addresses:
        if address in graph:
            timestamps.extend(
                t.block_timestamp
                for _, _, attrs in graph.out_edges(address, data=True)
                for t in [attrs[EDGE_TRANSFER]]
            )
    if timestamps:
        return max(timestamps)

    all_timestamps: list[datetime] = []
    for _, _, attrs in graph.edges(data=True):
        transfer: NormalizedTransfer = attrs[EDGE_TRANSFER]
        all_timestamps.append(transfer.block_timestamp)
    if all_timestamps:
        return max(all_timestamps)

    return datetime.fromtimestamp(0, tz=UTC)


class _ExpansionState:
    """Mutable bookkeeping for one expansion run."""

    def __init__(self, limits: ExpansionLimits) -> None:
        self.limits = limits
        self.visited: set[tuple[str, int]] = set()
        self.retained: dict[tuple[str, int], NormalizedTransfer] = {}
        self.truncated = False
        self.truncation_reason: PathBreakReason | None = None
        self.truncation_detail: str | None = None

    def mark_truncated(self, detail: str) -> None:
        self.truncated = True
        self.truncation_reason = PathBreakReason.EXPANSION_LIMIT_REACHED
        self.truncation_detail = detail

    def over_edge_budget(self) -> bool:
        return len(self.retained) >= self.limits.max_edges

    def over_node_budget(self, address: str, hop: int) -> bool:
        return len(self.visited) >= self.limits.max_nodes and (address, hop) not in self.visited

    def transfers_sorted(self) -> list[NormalizedTransfer]:
        return sorted(
            self.retained.values(),
            key=lambda t: (t.block_timestamp, t.block_number, t.tx_hash, t.log_index),
        )


def _process_neighbours(
    graph: TraceGraph,
    item: _FrontierItem,
    neighbours: Sequence[tuple[str, list[NormalizedTransfer]]],
    state: _ExpansionState,
    outcome: ExpansionOutcome,
    queue: deque[_FrontierItem],
) -> None:
    """Retain transfers for one frontier item and queue its non-terminal neighbours."""
    for neighbour, transfers in neighbours:
        for transfer in transfers:
            state.retained[(transfer.tx_hash, transfer.log_index)] = transfer

        if state.over_edge_budget():
            state.mark_truncated(
                f"Expansion stopped after {state.limits.max_edges} retained transfers."
            )
            return

        if state.over_node_budget(neighbour, item.hop + 1):
            state.mark_truncated(f"Expansion stopped after {state.limits.max_nodes} addresses.")
            return

        if is_terminal_address(graph, neighbour, state.limits):
            outcome.terminal_addresses.add(neighbour)
            continue

        outcome.expanded_addresses.add(neighbour)
        queue.append(_next_frontier(item, transfers, state.limits.time_window_days))


async def expand_graph(
    graph: TraceGraph,
    seed_addresses: Sequence[str],
    limits: ExpansionLimits,
    anchor_time: datetime | None = None,
) -> ExpansionOutcome:
    """Expand the graph outward from the seeds under the supplied budgets."""
    loop = asyncio.get_running_loop()
    started = loop.time()
    deadline = started + limits.deadline_seconds

    outcome = ExpansionOutcome(graph=graph, seed_addresses=list(seed_addresses))
    seeds = [s for s in seed_addresses if s in graph]
    if not seeds:
        return outcome

    anchor = anchor_time if anchor_time is not None else default_anchor(graph, seeds)
    outcome.anchor_time = anchor

    window_delta = timedelta(days=limits.time_window_days)
    queue: deque[_FrontierItem] = deque(
        _FrontierItem(
            address=seed,
            hop=0,
            window_start=anchor - window_delta,
            window_end=anchor + window_delta,
        )
        for seed in seeds
    )
    outcome.terminal_addresses.update(
        seed for seed in seeds if is_terminal_address(graph, seed, limits)
    )

    state = _ExpansionState(limits)

    while queue and not state.truncated:
        if loop.time() > deadline:
            state.mark_truncated(
                f"Expansion stopped after {limits.deadline_seconds} seconds of wall clock time."
            )
            break

        item = queue.popleft()
        if item.hop >= limits.max_hops or (item.address, item.hop) in state.visited:
            continue

        state.visited.add((item.address, item.hop))
        outcome.max_hop_reached = max(outcome.max_hop_reached, item.hop)

        include_incoming = limits.allow_incoming_expansion and item.hop == 0
        neighbours = _neighbours_within_window(graph, item, limits, include_incoming)
        _process_neighbours(graph, item, neighbours, state, outcome, queue)

    outcome.retained_transfers = state.transfers_sorted()
    outcome.truncated = state.truncated
    outcome.truncation_reason = state.truncation_reason
    outcome.truncation_detail = state.truncation_detail
    outcome.duration_ms = int((loop.time() - started) * 1000)
    return outcome

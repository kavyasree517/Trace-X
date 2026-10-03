"""Time-respecting path enumeration.

Only simple paths whose timestamps never decrease are returned. Each edge
retains the full P6 field set so that a path can be independently verified from
the report alone.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from app.adapters.base import NormalizedTransfer
from app.core.enums import PathBreakReason, TracingMethod
from app.graph.breaks import BreakResult, detect_node_break
from app.graph.builder import (
    NODE_ENTITY_TYPES,
    TraceGraph,
    all_successful_transfers,
    iter_edge_transfers,
)
from app.graph.value_tracing import TraceResult, trace_value


@dataclass(frozen=True)
class PathEdgeRecord:
    """A single edge of a path carrying the complete P6 field set."""

    hop_index: int
    tx_hash: str
    log_index: int
    block_number: int
    block_timestamp: datetime
    sender: str
    receiver: str
    asset_id: str
    asset_symbol: str
    asset_decimals: int | None
    amount_raw: int
    amount_decimal: Decimal | None
    transfer_kind: str
    status: str
    data_source: str

    def to_dict(self) -> dict[str, object]:
        """Return the P6 payload for persistence and rendering."""
        return {
            "hop_index": self.hop_index,
            "tx_hash": self.tx_hash,
            "log_index": self.log_index,
            "block_number": self.block_number,
            "block_timestamp": self.block_timestamp.isoformat(),
            "sender": self.sender,
            "receiver": self.receiver,
            "asset_id": self.asset_id,
            "asset_symbol": self.asset_symbol,
            "asset_decimals": self.asset_decimals,
            "amount_raw": self.amount_raw,
            "amount_decimal": str(self.amount_decimal) if self.amount_decimal is not None else None,
            "transfer_kind": self.transfer_kind,
            "status": self.status,
            "data_source": self.data_source,
        }

    @classmethod
    def from_transfer(cls, hop_index: int, transfer: NormalizedTransfer) -> PathEdgeRecord:
        return cls(
            hop_index=hop_index,
            tx_hash=transfer.tx_hash,
            log_index=transfer.log_index,
            block_number=transfer.block_number,
            block_timestamp=transfer.block_timestamp,
            sender=transfer.sender,
            receiver=transfer.receiver,
            asset_id=transfer.asset_id,
            asset_symbol=transfer.asset_symbol,
            asset_decimals=transfer.asset_decimals,
            amount_raw=transfer.amount_raw,
            amount_decimal=transfer.amount_decimal,
            transfer_kind=transfer.transfer_kind.value,
            status=transfer.status,
            data_source=transfer.source,
        )


@dataclass
class CandidatePath:
    """A path through the graph before ranking and capping are applied."""

    addresses: list[str]
    transfers: list[NormalizedTransfer]
    edges: list[PathEdgeRecord]
    trace: TraceResult
    break_result: BreakResult
    anchored_to_reported_tx: bool = False
    terminal_labelled: bool = False

    @property
    def hop_count(self) -> int:
        return len(self.transfers)

    @property
    def start_address(self) -> str:
        return self.addresses[0]

    @property
    def end_address(self) -> str:
        return self.addresses[-1]

    @property
    def first_timestamp(self) -> datetime:
        return self.transfers[0].block_timestamp

    @property
    def last_timestamp(self) -> datetime:
        return self.transfers[-1].block_timestamp

    @property
    def elapsed_seconds(self) -> int:
        return int((self.last_timestamp - self.first_timestamp).total_seconds())

    @property
    def has_break(self) -> bool:
        return self.break_result.has_break or self.trace.has_break

    @property
    def break_reason(self) -> PathBreakReason | None:
        if self.break_result.has_break and self.break_result.reason is not None:
            return self.break_result.reason
        return self.trace.break_reason

    @property
    def asset_id(self) -> str:
        return self.trace.asset_id

    @property
    def traced_value(self) -> Decimal:
        return self.trace.traced_amount

    @property
    def continuity_ratio(self) -> Decimal:
        return self.trace.continuity_ratio


@dataclass
class RankedPath:
    """A candidate path with its relevance criteria and display ordering."""

    path_index: int
    path: CandidatePath
    criteria: dict[str, float | bool | int]
    ordering_value: int
    criteria_breakdown: list[dict[str, object]] = field(default_factory=list)


@dataclass
class PathEnumeration:
    """All enumerated paths plus counts of what was pruned or omitted."""

    paths: list[CandidatePath] = field(default_factory=list)
    omitted_count: int = 0
    pruned_low_continuity: int = 0
    broken_paths: int = 0

    @property
    def total_found(self) -> int:
        return len(self.paths)


def _success_transfers(graph: TraceGraph, source: str, target: str) -> list[NormalizedTransfer]:
    """Return sorted, deduplicated successful transfers between adjacent nodes."""
    return iter_edge_transfers(graph, source, target)


def _walk(
    graph: TraceGraph,
    current: str,
    visited: list[str],
    transfers: list[NormalizedTransfer],
    max_hops: int,
    min_timestamp: datetime | None,
    traced_addresses: Sequence[str],
    pool: Sequence[NormalizedTransfer],
) -> list[CandidatePath]:
    """Depth-first walk collecting time-respecting simple paths."""
    results: list[CandidatePath] = []

    if transfers:
        results.append(
            _build_candidate(graph, list(visited), list(transfers), traced_addresses, pool)
        )

    if len(transfers) >= max_hops:
        return results

    for neighbour in sorted(graph.successors(current)):
        if neighbour in visited:
            continue

        for transfer in _success_transfers(graph, current, neighbour):
            if min_timestamp is not None and transfer.block_timestamp < min_timestamp:
                continue
            results.extend(
                _walk(
                    graph,
                    neighbour,
                    [*visited, neighbour],
                    [*transfers, transfer],
                    max_hops,
                    transfer.block_timestamp,
                    traced_addresses,
                    pool,
                )
            )

    return results


def _build_candidate(
    graph: TraceGraph,
    addresses: list[str],
    transfers: list[NormalizedTransfer],
    traced_addresses: Sequence[str],
    pool: Sequence[NormalizedTransfer],
) -> CandidatePath:
    """Assemble a candidate path with traced value and break evaluation."""
    trace = trace_value(transfers, TracingMethod.PROPORTIONAL, onward_pool=pool)

    terminal_types = graph.nodes[addresses[-1]].get(NODE_ENTITY_TYPES) or set()
    node_break = detect_node_break(addresses[-1], set(terminal_types))

    anchors = {a.lower() for a in traced_addresses}
    anchored = any(a.lower() in anchors for a in (transfers[0].sender, transfers[0].receiver))

    return CandidatePath(
        addresses=addresses,
        transfers=transfers,
        edges=[PathEdgeRecord.from_transfer(i, t) for i, t in enumerate(transfers)],
        trace=trace,
        break_result=node_break,
        anchored_to_reported_tx=anchored,
        terminal_labelled=bool(terminal_types),
    )


def enumerate_paths(
    graph: TraceGraph,
    seed_addresses: Sequence[str],
    max_hops: int,
    min_continuity_ratio: float,
    max_paths: int,
    tracing_method: TracingMethod = TracingMethod.PROPORTIONAL,
    anchor_time: datetime | None = None,
) -> PathEnumeration:
    """Enumerate, prune and cap candidate paths starting from the seeds."""
    enumeration = PathEnumeration()
    seeds = [s for s in seed_addresses if s in graph]
    if not seeds or max_hops < 1:
        return enumeration

    pool = all_successful_transfers(graph)

    candidates: list[CandidatePath] = []
    for seed in sorted(set(seeds)):
        candidates.extend(
            _walk(
                graph,
                seed,
                [seed],
                [],
                max_hops,
                anchor_time,
                seed_addresses,
                pool,
            )
        )

    for candidate in candidates:
        if candidate.trace.method is not tracing_method:
            candidate.trace = trace_value(candidate.transfers, tracing_method, onward_pool=pool)

    threshold = Decimal(str(min_continuity_ratio))
    for candidate in candidates:
        if candidate.continuity_ratio < threshold:
            enumeration.pruned_low_continuity += 1
            continue
        if candidate.has_break:
            enumeration.broken_paths += 1
        enumeration.paths.append(candidate)

    enumeration.paths.sort(
        key=lambda p: (
            -float(p.continuity_ratio),
            p.hop_count,
            p.first_timestamp,
            p.start_address,
            p.end_address,
        )
    )

    if len(enumeration.paths) > max_paths:
        enumeration.omitted_count = len(enumeration.paths) - max_paths
        enumeration.paths = enumeration.paths[:max_paths]

    return enumeration

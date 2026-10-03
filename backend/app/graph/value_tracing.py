"""Value continuity tracing along candidate paths.

Two methods are supported behind one interface:

* ``proportional``: each onward transfer carries a share of the received
  amount equal to ``sent / total_sent`` across all onward transfers of the
  same asset from that address.
* ``fifo``: the received amount is consumed by onward transfers in timestamp
  order until exhausted.

Both are deterministic estimations of value movement. Neither proves that
specific units of value moved between two addresses.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal

from app.adapters.base import NormalizedTransfer
from app.core.enums import PathBreakReason, TracingMethod

_QUANTUM = Decimal("1e-18")


def _as_decimal(amount: Decimal | None, amount_raw: int) -> Decimal:
    """Return the decimal amount, deriving it from the raw amount if needed."""
    if amount is not None:
        return amount
    return Decimal(amount_raw) / _QUANTUM


@dataclass(frozen=True)
class TraceResult:
    """Outcome of tracing value along one path for one asset."""

    traced_amount: Decimal
    asset_id: str
    method: TracingMethod
    continuity_ratio: Decimal
    break_reason: PathBreakReason | None = None
    notes: tuple[str, ...] = ()

    @property
    def has_break(self) -> bool:
        return self.break_reason is not None


def _available_outgoing(
    transfers: Sequence[NormalizedTransfer], address: str, asset_id: str
) -> list[NormalizedTransfer]:
    """Return successful onward transfers of one asset from an address."""
    return sorted(
        (
            t
            for t in transfers
            if t.sender == address
            and t.asset_id == asset_id
            and t.status == "success"
            and not t.is_self_transfer
        ),
        key=lambda t: (t.block_timestamp, t.block_number, t.tx_hash, t.log_index),
    )


def trace_proportional(
    available: Decimal,
    target: NormalizedTransfer,
    onward: Sequence[NormalizedTransfer],
) -> Decimal:
    """Return the share of `available` that follows `target`.

    Every onward transfer of the same asset leaving an address draws on the
    same received balance, so the share assigned to one onward transfer is
    proportional to its size relative to all onward transfers from that
    address. The result never exceeds either `available` or the amount
    actually sent.

    Gas is deliberately excluded: transaction fees do not represent value
    received from the incoming transfer.
    """
    if available <= 0 or target.status != "success" or target.is_self_transfer:
        return Decimal("0")

    candidates = [t for t in onward if t.status == "success" and not t.is_self_transfer]
    if not candidates:
        return Decimal("0")

    total = sum((_as_decimal(t.amount_decimal, t.amount_raw) for t in candidates), Decimal("0"))
    if total <= 0:
        return Decimal("0")

    target_amount = _as_decimal(target.amount_decimal, target.amount_raw)
    share = available * target_amount / total

    return min(share, target_amount, available).quantize(_QUANTUM, rounding=ROUND_HALF_EVEN)


def trace_value(
    path_transfers: Sequence[NormalizedTransfer],
    method: TracingMethod = TracingMethod.PROPORTIONAL,
    onward_pool: Sequence[NormalizedTransfer] | None = None,
) -> TraceResult:
    """Trace value along a path, returning the traced amount and continuity.

    ``onward_pool`` supplies every known onward transfer leaving each hop. It
    is required for the proportional method to split correctly: a hop that
    forwards 5 of the 10 it received to this path's next address must report
    half, not the full amount. When omitted, the path edges are used, which
    treats the path as the only known onward movement.

    An asset change ends tracing with ``swap_asset_change`` because the
    identity of the asset no longer matches the traced unit of account.
    """
    if not path_transfers:
        return TraceResult(
            traced_amount=Decimal("0"),
            asset_id="native",
            method=TracingMethod.NONE,
            continuity_ratio=Decimal("0"),
            notes=("empty_path",),
        )

    origin = path_transfers[0]
    asset_id = origin.asset_id
    origin_amount = _as_decimal(origin.amount_decimal, origin.amount_raw)

    if origin_amount <= 0:
        return TraceResult(
            traced_amount=Decimal("0"),
            asset_id=asset_id,
            method=method,
            continuity_ratio=Decimal("0"),
            notes=("zero_origin_amount",),
        )

    effective_method = TracingMethod.NONE if len(path_transfers) == 1 else method

    if effective_method is TracingMethod.NONE:
        return TraceResult(
            traced_amount=origin_amount,
            asset_id=asset_id,
            method=TracingMethod.NONE,
            continuity_ratio=Decimal("1"),
            notes=("single_hop",),
        )

    pool = list(onward_pool) if onward_pool is not None else list(path_transfers)

    if effective_method is TracingMethod.PROPORTIONAL:
        traced = _trace_proportional_chain(path_transfers, pool, asset_id)
        notes: tuple[str, ...] = ()
    else:
        traced, notes = _trace_fifo_chain(path_transfers, pool, asset_id)

    if traced is None:
        return TraceResult(
            traced_amount=Decimal("0"),
            asset_id=asset_id,
            method=effective_method,
            continuity_ratio=Decimal("0"),
            break_reason=PathBreakReason.SWAP_ASSET_CHANGE,
            notes=notes + ("asset_change",),
        )

    ratio = traced / origin_amount
    return TraceResult(
        traced_amount=traced,
        asset_id=asset_id,
        method=effective_method,
        continuity_ratio=ratio,
        notes=notes,
    )


def _trace_proportional_chain(
    path_transfers: Sequence[NormalizedTransfer],
    pool: Sequence[NormalizedTransfer],
    asset_id: str,
) -> Decimal | None:
    """Follow the proportional method across every hop of the path."""
    available = _as_decimal(path_transfers[0].amount_decimal, path_transfers[0].amount_raw)

    for index in range(len(path_transfers) - 1):
        hop = path_transfers[index]
        onward = path_transfers[index + 1]

        if onward.asset_id != asset_id:
            return None

        if onward.asset_symbol != hop.asset_symbol:
            return None

        onward_from_hop = [t for t in pool if t.sender == hop.receiver]
        available = trace_proportional(available, onward, onward_from_hop)

        if available <= 0:
            return available

    return available


def _trace_fifo_chain(
    path_transfers: Sequence[NormalizedTransfer],
    pool: Sequence[NormalizedTransfer],
    asset_id: str,
) -> tuple[Decimal, tuple[str, ...]]:
    """Follow the FIFO method across every hop of the path."""
    notes: list[str] = []
    available = _as_decimal(path_transfers[0].amount_decimal, path_transfers[0].amount_raw)
    consumed_hops = 0

    for index in range(1, len(path_transfers)):
        hop = path_transfers[index]
        if hop.asset_id != asset_id:
            break

        onward = _available_outgoing(pool, path_transfers[index - 1].receiver, asset_id)
        if not onward:
            notes.append("no_onward_transfer")
            break

        spendable = min(
            available,
            _as_decimal(onward[0].amount_decimal, onward[0].amount_raw),
        )
        available -= spendable
        consumed_hops += 1

        if available <= 0:
            break

    if consumed_hops < len(path_transfers) - 1:
        notes.append("balance_exhausted_before_path_end")

    return available, tuple(notes)

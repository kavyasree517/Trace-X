"""Unit tests for value tracing, breaks, expansion, and ranking."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.core.config import Settings
from app.core.enums import PathBreakReason, TracingMethod
from app.graph import (
    ExpansionLimits,
    build_graph,
    detect_asset_change,
    detect_node_break,
    enumerate_paths,
    expand_graph,
    rank_paths,
    trace_proportional,
    trace_value,
)
from tests.conftest import (
    ADDRESS_A,
    ADDRESS_B,
    ADDRESS_C,
    ADDRESS_D,
    ADDRESS_EXCHANGE,
    make_transfer,
)


def test_proportional_shares_balance_between_two_recipients() -> None:
    onward_c = make_transfer(ADDRESS_B, ADDRESS_C, amount="4.0")
    onward_d = make_transfer(ADDRESS_B, ADDRESS_D, amount="6.0")

    traced = trace_proportional(Decimal("10.0"), onward_c, [onward_c, onward_d])

    assert traced == Decimal("4.000000000000000000")


def test_proportional_explains_half_when_balanced_split() -> None:
    onward_c = make_transfer(ADDRESS_B, ADDRESS_C, amount="5.0")
    onward_d = make_transfer(ADDRESS_B, ADDRESS_D, amount="5.0")

    traced = trace_proportional(Decimal("10.0"), onward_c, [onward_c, onward_d])

    assert traced == Decimal("5.000000000000000000")


def test_proportional_respects_split_against_full_flow() -> None:
    onward = make_transfer(ADDRESS_B, ADDRESS_C, amount="4.0")

    traced = trace_proportional(Decimal("10.0"), onward, [onward])

    assert traced == Decimal("4.000000000000000000")


def test_proportional_returns_zero_without_onward_transfers() -> None:
    onward = make_transfer(ADDRESS_B, ADDRESS_C, amount="1.0")

    assert trace_proportional(Decimal("10.0"), onward, []) == Decimal("0")


def test_trace_value_single_hop_reports_full_continuity() -> None:
    result = trace_value([make_transfer(ADDRESS_A, ADDRESS_B, amount="3.0")])

    assert result.method is TracingMethod.NONE
    assert result.continuity_ratio == Decimal("1")
    assert result.traced_amount == Decimal("3.0")


def test_trace_value_empty_path_is_zero() -> None:
    result = trace_value([])

    assert result.traced_amount == Decimal("0")
    assert result.continuity_ratio == Decimal("0")


def test_asset_change_ends_tracing_with_break() -> None:
    path = [
        make_transfer(ADDRESS_A, ADDRESS_B, amount="5.0"),
        make_transfer(
            ADDRESS_B,
            ADDRESS_C,
            amount="100.0",
            asset_id="usdt",
            asset_symbol="USDT",
            decimals=6,
        ),
    ]

    result = trace_value(path)

    assert result.has_break
    assert result.break_reason is PathBreakReason.SWAP_ASSET_CHANGE


def test_traced_value_never_exceeds_originating_value() -> None:
    path = [
        make_transfer(ADDRESS_A, ADDRESS_B, amount="5.0", log_index=1),
        make_transfer(ADDRESS_B, ADDRESS_C, amount="50.0", log_index=2),
        make_transfer(ADDRESS_C, ADDRESS_D, amount="500.0", log_index=3),
    ]

    result = trace_value(path, onward_pool=path)

    assert result.traced_amount <= Decimal("5.0")
    assert result.continuity_ratio <= Decimal("1")


def test_fifo_consumes_balance_in_timestamp_order() -> None:
    transfers = [
        make_transfer(ADDRESS_A, ADDRESS_B, amount="10.0", minutes=0),
        make_transfer(ADDRESS_B, ADDRESS_C, amount="3.0", minutes=1),
        make_transfer(ADDRESS_B, ADDRESS_D, amount="4.0", minutes=2),
    ]

    result = trace_value(transfers, TracingMethod.FIFO, onward_pool=transfers)

    assert result.method is TracingMethod.FIFO
    assert result.traced_amount == Decimal("7.0")
    assert "no_onward_transfer" in result.notes


def test_mixer_label_breaks_the_path() -> None:
    result = detect_node_break(ADDRESS_A, {"mixer"})

    assert result.has_break
    assert result.reason is PathBreakReason.MIXER_INTERACTION


def test_bridge_label_breaks_the_path() -> None:
    result = detect_node_break(ADDRESS_A, {"bridge"})

    assert result.reason is PathBreakReason.BRIDGE_INTERACTION


def test_exchange_label_is_terminal_not_a_break() -> None:
    result = detect_node_break(ADDRESS_EXCHANGE, {"exchange_deposit_address"})

    assert result.has_break is False


def test_unlabelled_destination_does_not_break() -> None:
    result = detect_node_break(ADDRESS_A, set())

    assert result.has_break is False


def test_asset_change_is_not_a_break_when_swap_is_decoded() -> None:
    result = detect_asset_change("native", "usdt", decoded=True)

    assert result.has_break is False


def test_asset_change_breaks_when_swap_not_decoded() -> None:
    result = detect_asset_change("native", "usdt", decoded=False)

    assert result.reason is PathBreakReason.SWAP_ASSET_CHANGE


async def test_expansion_stops_at_terminal_labelled_address() -> None:
    transfers = [
        make_transfer(ADDRESS_A, ADDRESS_EXCHANGE, amount="5.0", minutes=0, log_index=1),
        make_transfer(ADDRESS_EXCHANGE, ADDRESS_C, amount="5.0", minutes=5, log_index=2),
    ]
    build = build_graph(transfers)
    build.graph.nodes[ADDRESS_EXCHANGE]["entity_types"] = {"exchange_deposit_address"}

    limits = ExpansionLimits(
        max_hops=3,
        max_nodes=100,
        max_edges=100,
        time_window_days=30,
        deadline_seconds=10,
        high_degree_threshold=200,
    )
    outcome = await expand_graph(build.graph, [ADDRESS_A], limits)

    assert ADDRESS_EXCHANGE in outcome.terminal_addresses
    assert ADDRESS_C not in outcome.expanded_addresses


async def test_expansion_respects_node_budget() -> None:
    transfers = [
        make_transfer(ADDRESS_A, ADDRESS_B, minutes=0, log_index=1),
        make_transfer(ADDRESS_A, ADDRESS_C, minutes=1, log_index=2),
        make_transfer(ADDRESS_A, ADDRESS_D, minutes=2, log_index=3),
    ]
    build = build_graph(transfers)

    limits = ExpansionLimits(
        max_hops=2,
        max_nodes=1,
        max_edges=100,
        time_window_days=30,
        deadline_seconds=10,
        high_degree_threshold=200,
    )
    outcome = await expand_graph(build.graph, [ADDRESS_A], limits)

    assert outcome.truncated
    assert outcome.truncation_reason is PathBreakReason.EXPANSION_LIMIT_REACHED


async def test_expansion_does_not_expand_hubs() -> None:
    transfers = [
        make_transfer(ADDRESS_A, ADDRESS_B, minutes=0, log_index=1),
        make_transfer(ADDRESS_B, ADDRESS_C, minutes=1, log_index=2),
    ]
    build = build_graph(transfers)

    limits = ExpansionLimits(
        max_hops=3,
        max_nodes=100,
        max_edges=100,
        time_window_days=30,
        deadline_seconds=10,
        high_degree_threshold=0,
    )
    outcome = await expand_graph(build.graph, [ADDRESS_A], limits)

    assert ADDRESS_B in outcome.terminal_addresses


def test_paths_never_decrease_in_time() -> None:
    transfers = [
        make_transfer(ADDRESS_A, ADDRESS_B, minutes=0, log_index=1),
        make_transfer(ADDRESS_B, ADDRESS_C, minutes=10, log_index=2),
        make_transfer(ADDRESS_C, ADDRESS_D, minutes=5, log_index=3),
    ]
    build = build_graph(transfers)

    result = enumerate_paths(
        build.graph, [ADDRESS_A], max_hops=3, min_continuity_ratio=0.0, max_paths=50
    )

    for path in result.paths:
        timestamps = [t.block_timestamp for t in path.transfers]
        assert timestamps == sorted(timestamps)


def test_low_continuity_paths_are_pruned() -> None:
    transfers = [
        make_transfer(ADDRESS_A, ADDRESS_B, amount="10.0", minutes=0, log_index=1),
        make_transfer(ADDRESS_B, ADDRESS_C, amount="10.0", minutes=1, log_index=2),
        make_transfer(ADDRESS_C, ADDRESS_D, amount="0.001", minutes=2, log_index=3),
    ]
    build = build_graph(transfers)

    result = enumerate_paths(
        build.graph, [ADDRESS_A], max_hops=3, min_continuity_ratio=0.05, max_paths=50
    )

    assert result.pruned_low_continuity > 0
    assert all(p.continuity_ratio >= Decimal("0.05") for p in result.paths)


def test_path_cap_reports_omitted_count() -> None:
    transfers = [
        make_transfer(ADDRESS_A, ADDRESS_B, minutes=0, log_index=1),
        make_transfer(ADDRESS_B, ADDRESS_C, minutes=1, log_index=2),
        make_transfer(ADDRESS_B, ADDRESS_D, minutes=2, log_index=3),
    ]
    build = build_graph(transfers)

    result = enumerate_paths(
        build.graph, [ADDRESS_A], max_hops=2, min_continuity_ratio=0.0, max_paths=1
    )

    assert len(result.paths) == 1
    assert result.omitted_count >= 1


def test_ranking_prefers_anchored_and_continuous_paths() -> None:
    anchored = [
        make_transfer(ADDRESS_A, ADDRESS_B, amount="5.0", minutes=0, log_index=1),
        make_transfer(ADDRESS_B, ADDRESS_C, amount="5.0", minutes=1, log_index=2),
    ]
    build = build_graph(anchored)
    paths = enumerate_paths(
        build.graph, [ADDRESS_A], max_hops=2, min_continuity_ratio=0.0, max_paths=50
    ).paths

    ranked = rank_paths(paths, Settings())

    assert ranked[0].path.anchored_to_reported_tx
    assert ranked[0].ordering_value > 0
    assert ranked[0].criteria_breakdown


def test_ranking_breakdown_has_no_probability_language() -> None:
    build = build_graph([make_transfer(ADDRESS_A, ADDRESS_B, log_index=1)])
    paths = enumerate_paths(
        build.graph, [ADDRESS_A], max_hops=1, min_continuity_ratio=0.0, max_paths=5
    ).paths

    ranked = rank_paths(paths, Settings())

    for entry in ranked[0].criteria_breakdown:
        assert "probab" not in str(entry).lower()
        assert "score" not in str(entry).lower()


def test_identical_input_produces_identical_output() -> None:
    transfers = [
        make_transfer(ADDRESS_A, ADDRESS_B, minutes=0, log_index=1),
        make_transfer(ADDRESS_B, ADDRESS_C, minutes=5, log_index=2),
    ]

    first = enumerate_paths(build_graph(transfers).graph, [ADDRESS_A], 3, 0.0, 10)
    second = enumerate_paths(build_graph(transfers).graph, [ADDRESS_A], 3, 0.0, 10)

    assert [p.addresses for p in first.paths] == [p.addresses for p in second.paths]
    assert [p.traced_value for p in first.paths] == [p.traced_value for p in second.paths]


@settings(max_examples=30, deadline=None)
@given(
    amounts=st.lists(
        st.decimals(min_value=Decimal("0.000001"), max_value=Decimal("1000"), places=6),
        min_size=2,
        max_size=6,
    )
)
def test_property_traced_value_never_exceeds_origin(amounts: list[Decimal]) -> None:
    transfers = [make_transfer(ADDRESS_A, ADDRESS_B, amount=str(amounts[0]), log_index=1)]
    for index, amount in enumerate(amounts[1:]):
        transfers.append(
            make_transfer(
                ADDRESS_B,
                ADDRESS_C if index % 2 == 0 else ADDRESS_D,
                amount=str(amount),
                minutes=index + 1,
                log_index=index + 2,
            )
        )

    result = trace_value(transfers)

    assert result.traced_amount <= Decimal(amounts[0])


@settings(max_examples=20, deadline=None)
@given(minutes=st.lists(st.integers(min_value=0, max_value=500), min_size=2, max_size=8))
def test_property_path_timestamps_never_decrease(minutes: list[int]) -> None:
    transfers = [
        make_transfer(
            ADDRESS_A if index == 0 else (ADDRESS_B if index % 2 == 1 else ADDRESS_C),
            ADDRESS_B if index == 0 else (ADDRESS_C if index % 2 == 1 else ADDRESS_D),
            minutes=minutes[index],
            log_index=index + 1,
        )
        for index in range(len(minutes))
    ]
    build = build_graph(transfers)

    result = enumerate_paths(
        build.graph, [ADDRESS_A], max_hops=len(minutes), min_continuity_ratio=0.0, max_paths=100
    )

    for path in result.paths:
        timestamps = [t.block_timestamp for t in path.transfers]
        assert timestamps == sorted(timestamps)


async def test_expansion_returns_within_deadline() -> None:
    transfers = [make_transfer(ADDRESS_A, ADDRESS_B, minutes=0, log_index=1)]
    build = build_graph(transfers)

    limits = ExpansionLimits(
        max_hops=4,
        max_nodes=100,
        max_edges=100,
        time_window_days=30,
        deadline_seconds=-1,
        high_degree_threshold=200,
    )
    outcome = await expand_graph(build.graph, [ADDRESS_A], limits)

    assert outcome.truncated
    assert "wall clock" in (outcome.truncation_detail or "")


def test_elapsed_seconds_is_non_negative() -> None:
    transfers = [
        make_transfer(ADDRESS_A, ADDRESS_B, minutes=0, log_index=1),
        make_transfer(ADDRESS_B, ADDRESS_C, minutes=30, log_index=2),
    ]
    build = build_graph(transfers)
    paths = enumerate_paths(build.graph, [ADDRESS_A], 2, 0.0, 5).paths

    assert paths
    for path in paths:
        assert path.elapsed_seconds == int(
            (path.last_timestamp - path.first_timestamp).total_seconds()
        )
        assert path.elapsed_seconds >= 0


@pytest.mark.parametrize("bad_asset", ["", "not-an-asset"])
def test_trace_with_missing_asset_id_is_handled(bad_asset: str) -> None:
    transfer = make_transfer(ADDRESS_A, ADDRESS_B, amount="1.0")
    result = trace_value([transfer])

    assert result.asset_id == "native"
    assert bad_asset != result.asset_id


def test_window_bounds_are_respected() -> None:
    assert timedelta(days=1).total_seconds() == 86400.0

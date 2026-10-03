"""Unit tests for label registry, confidence rules, matching and infrastructure."""

from __future__ import annotations

import json
from datetime import UTC, date, timedelta
from pathlib import Path

import pytest

from app.attribution.confidence import (
    ConfidenceInput,
    best_level,
    decide_attribution_state,
    evaluate_confidence,
    is_label_stale,
)
from app.attribution.infrastructure import (
    INFRASTRUCTURE_CAVEAT,
    assess_address,
    exclude_infrastructure_addresses,
)
from app.attribution.matcher import (
    PathAttribution,
    best_confidence,
    classify_connection,
    explain_attribution,
    headline_state_from,
    match_path,
)
from app.attribution.registry import (
    EntityLabelRecord,
    LabelRegistry,
    LabelRegistryError,
    default_registry_dir,
    label_from_dict,
    load_registry,
    registry_from_settings,
    seed_timestamp,
)
from app.core.config import get_settings
from app.core.enums import (
    AttributionConfidenceLevel,
    AttributionState,
    ConnectionType,
    EntityType,
    LabelOrigin,
    PathBreakReason,
    SourceType,
    TracingMethod,
    VerificationLevel,
)
from app.core.security import canonicalize_address
from app.graph.breaks import BreakResult
from app.graph.paths import CandidatePath, PathEdgeRecord
from app.graph.value_tracing import trace_value
from tests.conftest import (
    ADDRESS_A,
    ADDRESS_B,
    ADDRESS_C,
    ADDRESS_D,
    ADDRESS_EXCHANGE,
    ADDRESS_MIXER,
    BASE_TIME,
    make_transfer,
)

CHAIN = "ethereum"
TODAY = date(2026, 3, 15)
STALE_AFTER_DAYS = 365

# A reference outside the synthetic namespace, used to show that a citable
# label can be verified and is therefore accepted.
CITABLE_REFERENCE = "https://example.org/public-disclosure/exchange-a"


def label_payload(**overrides: object) -> dict[str, object]:
    """Return a valid level 2 label payload, overridable per test."""
    payload: dict[str, object] = {
        "entity_name": "Example Exchange",
        "entity_type": EntityType.EXCHANGE.value,
        "chain": CHAIN,
        "address": ADDRESS_EXCHANGE,
        "label_origin": LabelOrigin.OBSERVED_LABEL.value,
        "source_name": "Example public disclosure",
        "source_type": SourceType.REPUTABLE_SECONDARY.value,
        "source_reference": CITABLE_REFERENCE,
        "verification_level": VerificationLevel.LEVEL_2_REPUTABLE_SECONDARY.value,
        "observed_at": "2025-01-01",
        "last_verified_at": "2026-01-01",
        "scope_notes": "Applies to this address only.",
        "is_shared_infrastructure": False,
        "is_active": True,
    }
    payload.update(overrides)
    return payload


def make_registry(*records: EntityLabelRecord) -> LabelRegistry:
    """Build an in-memory registry from label records."""
    registry = LabelRegistry()
    for record in records:
        registry.add(record)
    registry.snapshot_hash = registry.compute_hash()
    return registry


def single_label_registry(**overrides: object) -> LabelRegistry:
    """Return a registry holding one label built from an overridable payload."""
    return make_registry(label_from_dict(label_payload(**overrides)))


def make_path(
    addresses: list[str],
    *,
    has_break: bool = False,
    break_reason: PathBreakReason | None = None,
    terminal_types: set[str] | None = None,
    amounts: list[str] | None = None,
) -> CandidatePath:
    """Build a candidate path with a deterministic edge set."""
    transfers = []
    resolved_amounts = amounts or ["5.0"] * max(len(addresses) - 1, 0)
    for index in range(len(addresses) - 1):
        transfers.append(
            make_transfer(
                addresses[index],
                addresses[index + 1],
                amount=resolved_amounts[index],
                minutes=index,
                log_index=index + 1,
            )
        )

    break_result = (
        BreakResult.broken(break_reason or PathBreakReason.MIXER_INTERACTION, "test break")
        if has_break
        else BreakResult.clear()
    )
    graph_addresses = list(addresses)

    return CandidatePath(
        addresses=graph_addresses,
        transfers=transfers,
        edges=[PathEdgeRecord.from_transfer(i, t) for i, t in enumerate(transfers)],
        trace=trace_value(transfers, TracingMethod.PROPORTIONAL, onward_pool=transfers),
        break_result=break_result,
        anchored_to_reported_tx=True,
        terminal_labelled=bool(terminal_types),
    )


def confidence_input(**overrides: object) -> ConfidenceInput:
    """Return a confidence input with neutral defaults for a level 2 label."""
    defaults: dict[str, object] = {
        "verification_level": VerificationLevel.LEVEL_2_REPUTABLE_SECONDARY.value,
        "label_origin": LabelOrigin.OBSERVED_LABEL.value,
        "independent_source_count": 1,
        "connection_type": ConnectionType.INDIRECT,
        "path_intact": True,
        "label_is_stale": False,
        "scope_match": True,
        "is_demo": False,
    }
    defaults.update(overrides)
    return ConfidenceInput(**defaults)  # type: ignore[arg-type]


def run_match(
    path: CandidatePath, registry: LabelRegistry, *, is_demo: bool = False
) -> list[PathAttribution]:
    """Match a path against a registry with today's staleness window applied."""
    return match_path(
        path,
        registry,
        CHAIN,
        is_demo=is_demo,
        today=TODAY,
        stale_after_days=STALE_AFTER_DAYS,
    )


def synthetic_mixer_registry() -> LabelRegistry:
    """Return a registry holding one synthetic mixer label in demo mode."""
    return single_label_registry(
        address=ADDRESS_MIXER,
        entity_type=EntityType.MIXER.value,
        verification_level=VerificationLevel.LEVEL_0_SYNTHETIC.value,
        source_type=SourceType.SYNTHETIC.value,
        source_reference="https://example.invalid/trace-x/demo-label/test",
    )


# Registry validation


def test_registry_loads_the_shipped_file_without_errors(label_registry_dir: Path) -> None:
    registry = load_registry(label_registry_dir, is_demo=True)

    assert registry.load_errors == []
    assert registry.total_labels() > 0


def test_registry_hash_is_stable_across_loads(label_registry_dir: Path) -> None:
    first = load_registry(label_registry_dir, is_demo=True)
    second = load_registry(label_registry_dir, is_demo=True)

    assert first.snapshot_hash == second.snapshot_hash
    assert len(first.snapshot_hash) == 64


def test_synthetic_labels_load_in_demo_and_are_skipped_outside_it(
    label_registry_dir: Path,
) -> None:
    demo = load_registry(label_registry_dir, is_demo=True)
    live = load_registry(label_registry_dir, is_demo=False)

    synthetic_demo = [
        label for labels in demo.labels.values() for label in labels if label.is_synthetic
    ]
    synthetic_live = [
        label for labels in live.labels.values() for label in labels if label.is_synthetic
    ]

    assert synthetic_demo
    assert synthetic_live == []
    assert live.total_labels() < demo.total_labels()


def test_synthetic_skip_is_recorded_as_a_load_error(label_registry_dir: Path) -> None:
    live = load_registry(label_registry_dir, is_demo=False)

    assert any("synthetic label skipped" in error for error in live.load_errors)


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"address": "0x1234"}, "Invalid label address"),
        (
            {"source_reference": "not-a-url"},
            "Source reference must be a URL",
        ),
        ({"verification_level": "level_9_invented"}, "Unknown verification level"),
        ({"entity_type": "dark_pool"}, "Unknown entity type"),
        ({"source_type": "rumour"}, "Unknown source type"),
        ({"last_verified_at": None}, "require last_verified_at"),
        ({"observed_at": "15-03-2026"}, "not an ISO 8601 date"),
    ],
)
def test_registry_rejects_invalid_entries(overrides: dict[str, object], expected: str) -> None:
    with pytest.raises(LabelRegistryError) as excinfo:
        label_from_dict(label_payload(**overrides))

    assert expected in str(excinfo.value)


@pytest.mark.parametrize(
    "missing", ["entity_name", "entity_type", "address", "source_name", "source_reference"]
)
def test_registry_rejects_entries_missing_required_fields(missing: str) -> None:
    payload = label_payload()
    del payload[missing]

    with pytest.raises(LabelRegistryError) as excinfo:
        label_from_dict(payload)

    assert missing in str(excinfo.value)


def test_registry_rejects_synthetic_label_pointing_outside_the_fixture_namespace() -> None:
    payload = label_payload(
        source_type=SourceType.SYNTHETIC.value,
        verification_level=VerificationLevel.LEVEL_0_SYNTHETIC.value,
        source_reference="https://etherscan.io/address/0x1234",
    )

    with pytest.raises(LabelRegistryError) as excinfo:
        label_from_dict(payload)

    assert "example.invalid" in str(excinfo.value)


def test_one_bad_entry_does_not_stop_the_file_from_loading(tmp_path: Path) -> None:
    payload = {"labels": [label_payload(), {"entity_name": "Incomplete"}]}
    (tmp_path / "mixed.json").write_text(json.dumps(payload), encoding="utf-8")

    registry = load_registry(tmp_path, is_demo=True)

    assert registry.total_labels() == 1
    assert len(registry.load_errors) == 1


def test_invalid_json_is_reported_rather_than_raising(tmp_path: Path) -> None:
    (tmp_path / "broken.json").write_text("{not json", encoding="utf-8")

    registry = load_registry(tmp_path, is_demo=True)

    assert registry.load_errors
    assert "invalid JSON" in registry.load_errors[0]


def test_a_registry_file_that_is_not_a_list_of_labels_is_reported(tmp_path: Path) -> None:
    (tmp_path / "wrong.json").write_text(
        json.dumps({"labels": {"not": "a list"}}), encoding="utf-8"
    )

    registry = load_registry(tmp_path, is_demo=True)

    assert registry.load_errors == ["wrong.json: expected a list of labels"]


def test_a_bare_label_object_without_a_labels_key_is_still_accepted(tmp_path: Path) -> None:
    (tmp_path / "bare.json").write_text(json.dumps(label_payload()), encoding="utf-8")

    registry = load_registry(tmp_path, is_demo=True)

    assert registry.total_labels() == 1


def test_registry_loads_using_the_configured_directory() -> None:
    registry = registry_from_settings()

    assert len(registry.snapshot_hash) == 64
    assert registry.total_labels() > 0


def test_the_default_registry_directory_is_absolute() -> None:
    assert default_registry_dir().is_absolute()


def test_an_absolute_registry_directory_setting_is_used_as_given(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("LABEL_REGISTRY_DIR", str(tmp_path))

    get_settings.cache_clear()
    try:
        assert default_registry_dir() == tmp_path
    finally:
        get_settings.cache_clear()


def test_seed_timestamp_is_timezone_aware() -> None:
    assert seed_timestamp().tzinfo is UTC


def test_missing_registry_directory_returns_an_empty_registry(tmp_path: Path) -> None:
    registry = load_registry(tmp_path / "absent", is_demo=True)

    assert registry.total_labels() == 0
    assert len(registry.snapshot_hash) == 64


def test_lookup_accepts_lower_case_and_active_only() -> None:
    registry = single_label_registry()

    found = registry.lookup(CHAIN, ADDRESS_EXCHANGE.lower())

    assert len(found) == 1
    assert found[0].address == canonicalize_address(ADDRESS_EXCHANGE)


def test_lookup_returns_nothing_for_an_invalid_address() -> None:
    registry = single_label_registry()

    assert registry.lookup(CHAIN, "not-an-address") == []


def test_inactive_labels_are_excluded_from_lookup() -> None:
    registry = single_label_registry(is_active=False)

    assert registry.lookup(CHAIN, ADDRESS_EXCHANGE) == []


def test_lookup_orders_the_strongest_verification_first() -> None:
    registry = make_registry(
        label_from_dict(
            label_payload(
                source_name="Community source",
                verification_level=VerificationLevel.LEVEL_1_COMMUNITY_OR_UNVERIFIED.value,
                source_type=SourceType.COMMUNITY.value,
                source_reference="https://example.org/community/list",
            )
        ),
        label_from_dict(label_payload(source_name="Disclosed source")),
    )

    found = registry.lookup(CHAIN, ADDRESS_EXCHANGE)

    assert [label.source_name for label in found] == ["Disclosed source", "Community source"]


def test_sources_for_counts_independent_source_names() -> None:
    registry = make_registry(
        label_from_dict(label_payload(source_name="Source one")),
        label_from_dict(
            label_payload(
                source_name="Source two",
                source_reference="https://example.org/second-source",
            )
        ),
    )

    assert len(registry.sources_for(CHAIN, ADDRESS_EXCHANGE)) == 2


def test_lookup_is_scoped_to_the_requested_chain() -> None:
    registry = make_registry(label_from_dict(label_payload(chain="polygon")))

    assert registry.lookup(CHAIN, ADDRESS_EXCHANGE) == []
    assert len(registry.lookup("polygon", ADDRESS_EXCHANGE)) == 1


# Label staleness


def test_label_verified_today_is_not_stale() -> None:
    assert is_label_stale(TODAY, TODAY, STALE_AFTER_DAYS) is False


def test_label_older_than_the_window_is_stale() -> None:
    assert is_label_stale(TODAY - timedelta(days=STALE_AFTER_DAYS + 1), TODAY, STALE_AFTER_DAYS)


def test_a_label_with_no_verification_date_counts_as_stale() -> None:
    assert is_label_stale(None, TODAY, STALE_AFTER_DAYS) is True


# Confidence rule table


def test_level_3_primary_source_on_an_intact_path_is_high() -> None:
    decision = evaluate_confidence(
        confidence_input(
            verification_level=VerificationLevel.LEVEL_3_PRIMARY_SOURCE.value,
        )
    )

    assert decision.level is AttributionConfidenceLevel.HIGH
    assert decision.rule_applied == "level_3_primary_source"


def test_two_independent_level_2_sources_are_high() -> None:
    decision = evaluate_confidence(
        confidence_input(
            verification_level=VerificationLevel.LEVEL_2_REPUTABLE_SECONDARY.value,
            independent_source_count=2,
        )
    )

    assert decision.level is AttributionConfidenceLevel.HIGH
    assert decision.rule_applied == "two_or_more_level_2_sources"


def test_a_single_level_2_source_is_medium() -> None:
    decision = evaluate_confidence(confidence_input(independent_source_count=1))

    assert decision.level is AttributionConfidenceLevel.MEDIUM
    assert decision.rule_applied == "single_level_2_source"


def test_a_stale_level_3_source_is_reduced_to_medium() -> None:
    decision = evaluate_confidence(
        confidence_input(
            verification_level=VerificationLevel.LEVEL_3_PRIMARY_SOURCE.value,
            label_is_stale=True,
        )
    )

    assert decision.level is AttributionConfidenceLevel.MEDIUM
    assert decision.rule_applied == "level_3_but_stale"


def test_a_stale_single_level_2_source_is_low() -> None:
    decision = evaluate_confidence(confidence_input(label_is_stale=True))

    assert decision.level is AttributionConfidenceLevel.LOW
    assert decision.rule_applied == "single_level_2_stale"


def test_an_unrecognised_verification_level_gives_no_confidence() -> None:
    decision = evaluate_confidence(confidence_input(verification_level="level_9_invented"))

    assert decision.level is AttributionConfidenceLevel.NONE
    assert decision.rule_applied == "unrecognised_verification_level"


def test_an_unusable_label_yields_no_match_rather_than_an_association() -> None:
    decision = evaluate_confidence(confidence_input(verification_level="level_9_invented"))

    state = decide_attribution_state(decision, has_label=True)

    assert state is AttributionState.NO_MATCH_IN_CURRENT_REFERENCES


def test_a_level_1_community_source_is_low() -> None:
    decision = evaluate_confidence(
        confidence_input(verification_level=VerificationLevel.LEVEL_1_COMMUNITY_OR_UNVERIFIED.value)
    )

    assert decision.level is AttributionConfidenceLevel.LOW
    assert decision.rule_applied == "level_1_community_only"


def test_an_inferred_cluster_label_is_low() -> None:
    decision = evaluate_confidence(
        confidence_input(
            verification_level=VerificationLevel.LEVEL_3_PRIMARY_SOURCE.value,
            label_origin=LabelOrigin.INFERRED_CLUSTER.value,
        )
    )

    assert decision.level is AttributionConfidenceLevel.LOW
    assert decision.rule_applied == "inferred_cluster"


def test_a_broken_path_is_low() -> None:
    decision = evaluate_confidence(
        confidence_input(
            verification_level=VerificationLevel.LEVEL_3_PRIMARY_SOURCE.value,
            path_intact=False,
        )
    )

    assert decision.level is AttributionConfidenceLevel.LOW
    assert decision.rule_applied == "path_break"


def test_a_synthetic_label_outside_demo_mode_is_none() -> None:
    decision = evaluate_confidence(
        confidence_input(
            verification_level=VerificationLevel.LEVEL_0_SYNTHETIC.value,
            is_demo=False,
        )
    )

    assert decision.level is AttributionConfidenceLevel.NONE
    assert decision.rule_applied == "synthetic_outside_demo"
    assert decision.is_synthetic is True


def test_a_synthetic_label_inside_demo_mode_is_low_not_none() -> None:
    decision = evaluate_confidence(
        confidence_input(
            verification_level=VerificationLevel.LEVEL_0_SYNTHETIC.value,
            is_demo=True,
        )
    )

    assert decision.level is AttributionConfidenceLevel.LOW
    assert decision.rule_applied == "synthetic_demo_only"
    assert decision.is_synthetic is True


def test_confidence_returns_every_factor_it_used() -> None:
    decision = evaluate_confidence(confidence_input(label_is_stale=True))
    payload = decision.factors_payload

    assert set(payload) == {
        "verification_level",
        "label_origin",
        "label_is_stale",
        "scope_match",
        "independent_source_count",
        "connection_type",
        "path_intact",
        "rule_applied",
    }


def test_confidence_output_contains_no_percentage_or_probability() -> None:
    decision = evaluate_confidence(confidence_input())

    rendered = f"{decision.level.value} {decision.factors_payload}"
    assert "%" not in rendered
    assert "probab" not in rendered.lower()


def test_best_level_returns_the_strongest_present() -> None:
    levels = [
        AttributionConfidenceLevel.NONE,
        AttributionConfidenceLevel.LOW,
        AttributionConfidenceLevel.HIGH,
    ]

    assert best_level(levels) is AttributionConfidenceLevel.HIGH


def test_best_level_of_an_empty_sequence_is_none() -> None:
    assert best_level([]) is AttributionConfidenceLevel.NONE


# Attribution states


def test_high_confidence_on_an_observed_label_is_a_verified_match() -> None:
    decision = evaluate_confidence(
        confidence_input(verification_level=VerificationLevel.LEVEL_3_PRIMARY_SOURCE.value)
    )

    state = decide_attribution_state(decision, has_label=True)

    assert state is AttributionState.VERIFIED_LABEL_MATCH


def test_low_confidence_is_a_potential_association() -> None:
    decision = evaluate_confidence(
        confidence_input(verification_level=VerificationLevel.LEVEL_1_COMMUNITY_OR_UNVERIFIED.value)
    )

    state = decide_attribution_state(decision, has_label=True)

    assert state is AttributionState.POTENTIAL_ASSOCIATION


def test_a_broken_path_yields_insufficient_data() -> None:
    decision = evaluate_confidence(
        confidence_input(
            verification_level=VerificationLevel.LEVEL_3_PRIMARY_SOURCE.value,
            path_intact=False,
        )
    )

    state = decide_attribution_state(decision, has_label=True)

    assert state is AttributionState.INSUFFICIENT_DATA


def test_an_unlabelled_terminal_yields_no_match_in_current_references() -> None:
    decision = evaluate_confidence(confidence_input())

    state = decide_attribution_state(decision, has_label=False)

    assert state is AttributionState.NO_MATCH_IN_CURRENT_REFERENCES


def test_a_synthetic_label_outside_demo_mode_yields_no_match() -> None:
    decision = evaluate_confidence(
        confidence_input(
            verification_level=VerificationLevel.LEVEL_0_SYNTHETIC.value,
            is_demo=False,
        )
    )

    state = decide_attribution_state(decision, has_label=True, is_synthetic_outside_demo=True)

    assert state is AttributionState.NO_MATCH_IN_CURRENT_REFERENCES


def test_a_synthetic_label_inside_demo_mode_is_never_a_verified_match() -> None:
    decision = evaluate_confidence(
        confidence_input(
            verification_level=VerificationLevel.LEVEL_0_SYNTHETIC.value,
            is_demo=True,
        )
    )

    state = decide_attribution_state(decision, has_label=True)

    assert state is not AttributionState.VERIFIED_LABEL_MATCH


def test_every_attribution_state_is_reachable() -> None:
    seen = {
        decide_attribution_state(evaluate_confidence(confidence_input()), has_label=False),
        decide_attribution_state(
            evaluate_confidence(
                confidence_input(
                    verification_level=VerificationLevel.LEVEL_3_PRIMARY_SOURCE.value,
                    path_intact=False,
                )
            ),
            has_label=True,
        ),
        decide_attribution_state(
            evaluate_confidence(
                confidence_input(
                    verification_level=VerificationLevel.LEVEL_1_COMMUNITY_OR_UNVERIFIED.value
                )
            ),
            has_label=True,
        ),
        decide_attribution_state(
            evaluate_confidence(
                confidence_input(verification_level=VerificationLevel.LEVEL_3_PRIMARY_SOURCE.value)
            ),
            has_label=True,
        ),
    }

    assert seen == set(AttributionState)


# Path matching


def test_a_label_on_the_first_receiver_is_a_direct_connection() -> None:
    path = make_path([ADDRESS_A, ADDRESS_B, ADDRESS_C])

    assert classify_connection(path, ADDRESS_B) is ConnectionType.DIRECT


def test_a_label_further_along_is_an_indirect_connection() -> None:
    path = make_path([ADDRESS_A, ADDRESS_B, ADDRESS_C])

    assert classify_connection(path, ADDRESS_C) is ConnectionType.INDIRECT


def test_matching_a_direct_labelled_terminal_reports_medium_confidence() -> None:
    path = make_path([ADDRESS_A, ADDRESS_EXCHANGE])
    registry = single_label_registry()

    results = run_match(path, registry)

    assert len(results) == 1
    attribution = results[0]
    assert attribution.connection_type is ConnectionType.DIRECT
    assert attribution.confidence_level is AttributionConfidenceLevel.MEDIUM
    assert attribution.attribution_state is AttributionState.VERIFIED_LABEL_MATCH


def test_matching_an_unlabelled_terminal_returns_no_attribution() -> None:
    path = make_path([ADDRESS_A, ADDRESS_D])
    registry = single_label_registry()

    assert run_match(path, registry) == []


def test_a_broken_path_to_a_labelled_terminal_is_insufficient_data() -> None:
    path = make_path(
        [ADDRESS_A, ADDRESS_EXCHANGE],
        has_break=True,
        break_reason=PathBreakReason.EXPANSION_LIMIT_REACHED,
    )
    registry = single_label_registry()

    results = run_match(path, registry)

    assert results[0].attribution_state is AttributionState.INSUFFICIENT_DATA


def test_a_stale_label_is_flagged_on_the_attribution() -> None:
    path = make_path([ADDRESS_A, ADDRESS_EXCHANGE])
    registry = single_label_registry(last_verified_at="2019-01-01")

    results = run_match(path, registry)

    assert results[0].label_is_stale is True
    assert results[0].confidence_level is AttributionConfidenceLevel.LOW


def test_a_synthetic_label_matches_in_demo_mode_with_a_notice() -> None:
    path = make_path([ADDRESS_A, ADDRESS_MIXER])

    results = run_match(path, synthetic_mixer_registry(), is_demo=True)

    assert len(results) == 1
    assert results[0].attribution_state is not AttributionState.VERIFIED_LABEL_MATCH


def test_a_synthetic_label_outside_demo_mode_is_suppressed() -> None:
    path = make_path([ADDRESS_A, ADDRESS_MIXER])

    results = run_match(path, synthetic_mixer_registry())

    assert len(results) == 1
    assert results[0].confidence_level is AttributionConfidenceLevel.NONE
    assert results[0].attribution_state is AttributionState.NO_MATCH_IN_CURRENT_REFERENCES


def test_every_label_on_an_address_produces_its_own_attribution() -> None:
    path = make_path([ADDRESS_A, ADDRESS_EXCHANGE])
    registry = make_registry(
        label_from_dict(
            label_payload(
                source_name="Community source",
                verification_level=VerificationLevel.LEVEL_1_COMMUNITY_OR_UNVERIFIED.value,
                source_type=SourceType.COMMUNITY.value,
                source_reference="https://example.org/community/list",
            )
        ),
        label_from_dict(label_payload(source_name="Disclosed source")),
    )

    results = run_match(path, registry)

    assert len(results) == 2


def test_attribution_records_the_hop_count_of_the_path() -> None:
    path = make_path([ADDRESS_A, ADDRESS_B, ADDRESS_EXCHANGE])
    registry = single_label_registry()

    results = run_match(path, registry)

    assert results[0].hop_count == 2
    assert results[0].connection_type is ConnectionType.INDIRECT


def test_matching_is_identical_on_repeat_runs() -> None:
    path = make_path([ADDRESS_A, ADDRESS_B, ADDRESS_EXCHANGE])
    registry = single_label_registry()

    first = run_match(path, registry)
    second = run_match(path, registry)

    assert [a.explanation for a in first] == [a.explanation for a in second]
    assert [a.attribution_state for a in first] == [a.attribution_state for a in second]


# Explanation text


def test_explanation_names_the_source_and_does_not_implicate_the_service() -> None:
    label = label_from_dict(label_payload())
    decision = evaluate_confidence(confidence_input())

    text = explain_attribution(
        address=ADDRESS_EXCHANGE,
        label=label,
        connection=ConnectionType.DIRECT,
        confidence=decision,
        stale=False,
        hop_count=1,
        state=AttributionState.VERIFIED_LABEL_MATCH,
    )

    assert label.source_name in text
    assert "does not show that the service knew of or took part" in text


@pytest.mark.parametrize(
    "prohibited",
    [
        "criminal",
        "fraudulent",
        "guilty",
        "complicit",
        "scam",
        "confirmed fraud",
    ],
)
def test_explanation_text_contains_no_accusatory_language(prohibited: str) -> None:
    label = label_from_dict(label_payload())
    decision = evaluate_confidence(confidence_input())

    text = explain_attribution(
        address=ADDRESS_EXCHANGE,
        label=label,
        connection=ConnectionType.INDIRECT,
        confidence=decision,
        stale=True,
        hop_count=2,
        state=AttributionState.POTENTIAL_ASSOCIATION,
    ).lower()

    assert prohibited not in text


def test_explanation_reports_staleness_and_scope() -> None:
    label = label_from_dict(label_payload(scope_notes="Applies to this address only."))
    decision = evaluate_confidence(confidence_input(label_is_stale=True))

    text = explain_attribution(
        address=ADDRESS_EXCHANGE,
        label=label,
        connection=ConnectionType.DIRECT,
        confidence=decision,
        stale=True,
        hop_count=1,
        state=AttributionState.POTENTIAL_ASSOCIATION,
    )

    assert "not been verified recently" in text
    assert "Applies to this address only." in text


def test_explanation_notes_possible_shared_infrastructure() -> None:
    label = label_from_dict(label_payload(is_shared_infrastructure=True))
    decision = evaluate_confidence(confidence_input())

    text = explain_attribution(
        address=ADDRESS_EXCHANGE,
        label=label,
        connection=ConnectionType.DIRECT,
        confidence=decision,
        stale=False,
        hop_count=1,
        state=AttributionState.VERIFIED_LABEL_MATCH,
    )

    assert "possibly shared infrastructure" in text


def test_explanation_uses_the_singular_for_one_transfer() -> None:
    label = label_from_dict(label_payload())
    decision = evaluate_confidence(confidence_input())

    text = explain_attribution(
        address=ADDRESS_EXCHANGE,
        label=label,
        connection=ConnectionType.DIRECT,
        confidence=decision,
        stale=False,
        hop_count=1,
        state=AttributionState.VERIFIED_LABEL_MATCH,
    )

    assert "1 transfer" in text


# Shared infrastructure


def test_a_deposit_address_is_treated_as_shared_infrastructure() -> None:
    registry = single_label_registry(entity_type=EntityType.EXCHANGE_DEPOSIT_ADDRESS.value)

    assessment = assess_address(CHAIN, ADDRESS_EXCHANGE, registry, high_degree_threshold=200)

    assert assessment.is_shared_infrastructure is True
    assert assessment.caveat == INFRASTRUCTURE_CAVEAT


def test_an_exchange_hot_wallet_is_not_shared_infrastructure() -> None:
    registry = single_label_registry(entity_type=EntityType.EXCHANGE_HOT_WALLET.value)

    assessment = assess_address(CHAIN, ADDRESS_EXCHANGE, registry, high_degree_threshold=200)

    assert assessment.is_shared_infrastructure is False
    assert assessment.caveat is None


def test_a_hub_degree_above_the_threshold_is_flagged() -> None:
    registry = single_label_registry(entity_type=EntityType.EXCHANGE_HOT_WALLET.value)

    assessment = assess_address(
        CHAIN, ADDRESS_EXCHANGE, registry, high_degree_threshold=10, observed_degree=11
    )

    assert assessment.is_shared_infrastructure is True
    assert any("hub threshold" in reason for reason in assessment.reasons)


def test_a_registry_flagged_address_is_reported_as_shared_infrastructure() -> None:
    registry = single_label_registry(
        entity_type=EntityType.EXCHANGE_HOT_WALLET.value, is_shared_infrastructure=True
    )

    assessment = assess_address(CHAIN, ADDRESS_EXCHANGE, registry, high_degree_threshold=200)

    assert assessment.is_shared_infrastructure is True
    assert any("Registry marks" in reason for reason in assessment.reasons)


def test_infrastructure_exclusion_drops_deposit_addresses_and_hubs() -> None:
    registry = single_label_registry(
        address=ADDRESS_EXCHANGE, entity_type=EntityType.EXCHANGE_DEPOSIT_ADDRESS.value
    )

    kept = exclude_infrastructure_addresses(
        {ADDRESS_EXCHANGE, ADDRESS_A, ADDRESS_B},
        CHAIN,
        registry,
        hub_exclusion_degree=100,
        degrees={ADDRESS_B: 500},
    )

    assert kept == {ADDRESS_A}


def test_infrastructure_exclusion_keeps_ordinary_addresses() -> None:
    registry = single_label_registry()

    kept = exclude_infrastructure_addresses(
        {ADDRESS_A, ADDRESS_B}, CHAIN, registry, hub_exclusion_degree=100
    )

    assert kept == {ADDRESS_A, ADDRESS_B}


def test_the_infrastructure_caveat_does_not_imply_common_ownership() -> None:
    lowered = INFRASTRUCTURE_CAVEAT.lower()

    assert "does not indicate common ownership" in lowered
    assert "same operator" not in lowered


def test_exclusion_short_circuits_on_a_registry_flagged_address() -> None:
    registry = single_label_registry(
        entity_type=EntityType.EXCHANGE_HOT_WALLET.value, is_shared_infrastructure=True
    )

    kept = exclude_infrastructure_addresses(
        {ADDRESS_EXCHANGE, ADDRESS_A}, CHAIN, registry, hub_exclusion_degree=100
    )

    assert kept == {ADDRESS_A}


def test_entity_types_for_returns_the_recorded_types() -> None:
    registry = single_label_registry(entity_type=EntityType.EXCHANGE_HOT_WALLET.value)

    assert registry.entity_types_for(CHAIN, ADDRESS_EXCHANGE) == {
        EntityType.EXCHANGE_HOT_WALLET.value
    }


# Aggregation helpers


def test_best_confidence_returns_the_strongest_across_attributions() -> None:
    path_low = make_path([ADDRESS_A, ADDRESS_B])
    path_high = make_path([ADDRESS_A, ADDRESS_EXCHANGE])
    registry = make_registry(
        label_from_dict(
            label_payload(
                source_name="Community source",
                verification_level=VerificationLevel.LEVEL_1_COMMUNITY_OR_UNVERIFIED.value,
                source_type=SourceType.COMMUNITY.value,
                source_reference="https://example.org/community/list",
            )
        ),
        label_from_dict(
            label_payload(
                source_name="Disclosed source",
                verification_level=VerificationLevel.LEVEL_3_PRIMARY_SOURCE.value,
                source_type=SourceType.PRIMARY_DISCLOSURE.value,
                source_reference="https://example.org/primary/disclosure",
            )
        ),
    )

    low = run_match(path_low, registry)
    high = run_match(path_high, registry)

    assert best_confidence([*low, *high]) is AttributionConfidenceLevel.HIGH


def test_headline_prefers_a_verified_match_over_a_potential_association() -> None:
    path = make_path([ADDRESS_A, ADDRESS_EXCHANGE])
    community = label_from_dict(
        label_payload(
            source_name="Community source",
            verification_level=VerificationLevel.LEVEL_1_COMMUNITY_OR_UNVERIFIED.value,
            source_type=SourceType.COMMUNITY.value,
            source_reference="https://example.org/community/list",
        )
    )
    disclosed = label_from_dict(
        label_payload(
            source_name="Disclosed source",
            verification_level=VerificationLevel.LEVEL_3_PRIMARY_SOURCE.value,
            source_type=SourceType.PRIMARY_DISCLOSURE.value,
            source_reference="https://example.org/primary/disclosure",
        )
    )
    registry = make_registry(community, disclosed)

    attributions = run_match(path, registry)

    assert headline_state_from(attributions) is AttributionState.VERIFIED_LABEL_MATCH


def test_headline_is_none_when_nothing_is_labelled() -> None:
    assert headline_state_from([]) is None


def test_best_confidence_of_no_attributions_is_none() -> None:
    assert best_confidence([]) is AttributionConfidenceLevel.NONE


def test_a_path_with_no_addresses_matches_nothing() -> None:
    empty = make_path([ADDRESS_A])
    empty.addresses = []

    assert run_match(empty, single_label_registry()) == []


def test_a_single_address_path_has_no_direct_connection() -> None:
    path = make_path([ADDRESS_A])

    assert classify_connection(path, ADDRESS_A) is ConnectionType.INDIRECT


def test_an_exchange_label_is_reported_as_the_named_entity() -> None:
    path = make_path([ADDRESS_A, ADDRESS_EXCHANGE])

    attribution = run_match(path, single_label_registry())[0]

    assert attribution.is_reported_entity is True


def test_a_mixer_label_is_not_reported_as_the_named_entity() -> None:
    path = make_path([ADDRESS_A, ADDRESS_MIXER])

    attribution = run_match(path, synthetic_mixer_registry(), is_demo=True)[0]

    assert attribution.is_reported_entity is False


def test_headline_reports_potential_association_when_that_is_all_that_exists() -> None:
    path = make_path([ADDRESS_A, ADDRESS_EXCHANGE])
    registry = make_registry(
        label_from_dict(
            label_payload(
                source_name="Community source",
                verification_level=VerificationLevel.LEVEL_1_COMMUNITY_OR_UNVERIFIED.value,
                source_type=SourceType.COMMUNITY.value,
                source_reference="https://example.org/community/list",
            )
        )
    )

    assert headline_state_from(run_match(path, registry)) is AttributionState.POTENTIAL_ASSOCIATION


def test_shared_infrastructure_addresses_are_listed_for_a_chain() -> None:
    registry = single_label_registry(
        entity_type=EntityType.EXCHANGE_DEPOSIT_ADDRESS.value, is_shared_infrastructure=True
    )

    assert ADDRESS_EXCHANGE in registry.shared_infrastructure_addresses(CHAIN)
    assert registry.shared_infrastructure_addresses("polygon") == set()


def test_registry_records_the_registry_version_fields_it_understands() -> None:
    record = label_from_dict(label_payload(cluster_id="cluster-42"))

    assert record.cluster_id == "cluster-42"
    assert record.label_origin == LabelOrigin.OBSERVED_LABEL.value
    assert record.observed_at == date(2025, 1, 1)
    assert record.last_verified_at == date(2026, 1, 1)


def test_timestamps_on_test_paths_are_time_ordered() -> None:
    path = make_path([ADDRESS_A, ADDRESS_B, ADDRESS_C])

    timestamps = [transfer.block_timestamp for transfer in path.transfers]

    assert timestamps == sorted(timestamps)
    assert timestamps[0] == BASE_TIME

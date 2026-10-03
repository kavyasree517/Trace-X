"""Tests for the administrative label CLI.

The database is an in-memory SQLite instance created from the SQLAlchemy
metadata, so the change log behaviour can be verified without a server.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.attribution import seed as seed_module
from app.attribution.registry import (
    LabelRegistry,
    label_from_dict,
    load_registry,
)
from app.attribution.seed import (
    SeedError,
    _parse_changes,
    add_label,
    apply_sync_plan,
    build_parser,
    deactivate_label,
    plan_sync,
    read_label_file,
    update_label,
)
from app.core.config import Settings
from app.core.enums import EntityType, SourceType, VerificationLevel
from app.models.base import Base
from app.models.label import EntityLabel, LabelChangeLog

CHAIN = "ethereum"
ACTOR = "test_actor"
CITABLE_REFERENCE = "https://example.org/public-disclosure/exchange-a"


def label_payload(**overrides: object) -> dict[str, object]:
    """Return a valid level 2 label payload, overridable per test."""
    payload: dict[str, object] = {
        "entity_name": "Example Exchange",
        "entity_type": EntityType.EXCHANGE.value,
        "chain": CHAIN,
        "address": "0x5555555555555555555555555555555555555555",
        "label_origin": "observed_label",
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


def make_registry(*payloads: dict[str, object]) -> LabelRegistry:
    """Return a registry built from label payloads."""
    registry = LabelRegistry()
    for payload in payloads:
        registry.add(label_from_dict(payload))
    registry.snapshot_hash = registry.compute_hash()
    return registry


def make_row(**overrides: object) -> EntityLabel:
    """Return an unsaved label row, overridable per test."""
    values: dict[str, object] = {
        "entity_name": "Example Exchange",
        "entity_type": EntityType.EXCHANGE.value,
        "chain": CHAIN,
        "address": "0x5555555555555555555555555555555555555555",
        "label_origin": "observed_label",
        "source_name": "Example public disclosure",
        "source_type": SourceType.REPUTABLE_SECONDARY.value,
        "source_reference": CITABLE_REFERENCE,
        "verification_level": VerificationLevel.LEVEL_2_REPUTABLE_SECONDARY.value,
        "observed_at": date(2025, 1, 1),
        "last_verified_at": date(2026, 1, 1),
        "scope_notes": "Applies to this address only.",
        "is_shared_infrastructure": False,
        "is_active": True,
    }
    values.update(overrides)
    return EntityLabel(**values)  # type: ignore[arg-type]


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    """Provide a session against a fresh in-memory database."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_maker() as open_session:
        yield open_session

    await engine.dispose()


# Planning


def test_an_empty_database_plans_a_creation_for_every_label() -> None:
    registry = make_registry(label_payload())

    plan = plan_sync(registry, [])

    assert len(plan.created) == 1
    assert plan.updated == []
    assert plan.deactivated == []
    assert plan.has_changes is True


def test_a_matching_label_is_reported_as_unchanged() -> None:
    registry = make_registry(label_payload())

    plan = plan_sync(registry, [make_row()])

    assert plan.unchanged
    assert plan.created == []
    assert plan.updated == []
    assert plan.has_changes is False


def test_a_changed_field_is_reported_as_an_update() -> None:
    registry = make_registry(label_payload(scope_notes="Updated scope note."))

    plan = plan_sync(registry, [make_row()])

    assert plan.updated
    _, changes = plan.updated[0]
    assert changes == {"scope_notes": "Updated scope note."}


def test_a_label_missing_from_the_registry_is_deactivated_not_deleted() -> None:
    plan = plan_sync(make_registry(), [make_row()])

    assert len(plan.deactivated) == 1
    assert plan.deactivated[0][1] == "0x5555555555555555555555555555555555555555"


def test_an_already_inactive_label_is_not_planned_for_deactivation_again() -> None:
    plan = plan_sync(make_registry(), [make_row(is_active=False)])

    assert plan.deactivated == []


def test_a_reactivated_registry_entry_is_planned_as_a_creation() -> None:
    plan = plan_sync(make_registry(label_payload()), [make_row(is_active=False)])

    assert len(plan.created) == 1


def test_the_plan_total_counts_every_kind_of_change() -> None:
    plan = plan_sync(make_registry(label_payload(scope_notes="Changed.")), [make_row()])

    assert plan.total_changes == len(plan.created) + len(plan.updated) + len(plan.deactivated)


def test_planning_is_deterministic_across_runs() -> None:
    registry = make_registry(label_payload())

    first = plan_sync(registry, [make_row()])
    second = plan_sync(registry, [make_row()])

    assert first == second


# Applying a plan


async def test_applying_a_plan_creates_rows_and_logs_the_creation(
    session: AsyncSession,
) -> None:
    plan = plan_sync(make_registry(label_payload()), [])

    counts = await apply_sync_plan(session, plan, ACTOR)
    await session.commit()

    assert counts == {"created": 1, "updated": 0, "deactivated": 0}
    logs = await _logs_of_type(session, "created")
    assert len(logs) == 1
    assert logs[0].changed_by == ACTOR
    assert logs[0].previous_value is None
    assert logs[0].new_value is not None


async def test_applying_a_plan_writes_every_change_to_the_log(
    session: AsyncSession,
) -> None:
    session.add(make_row())
    await session.commit()
    plan = plan_sync(make_registry(label_payload(scope_notes="Changed.")), [make_row()])

    counts = await apply_sync_plan(session, plan, ACTOR)
    await session.commit()

    assert counts["updated"] == 1
    logs = await _logs_of_type(session, "updated")
    assert len(logs) == 1
    assert logs[0].previous_value is not None
    assert logs[0].new_value is not None


async def test_deactivating_keeps_the_row_and_logs_the_change(
    session: AsyncSession,
) -> None:
    session.add(make_row())
    await session.commit()
    plan = plan_sync(make_registry(), [make_row(is_active=True)])

    counts = await apply_sync_plan(session, plan, ACTOR)
    await session.commit()

    assert counts["deactivated"] == 1
    logs = await _logs_of_type(session, "deactivated")
    assert len(logs) == 1
    assert logs[0].new_value["is_active"] is False
    stored = (await session.execute(_all_labels())).scalars().all()
    assert stored[0].is_active is False


# Add, update, deactivate


async def test_adding_a_label_stores_it_and_logs_the_creation(
    session: AsyncSession,
) -> None:
    record = label_from_dict(label_payload())

    row = await add_label(session, record, ACTOR)
    await session.commit()

    assert row.entity_name == "Example Exchange"
    logs = await _logs_of_type(session, "created")
    assert len(logs) == 1


async def test_adding_a_duplicate_label_is_refused(session: AsyncSession) -> None:
    record = label_from_dict(label_payload())
    await add_label(session, record, ACTOR)
    await session.commit()

    with pytest.raises(SeedError):
        await add_label(session, record, ACTOR)


async def test_updating_a_label_changes_it_and_logs_the_change(
    session: AsyncSession,
) -> None:
    await add_label(session, label_from_dict(label_payload()), ACTOR)
    await session.commit()

    row = await update_label(
        session,
        CHAIN,
        "0x5555555555555555555555555555555555555555",
        "Example public disclosure",
        {"scope_notes": "Narrowed scope."},
        ACTOR,
    )
    await session.commit()

    assert row.scope_notes == "Narrowed scope."
    logs = await _logs_of_type(session, "updated")
    assert len(logs) == 1
    assert logs[0].previous_value["scope_notes"] == "Applies to this address only."
    assert logs[0].new_value["scope_notes"] == "Narrowed scope."


async def test_updating_an_unknown_label_is_refused(session: AsyncSession) -> None:
    with pytest.raises(SeedError):
        await update_label(
            session,
            CHAIN,
            "0x9999999999999999999999999999999999999999",
            "Example public disclosure",
            {"scope_notes": "Nothing to update."},
            ACTOR,
        )


async def test_updating_an_immutable_field_is_refused(session: AsyncSession) -> None:
    await add_label(session, label_from_dict(label_payload()), ACTOR)
    await session.commit()

    with pytest.raises(SeedError):
        await update_label(
            session,
            CHAIN,
            "0x5555555555555555555555555555555555555555",
            "Example public disclosure",
            {"address": "0x9999999999999999999999999999999999999999"},
            ACTOR,
        )


async def test_updating_with_no_fields_is_refused(session: AsyncSession) -> None:
    await add_label(session, label_from_dict(label_payload()), ACTOR)
    await session.commit()

    with pytest.raises(SeedError):
        await update_label(
            session,
            CHAIN,
            "0x5555555555555555555555555555555555555555",
            "Example public disclosure",
            {},
            ACTOR,
        )


async def test_a_deactivated_label_cannot_be_updated(session: AsyncSession) -> None:
    await add_label(session, label_from_dict(label_payload()), ACTOR)
    await session.commit()
    await deactivate_label(
        session,
        CHAIN,
        "0x5555555555555555555555555555555555555555",
        "Example public disclosure",
        ACTOR,
    )
    await session.commit()

    with pytest.raises(SeedError):
        await update_label(
            session,
            CHAIN,
            "0x5555555555555555555555555555555555555555",
            "Example public disclosure",
            {"scope_notes": "Narrowed scope."},
            ACTOR,
        )


async def test_deactivating_twice_is_refused(session: AsyncSession) -> None:
    await add_label(session, label_from_dict(label_payload()), ACTOR)
    await session.commit()
    await deactivate_label(
        session,
        CHAIN,
        "0x5555555555555555555555555555555555555555",
        "Example public disclosure",
        ACTOR,
    )
    await session.commit()

    with pytest.raises(SeedError):
        await deactivate_label(
            session,
            CHAIN,
            "0x5555555555555555555555555555555555555555",
            "Example public disclosure",
            ACTOR,
        )


async def test_the_change_log_records_who_and_when(session: AsyncSession) -> None:
    before = datetime.now(UTC).replace(tzinfo=None)
    await add_label(session, label_from_dict(label_payload()), "first_operator")
    await session.commit()

    logs = await _logs_of_type(session, "created")

    assert logs[0].changed_by == "first_operator"
    # SQLite does not retain the timezone, so compare in UTC wall clock terms.
    assert before <= logs[0].changed_at <= before + timedelta(seconds=30)


async def test_a_second_run_after_a_sync_makes_no_changes(
    session: AsyncSession,
) -> None:
    registry = make_registry(label_payload())
    await apply_sync_plan(session, plan_sync(registry, []), ACTOR)
    await session.commit()

    stored = (await session.execute(_all_labels())).scalars().all()
    second = plan_sync(registry, list(stored))

    assert second.has_changes is False


# Label file reading


def test_reading_a_valid_label_file_returns_a_record(tmp_path: Path) -> None:
    path = tmp_path / "label.json"
    path.write_text(json.dumps(label_payload()), encoding="utf-8")

    record = read_label_file(path)

    assert record.entity_name == "Example Exchange"


def test_reading_an_invalid_json_file_is_reported(tmp_path: Path) -> None:
    path = tmp_path / "label.json"
    path.write_text("{not json", encoding="utf-8")

    with pytest.raises(SeedError) as excinfo:
        read_label_file(path)

    assert "not valid JSON" in str(excinfo.value)


def test_reading_a_missing_file_is_reported(tmp_path: Path) -> None:
    with pytest.raises(SeedError) as excinfo:
        read_label_file(tmp_path / "absent.json")

    assert "could not be read" in str(excinfo.value)


def test_reading_a_file_that_is_not_an_object_is_reported(tmp_path: Path) -> None:
    path = tmp_path / "label.json"
    path.write_text(json.dumps([label_payload()]), encoding="utf-8")

    with pytest.raises(SeedError) as excinfo:
        read_label_file(path)

    assert "single label object" in str(excinfo.value)


def test_reading_a_file_that_is_not_a_valid_label_is_reported(tmp_path: Path) -> None:
    path = tmp_path / "label.json"
    path.write_text(json.dumps({"entity_name": "Incomplete"}), encoding="utf-8")

    with pytest.raises(SeedError) as excinfo:
        read_label_file(path)

    assert "not a valid label" in str(excinfo.value)


# Command line parsing


def test_the_parser_defaults_to_sync() -> None:
    args = build_parser().parse_args([])

    assert args.command is None
    assert args.dry_run is False
    assert args.actor


def test_the_parser_accepts_a_dry_run() -> None:
    args = build_parser().parse_args(["--dry-run"])

    assert args.dry_run is True


def test_the_parser_accepts_field_value_pairs() -> None:
    args = build_parser().parse_args(
        [
            "update",
            "--chain",
            CHAIN,
            "--address",
            "0x5555555555555555555555555555555555555555",
            "--source-name",
            "Example public disclosure",
            "--set",
            "scope_notes=Narrowed scope.",
            "--set",
            "last_verified_at=2026-02-01",
        ]
    )

    assert args.changes == ["scope_notes=Narrowed scope.", "last_verified_at=2026-02-01"]


def test_a_date_change_is_parsed_into_a_date() -> None:
    parsed = _parse_changes(["last_verified_at=2026-02-01"])

    assert parsed == {"last_verified_at": date(2026, 2, 1)}


def test_a_boolean_change_is_parsed_into_a_boolean() -> None:
    parsed = _parse_changes(["is_shared_infrastructure=true"])

    assert parsed == {"is_shared_infrastructure": True}


def test_an_invalid_date_change_is_refused() -> None:
    with pytest.raises(SeedError):
        _parse_changes(["last_verified_at=01-02-2026"])


def test_an_invalid_boolean_change_is_refused() -> None:
    with pytest.raises(SeedError):
        _parse_changes(["is_shared_infrastructure=maybe"])


def test_a_change_without_an_equals_sign_is_refused() -> None:
    with pytest.raises(SeedError):
        _parse_changes(["scope_notes"])


def test_no_changes_parse_to_an_empty_mapping() -> None:
    assert _parse_changes(None) == {}


# Registry integration


def test_the_shipped_registry_plans_creations_into_an_empty_database(
    label_registry_dir: Path,
) -> None:
    registry = load_registry(label_registry_dir, is_demo=True)

    plan = plan_sync(registry, [])

    assert len(plan.created) == registry.total_labels()
    assert plan.updated == []
    assert plan.deactivated == []


async def test_seeding_the_shipped_registry_twice_is_idempotent(
    session: AsyncSession, label_registry_dir: Path
) -> None:
    registry = load_registry(label_registry_dir, is_demo=True)
    await apply_sync_plan(session, plan_sync(registry, []), ACTOR)
    await session.commit()

    stored = (await session.execute(_all_labels())).scalars().all()
    second_plan = plan_sync(registry, list(stored))

    assert second_plan.has_changes is False
    assert second_plan.total_changes == 0


# Command dispatch


def _settings(**overrides: object) -> Settings:
    """Return settings with the registry directory pointed at ``tmp_path``."""
    values: dict[str, object] = {
        "DEMO_MODE": True,
        "ALLOW_SYNTHETIC_LABELS": True,
        "CHAIN_DEFAULT": CHAIN,
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


@pytest.fixture
def registry_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Write a registry file into a temporary directory and point settings at it."""
    directory = tmp_path / "label_registry"
    directory.mkdir()
    payload = {"labels": [label_payload()]}
    (directory / "entities.json").write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(seed_module, "default_registry_dir", lambda: directory)
    return directory


async def test_a_sync_creates_the_labels_from_the_registry_files(
    session: AsyncSession, registry_dir: Path
) -> None:
    exit_code = await seed_module.run_sync(session, _settings(), ACTOR, dry_run=False)

    assert exit_code == 0
    stored = (await session.execute(_all_labels())).scalars().all()
    assert len(stored) == 1


async def test_a_dry_run_writes_nothing(
    session: AsyncSession, registry_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = await seed_module.run_sync(session, _settings(), ACTOR, dry_run=True)

    assert exit_code == 0
    stored = (await session.execute(_all_labels())).scalars().all()
    assert stored == []
    assert "Dry run" in capsys.readouterr().out


async def test_a_second_sync_reports_no_changes(
    session: AsyncSession, registry_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    await seed_module.run_sync(session, _settings(), ACTOR, dry_run=False)

    exit_code = await seed_module.run_sync(session, _settings(), ACTOR, dry_run=False)

    assert exit_code == 0
    assert "No changes" in capsys.readouterr().out


async def test_a_sync_outside_demo_mode_skips_synthetic_labels(
    session: AsyncSession, registry_dir: Path
) -> None:
    synthetic = label_payload(
        entity_type=EntityType.EXCHANGE_DEPOSIT_ADDRESS.value,
        source_type=SourceType.SYNTHETIC.value,
        verification_level=VerificationLevel.LEVEL_0_SYNTHETIC.value,
        source_reference="https://example.invalid/trace-x/demo-label/test",
    )
    payload = {"labels": [synthetic]}
    (registry_dir / "synthetic.json").write_text(json.dumps(payload), encoding="utf-8")

    await seed_module.run_sync(
        session, _settings(DEMO_MODE=False, ALLOW_SYNTHETIC_LABELS=False), ACTOR, dry_run=False
    )

    stored = (await session.execute(_all_labels())).scalars().all()
    assert [row.source_name for row in stored] == ["Example public disclosure"]


async def test_the_sync_command_dispatches_without_a_subcommand(
    session: AsyncSession, registry_dir: Path
) -> None:
    args = build_parser().parse_args(["--actor", ACTOR, "sync"])

    exit_code = await seed_module.run_command(args, session)

    assert exit_code == 0


async def test_the_add_command_refuses_a_synthetic_label_when_not_allowed(
    session: AsyncSession, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        seed_module,
        "get_settings",
        lambda: _settings(DEMO_MODE=False, ALLOW_SYNTHETIC_LABELS=False),
    )
    path = tmp_path / "label.json"
    path.write_text(
        json.dumps(
            label_payload(
                source_type=SourceType.SYNTHETIC.value,
                verification_level=VerificationLevel.LEVEL_0_SYNTHETIC.value,
                source_reference="https://example.invalid/trace-x/demo-label/test",
            )
        ),
        encoding="utf-8",
    )
    args = build_parser().parse_args(["add", str(path)])

    with pytest.raises(SeedError):
        await seed_module.run_command(args, session)


async def test_the_add_command_stores_a_valid_label(
    session: AsyncSession, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(seed_module, "get_settings", lambda: _settings())
    path = tmp_path / "label.json"
    path.write_text(json.dumps(label_payload()), encoding="utf-8")
    args = build_parser().parse_args(["--actor", ACTOR, "add", str(path)])

    exit_code = await seed_module.run_command(args, session)

    assert exit_code == 0
    stored = (await session.execute(_all_labels())).scalars().all()
    assert len(stored) == 1


async def test_the_update_command_applies_a_change(
    session: AsyncSession, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(seed_module, "get_settings", lambda: _settings())
    path = tmp_path / "label.json"
    path.write_text(json.dumps(label_payload()), encoding="utf-8")
    await seed_module.run_command(build_parser().parse_args(["add", str(path)]), session)

    args = build_parser().parse_args(
        [
            "update",
            "--chain",
            CHAIN,
            "--address",
            "0x5555555555555555555555555555555555555555",
            "--source-name",
            "Example public disclosure",
            "--set",
            "scope_notes=Narrowed scope.",
        ]
    )
    exit_code = await seed_module.run_command(args, session)

    assert exit_code == 0
    stored = (await session.execute(_all_labels())).scalars().all()
    assert stored[0].scope_notes == "Narrowed scope."


async def test_the_deactivate_command_marks_a_label_inactive(
    session: AsyncSession, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(seed_module, "get_settings", lambda: _settings())
    path = tmp_path / "label.json"
    path.write_text(json.dumps(label_payload()), encoding="utf-8")
    await seed_module.run_command(build_parser().parse_args(["add", str(path)]), session)

    args = build_parser().parse_args(
        [
            "deactivate",
            "--chain",
            CHAIN,
            "--address",
            "0x5555555555555555555555555555555555555555",
            "--source-name",
            "Example public disclosure",
        ]
    )
    exit_code = await seed_module.run_command(args, session)

    assert exit_code == 0
    stored = (await session.execute(_all_labels())).scalars().all()
    assert stored[0].is_active is False


def _all_labels():
    """Return a select statement for every stored label."""
    return select(EntityLabel)


async def _logs_of_type(session: AsyncSession, change_type: str) -> list[LabelChangeLog]:
    """Return the change log entries of one type, oldest first."""
    result = await session.execute(
        select(LabelChangeLog).where(LabelChangeLog.change_type == change_type)
    )
    return sorted(result.scalars().all(), key=lambda entry: entry.changed_at)

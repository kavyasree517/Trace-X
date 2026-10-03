"""Administrative label management.

Three operations are supported:

* ``sync`` reads the JSON files under ``backend/data/label_registry`` and brings
  the ``entity_labels`` table into line with them, creating, updating or
  deactivating rows as needed.
* ``add`` inserts a single label from a JSON file that must pass the same
  validation the registry applies.
* ``update`` changes the fields of one existing label.
* ``deactivate`` marks a label inactive without deleting it, so that historical
  reports keep pointing at a real row.

Every change writes a row to ``label_change_log`` recording the previous and
new values, so that the state of the registry at any past moment can be
reconstructed.

Synthetic labels are refused unless demonstration mode is enabled. A synthetic
address must never reach a report that claims to describe a real investigation.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.attribution.registry import (
    EntityLabelRecord,
    LabelRegistry,
    default_registry_dir,
    label_from_dict,
    load_registry,
)
from app.core.config import Settings, get_settings
from app.core.logging import get_logger, setup_logging
from app.models.label import EntityLabel, LabelChangeLog

logger = get_logger("app.attribution.seed")

DEFAULT_ACTOR = "seed_cli"

# Fields that are stored on the label row and may be changed by an update.
_UPDATABLE_FIELDS = (
    "entity_name",
    "entity_type",
    "label_origin",
    "source_type",
    "source_reference",
    "verification_level",
    "cluster_id",
    "observed_at",
    "last_verified_at",
    "scope_notes",
    "is_shared_infrastructure",
)


class SeedError(RuntimeError):
    """Raised when a label operation cannot be completed as requested."""


# A label is identified by chain, canonical address and source name.
LabelKey = tuple[str, str, str]


@dataclass
class LabelSyncPlan:
    """Difference between the registry files and the stored labels."""

    created: list[EntityLabelRecord] = field(default_factory=list)
    updated: list[tuple[LabelKey, dict[str, Any]]] = field(default_factory=list)
    deactivated: list[LabelKey] = field(default_factory=list)
    unchanged: list[LabelKey] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.created or self.updated or self.deactivated)

    @property
    def total_changes(self) -> int:
        return len(self.created) + len(self.updated) + len(self.deactivated)


def record_to_payload(record: EntityLabelRecord) -> dict[str, Any]:
    """Return the stored field values of a label as a comparable payload."""
    return {
        "entity_name": record.entity_name,
        "entity_type": record.entity_type,
        "chain": record.chain,
        "address": record.address,
        "label_origin": record.label_origin,
        "source_name": record.source_name,
        "source_type": record.source_type,
        "source_reference": record.source_reference,
        "verification_level": record.verification_level,
        "cluster_id": record.cluster_id,
        "observed_at": record.observed_at,
        "last_verified_at": record.last_verified_at,
        "scope_notes": record.scope_notes,
        "is_shared_infrastructure": record.is_shared_infrastructure,
        "is_active": record.is_active,
    }


def row_to_payload(row: EntityLabel) -> dict[str, Any]:
    """Return the stored field values of a database row as a payload."""
    return {
        "entity_name": row.entity_name,
        "entity_type": row.entity_type,
        "chain": row.chain,
        "address": row.address,
        "label_origin": row.label_origin,
        "source_name": row.source_name,
        "source_type": row.source_type,
        "source_reference": row.source_reference,
        "verification_level": row.verification_level,
        "cluster_id": row.cluster_id,
        "observed_at": row.observed_at,
        "last_verified_at": row.last_verified_at,
        "scope_notes": row.scope_notes,
        "is_shared_infrastructure": row.is_shared_infrastructure,
        "is_active": row.is_active,
    }


def _identify(payload: dict[str, Any]) -> LabelKey:
    return (
        str(payload["chain"]),
        str(payload["address"]),
        str(payload["source_name"]),
    )


def _find_row(rows: list[EntityLabel], key: LabelKey) -> EntityLabel | None:
    """Return the stored row matching an identifying key, if any."""
    return next(
        (row for row in rows if _identify(row_to_payload(row)) == key),
        None,
    )


def _render(key: LabelKey) -> str:
    """Return an identifying key in a readable form for messages."""
    return f"{key[0]} {key[1]} ({key[2]})"


def _row_fields(row: EntityLabel) -> dict[str, Any]:
    """Return only the fields an update may change."""
    payload = row_to_payload(row)
    return {name: payload[name] for name in _UPDATABLE_FIELDS}


def plan_sync(registry: LabelRegistry, rows: list[EntityLabel]) -> LabelSyncPlan:
    """Compare registry entries against stored rows and return the difference.

    Rows that are absent from the registry files are deactivated rather than
    deleted, so that reports already generated continue to resolve.
    """
    plan = LabelSyncPlan()
    stored = {_identify(row_to_payload(row)): row for row in rows}
    seen: set[LabelKey] = set()

    for chain_address in sorted(registry.labels):
        for record in registry.labels[chain_address]:
            key = _identify(record_to_payload(record))
            seen.add(key)
            existing = stored.get(key)

            if existing is None or not existing.is_active:
                plan.created.append(record)
                continue

            changes = {
                name: value
                for name, value in record_to_payload(record).items()
                if name in _UPDATABLE_FIELDS and value != getattr(existing, name)
            }
            if changes:
                plan.updated.append((key, changes))
            else:
                plan.unchanged.append(key)

    for key, row in sorted(stored.items()):
        if key in seen or not row.is_active:
            continue
        plan.deactivated.append(key)

    return plan


async def load_existing_rows(session: AsyncSession) -> list[EntityLabel]:
    """Return every stored label row."""
    result = await session.execute(select(EntityLabel))
    return list(result.scalars().all())


def _json_safe(value: Any) -> Any:
    """Return a JSON serialisable copy of a label payload.

    Dates are stored as ISO 8601 strings so that a change log row can be read
    back without knowing the column types of the source table.
    """
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, date):
        return value.isoformat()
    return value


async def _write_change_log(
    session: AsyncSession,
    label_id: Any,
    change_type: str,
    actor: str,
    previous: dict[str, Any] | None,
    new: dict[str, Any] | None,
    changed_at: datetime,
) -> None:
    """Record one label change so the registry history stays reconstructable."""
    session.add(
        LabelChangeLog(
            label_id=label_id,
            change_type=change_type,
            changed_at=changed_at,
            changed_by=actor,
            previous_value=_json_safe(previous) if previous is not None else None,
            new_value=_json_safe(new) if new is not None else None,
        )
    )


async def _insert_label(
    session: AsyncSession, record: EntityLabelRecord, actor: str, changed_at: datetime
) -> None:
    row = EntityLabel(
        entity_name=record.entity_name,
        entity_type=record.entity_type,
        chain=record.chain,
        address=record.address,
        cluster_id=record.cluster_id,
        label_origin=record.label_origin,
        source_name=record.source_name,
        source_type=record.source_type,
        source_reference=record.source_reference,
        verification_level=record.verification_level,
        observed_at=record.observed_at,
        last_verified_at=record.last_verified_at,
        scope_notes=record.scope_notes,
        is_shared_infrastructure=record.is_shared_infrastructure,
        is_active=record.is_active,
    )
    session.add(row)
    await session.flush()
    await _write_change_log(
        session,
        row.id,
        "created",
        actor,
        previous=None,
        new=row_to_payload(row),
        changed_at=changed_at,
    )


async def apply_sync_plan(session: AsyncSession, plan: LabelSyncPlan, actor: str) -> dict[str, int]:
    """Write a sync plan to the database and return the counts applied."""
    changed_at = datetime.now(UTC)
    counts = {"created": 0, "updated": 0, "deactivated": 0}

    for record in plan.created:
        await _insert_label(session, record, actor, changed_at)
        counts["created"] += 1

    rows = await load_existing_rows(session)

    for key, changes in plan.updated:
        row = _find_row(rows, key)
        if row is None:
            raise SeedError(f"Cannot update a label that is not stored: {_render(key)}")
        previous = _row_fields(row)
        for name, value in changes.items():
            setattr(row, name, value)
        await session.flush()
        await _write_change_log(
            session,
            row.id,
            "updated",
            actor,
            previous=previous,
            new={**previous, **changes},
            changed_at=changed_at,
        )
        counts["updated"] += 1

    for key in plan.deactivated:
        row = _find_row(rows, key)
        if row is None:
            raise SeedError(f"Cannot deactivate a label that is not stored: {_render(key)}")
        previous = _row_fields(row)
        row.is_active = False
        await session.flush()
        await _write_change_log(
            session,
            row.id,
            "deactivated",
            actor,
            previous=previous,
            new={**previous, "is_active": False},
            changed_at=changed_at,
        )
        counts["deactivated"] += 1

    return counts


async def add_label(session: AsyncSession, record: EntityLabelRecord, actor: str) -> EntityLabel:
    """Insert one label and log the creation."""
    existing = await load_existing_rows(session)
    keys = {_identify(row_to_payload(row)) for row in existing}
    key = _identify(record_to_payload(record))
    if key in keys:
        raise SeedError(f"Label already exists: {_render(key)}")

    await _insert_label(session, record, actor, datetime.now(UTC))
    result = await session.execute(
        select(EntityLabel).where(
            EntityLabel.chain == record.chain,
            EntityLabel.address == record.address,
            EntityLabel.source_name == record.source_name,
        )
    )
    row = result.scalar_one()
    return row


async def update_label(
    session: AsyncSession,
    chain: str,
    address: str,
    source_name: str,
    changes: dict[str, Any],
    actor: str,
) -> EntityLabel:
    """Apply field changes to one stored label and log them."""
    unknown = sorted(set(changes) - set(_UPDATABLE_FIELDS))
    if unknown:
        raise SeedError(f"Fields cannot be updated: {', '.join(unknown)}")
    if not changes:
        raise SeedError("No fields were given to update")

    rows = await load_existing_rows(session)
    key = _identify({"chain": chain, "address": address, "source_name": source_name})
    row = _find_row(rows, key)
    if row is None:
        raise SeedError(f"Label not found: {_render(key)}")
    if not row.is_active:
        raise SeedError(f"Label is deactivated and cannot be updated: {_render(key)}")

    previous = _row_fields(row)
    for name, value in changes.items():
        setattr(row, name, value)
    await session.flush()
    await _write_change_log(
        session,
        row.id,
        "updated",
        actor,
        previous=previous,
        new={**previous, **changes},
        changed_at=datetime.now(UTC),
    )
    return row


async def deactivate_label(
    session: AsyncSession,
    chain: str,
    address: str,
    source_name: str,
    actor: str,
) -> EntityLabel:
    """Mark one label inactive and log the deactivation."""
    rows = await load_existing_rows(session)
    key = _identify({"chain": chain, "address": address, "source_name": source_name})
    row = _find_row(rows, key)
    if row is None:
        raise SeedError(f"Label not found: {_render(key)}")
    if not row.is_active:
        raise SeedError(f"Label is already deactivated: {_render(key)}")

    previous = _row_fields(row)
    row.is_active = False
    await session.flush()
    await _write_change_log(
        session,
        row.id,
        "deactivated",
        actor,
        previous=previous,
        new={**previous, "is_active": False},
        changed_at=datetime.now(UTC),
    )
    return row


def read_label_file(path: Path) -> EntityLabelRecord:
    """Load and validate one label from a JSON file."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SeedError(f"{path.name} is not valid JSON: {exc.msg}") from exc
    except OSError as exc:
        raise SeedError(f"{path.name} could not be read: {exc.strerror}") from exc

    if not isinstance(payload, dict):
        raise SeedError(f"{path.name} must contain a single label object")
    try:
        return label_from_dict(payload)
    except ValueError as exc:
        raise SeedError(f"{path.name} is not a valid label: {exc}") from exc


def _parse_changes(values: list[str] | None) -> dict[str, Any]:
    """Parse ``field=value`` command line pairs into typed values."""
    changes: dict[str, Any] = {}
    for item in values or []:
        if "=" not in item:
            raise SeedError(f"Changes must be given as field=value, received: {item}")
        field, _, raw = item.partition("=")
        name = field.strip()
        if name in ("observed_at", "last_verified_at"):
            try:
                changes[name] = date.fromisoformat(raw.strip())
            except ValueError as exc:
                raise SeedError(f"{name} must be an ISO 8601 date: {raw}") from exc
        elif name == "is_shared_infrastructure":
            lowered = raw.strip().lower()
            if lowered not in ("true", "false"):
                raise SeedError(f"{name} must be true or false, received: {raw}")
            changes[name] = lowered == "true"
        else:
            changes[name] = raw
    return changes


def build_parser() -> argparse.ArgumentParser:
    """Return the command line parser for label administration.

    The shared options are attached to every subcommand as well as the top
    level, so that ``seed --actor x sync`` and ``seed sync --actor x`` both
    work. A value given after the subcommand wins.
    """
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument(
        "--actor",
        default=argparse.SUPPRESS,
        help="Recorded as changed_by in the change log.",
    )
    shared.add_argument(
        "--dry-run",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Report what a sync would change without writing anything.",
    )

    parser = argparse.ArgumentParser(
        prog="python -m app.attribution.seed",
        parents=[shared],
        description="Add, update and deactivate entity labels with a change log.",
    )
    parser.set_defaults(actor=DEFAULT_ACTOR, dry_run=False)

    subcommands = parser.add_subparsers(dest="command")
    subcommands.add_parser(
        "sync", parents=[shared], help="Apply the registry files to the database."
    )

    add_parser = subcommands.add_parser(
        "add", parents=[shared], help="Add one label from a JSON file."
    )
    add_parser.add_argument("file", type=Path, help="Path to the label JSON file.")

    update_parser = subcommands.add_parser(
        "update", parents=[shared], help="Update one stored label."
    )
    update_parser.add_argument("--chain", required=True)
    update_parser.add_argument("--address", required=True)
    update_parser.add_argument("--source-name", required=True)
    update_parser.add_argument(
        "--set",
        action="append",
        dest="changes",
        metavar="FIELD=VALUE",
        help="Field to change. May be repeated.",
    )

    deactivate_parser = subcommands.add_parser(
        "deactivate", parents=[shared], help="Deactivate one stored label."
    )
    deactivate_parser.add_argument("--chain", required=True)
    deactivate_parser.add_argument("--address", required=True)
    deactivate_parser.add_argument("--source-name", required=True)

    return parser


async def run_sync(session: AsyncSession, settings: Settings, actor: str, dry_run: bool) -> int:
    """Synchronise the registry files into the database."""
    directory = default_registry_dir()
    registry = load_registry(
        directory, is_demo=settings.DEMO_MODE, chain_default=settings.CHAIN_DEFAULT
    )
    if registry.load_errors:
        for error in registry.load_errors:
            logger.warning("registry_entry_rejected", detail=error)

    plan = plan_sync(registry, await load_existing_rows(session))

    if not plan.has_changes:
        logger.info(
            "label_sync_no_changes",
            registry_dir=str(directory),
            registry_hash=registry.snapshot_hash,
            unchanged=len(plan.unchanged),
        )
        print(f"No changes. {len(plan.unchanged)} labels already match the registry.")
        return 0

    if dry_run:
        print(
            f"Dry run. Would create {len(plan.created)}, "
            f"update {len(plan.updated)}, deactivate {len(plan.deactivated)} labels."
        )
        for record in plan.created:
            print(f"  create     {record.entity_name} ({record.address})")
        for key, _ in plan.updated:
            print(f"  update     {_render(key)}")
        for key in plan.deactivated:
            print(f"  deactivate {_render(key)}")
        return 0

    counts = await apply_sync_plan(session, plan, actor)
    await session.commit()
    logger.info(
        "label_sync_completed",
        registry_dir=str(directory),
        registry_hash=registry.snapshot_hash,
        actor=actor,
        **counts,
    )
    print(
        f"Created {counts['created']}, updated {counts['updated']}, "
        f"deactivated {counts['deactivated']} labels. "
        f"Registry hash {registry.snapshot_hash}."
    )
    return 0


async def run_command(args: argparse.Namespace, session: AsyncSession) -> int:
    """Dispatch one parsed command against the database."""
    settings = get_settings()
    actor = str(args.actor)
    command = args.command or "sync"

    if command == "sync":
        return await run_sync(session, settings, actor, bool(args.dry_run))

    if command == "add":
        record = read_label_file(args.file)
        if record.is_synthetic and not settings.ALLOW_SYNTHETIC_LABELS:
            raise SeedError(
                "Synthetic labels require ALLOW_SYNTHETIC_LABELS and DEMO_MODE to be enabled."
            )
        row = await add_label(session, record, actor)
        await session.commit()
        logger.info("label_created", address=row.address, actor=actor, chain=row.chain)
        print(f"Added {row.entity_name} at {row.address}.")
        return 0

    if command == "update":
        changes = _parse_changes(args.changes)
        row = await update_label(
            session, args.chain, args.address, args.source_name, changes, actor
        )
        await session.commit()
        changed = ", ".join(sorted(changes))
        logger.info("label_updated", address=row.address, actor=actor, chain=row.chain)
        print(f"Updated {changed} for {row.entity_name} at {row.address}.")
        return 0

    row = await deactivate_label(session, args.chain, args.address, args.source_name, actor)
    await session.commit()
    logger.info("label_deactivated", address=row.address, actor=actor, chain=row.chain)
    print(f"Deactivated {row.entity_name} at {row.address}.")
    return 0


async def _amain(argv: list[str] | None = None) -> int:
    """Run the command line tool and return its exit code."""
    from app.api.deps import get_session_maker

    settings = get_settings()
    setup_logging(settings.LOG_LEVEL)

    args = build_parser().parse_args(argv)
    session_maker = get_session_maker()

    try:
        async with session_maker() as session:
            return await run_command(args, session)
    except SeedError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        logger.error("seed_command_failed", error=str(exc))
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def main() -> None:
    """Entry point used by ``make seed``."""
    raise SystemExit(asyncio.run(_amain()))


if __name__ == "__main__":
    main()

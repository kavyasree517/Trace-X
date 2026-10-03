"""Entity label registry loaded from versioned JSON files.

Registry files live in ``backend/data/label_registry``. Each label must carry
a citable source name and reference. A label without a public reference and an
observed date is rejected at load time rather than being silently accepted,
because an unverifiable label cannot be shown with its provenance.

Synthetic labels are permitted only in demonstration mode.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from app.core.enums import (
    EntityType,
    LabelOrigin,
    SourceType,
    VerificationLevel,
)
from app.core.security import canonicalize_address

_SYNTHETIC = VerificationLevel.LEVEL_0_SYNTHETIC.value
# Synthetic labels are citable only within TRACE-X's own demonstration
# fixtures, identified by an example.invalid reference. Every other source
# type in the controlled vocabulary must point at a public URL.
_SYNTHETIC_REFERENCE_PREFIX = "https://example.invalid/"


class LabelRegistryError(ValueError):
    """Raised when a registry entry fails validation."""


@dataclass(frozen=True)
class EntityLabelRecord:
    """One registry entry with the complete P7 provenance field set."""

    entity_name: str
    entity_type: str
    chain: str
    address: str
    label_origin: str
    source_name: str
    source_type: str
    source_reference: str
    verification_level: str
    cluster_id: str | None = None
    observed_at: date | None = None
    last_verified_at: date | None = None
    scope_notes: str | None = None
    is_shared_infrastructure: bool = False
    is_active: bool = True
    notes: str | None = None

    @property
    def is_synthetic(self) -> bool:
        return self.verification_level == _SYNTHETIC

    @property
    def verification_rank(self) -> int:
        """Return a numeric rank so the strongest of several labels can be picked."""
        order = {
            VerificationLevel.LEVEL_3_PRIMARY_SOURCE.value: 3,
            VerificationLevel.LEVEL_2_REPUTABLE_SECONDARY.value: 2,
            VerificationLevel.LEVEL_1_COMMUNITY_OR_UNVERIFIED.value: 1,
            VerificationLevel.LEVEL_0_SYNTHETIC.value: 0,
        }
        return order.get(self.verification_level, 0)


def _parse_date(value: Any, field_name: str) -> date | None:
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise LabelRegistryError(f"{field_name} is not an ISO 8601 date: {value}") from exc


def label_from_dict(payload: dict[str, Any], chain_default: str = "ethereum") -> EntityLabelRecord:
    """Validate one registry payload and return a label record."""
    required = (
        "entity_name",
        "entity_type",
        "address",
        "source_name",
        "source_type",
        "source_reference",
        "verification_level",
    )
    missing = [key for key in required if not payload.get(key)]
    if missing:
        raise LabelRegistryError(f"Label entry missing required fields: {', '.join(missing)}")

    verification = str(payload["verification_level"])
    if verification not in {level.value for level in VerificationLevel}:
        raise LabelRegistryError(f"Unknown verification level: {verification}")

    source_type = str(payload["source_type"])
    if source_type not in {value.value for value in SourceType}:
        raise LabelRegistryError(f"Unknown source type: {source_type}")

    entity_type = str(payload["entity_type"])
    if entity_type not in {value.value for value in EntityType}:
        raise LabelRegistryError(f"Unknown entity type: {entity_type}")

    try:
        address = canonicalize_address(str(payload["address"]))
    except ValueError as exc:
        raise LabelRegistryError(f"Invalid label address: {payload['address']}") from exc

    reference = str(payload["source_reference"])
    if not reference.startswith(("http://", "https://")):
        raise LabelRegistryError(
            f"Source reference must be a URL so the label can be verified: {reference}"
        )

    if source_type == SourceType.SYNTHETIC.value and not reference.startswith(
        _SYNTHETIC_REFERENCE_PREFIX
    ):
        raise LabelRegistryError(
            "Synthetic labels must reference a TRACE-X demonstration fixture under "
            f"{_SYNTHETIC_REFERENCE_PREFIX}, not an external claim."
        )

    observed_at = _parse_date(payload.get("observed_at"), "observed_at")
    last_verified_at = _parse_date(payload.get("last_verified_at"), "last_verified_at")

    if verification != _SYNTHETIC and last_verified_at is None:
        raise LabelRegistryError(
            "Non-synthetic labels require last_verified_at so label freshness can be assessed."
        )

    return EntityLabelRecord(
        entity_name=str(payload["entity_name"]),
        entity_type=entity_type,
        chain=str(payload.get("chain", chain_default)),
        address=address,
        label_origin=str(payload.get("label_origin", LabelOrigin.OBSERVED_LABEL.value)),
        source_name=str(payload["source_name"]),
        source_type=source_type,
        source_reference=reference,
        verification_level=verification,
        cluster_id=payload.get("cluster_id"),
        observed_at=observed_at,
        last_verified_at=last_verified_at,
        scope_notes=payload.get("scope_notes"),
        is_shared_infrastructure=bool(payload.get("is_shared_infrastructure", False)),
        is_active=bool(payload.get("is_active", True)),
        notes=payload.get("notes"),
    )


@dataclass
class LabelRegistry:
    """In-memory index of labels keyed by chain and canonical address."""

    labels: dict[tuple[str, str], list[EntityLabelRecord]] = field(default_factory=dict)
    snapshot_hash: str = ""
    load_errors: list[str] = field(default_factory=list)

    def add(self, record: EntityLabelRecord) -> None:
        key = (record.chain, record.address)
        self.labels.setdefault(key, []).append(record)

    def lookup(self, chain: str, address: str) -> list[EntityLabelRecord]:
        """Return active labels for an address, strongest verification first."""
        try:
            canonical = canonicalize_address(address)
        except ValueError:
            return []

        found = [label for label in self.labels.get((chain, canonical), []) if label.is_active]
        return sorted(found, key=lambda label: (-label.verification_rank, label.source_name))

    def entity_types_for(self, chain: str, address: str) -> set[str]:
        """Return the set of entity types recorded for an address."""
        return {label.entity_type for label in self.lookup(chain, address)}

    def shared_infrastructure_addresses(self, chain: str) -> set[str]:
        """Return addresses flagged as possibly shared infrastructure."""
        return {
            address
            for (label_chain, address), labels in self.labels.items()
            if label_chain == chain
            and any(label.is_shared_infrastructure for label in labels)
            and any(label.is_active for label in labels)
        }

    def total_labels(self) -> int:
        return sum(len(entries) for entries in self.labels.values())

    def sources_for(self, chain: str, address: str) -> set[str]:
        """Return distinct source names backing a label, for independence counting."""
        return {label.source_name for label in self.lookup(chain, address)}

    def compute_hash(self) -> str:
        """Return a stable SHA-256 hash of the registry contents."""
        digest = hashlib.sha256()
        for chain, address in sorted(self.labels):
            for label in sorted(self.labels[(chain, address)], key=lambda item: item.source_name):
                digest.update(
                    "|".join(
                        [
                            chain,
                            address,
                            label.entity_name,
                            label.entity_type,
                            label.source_name,
                            label.source_reference,
                            label.verification_level,
                            str(label.last_verified_at),
                        ]
                    ).encode("utf-8")
                )
                digest.update(b"\n")
        return digest.hexdigest()


def load_registry(
    directory: Path,
    is_demo: bool = True,
    chain_default: str = "ethereum",
) -> LabelRegistry:
    """Load every JSON label file in a directory into a registry.

    Synthetic labels are skipped unless demonstration mode is enabled. Entries
    that fail validation are recorded in ``load_errors`` and excluded, so that
    one malformed file cannot prevent the rest of the registry from loading.
    """
    registry = LabelRegistry()

    if not directory.exists():
        registry.snapshot_hash = registry.compute_hash()
        return registry

    for path in sorted(directory.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            registry.load_errors.append(f"{path.name}: invalid JSON ({exc.msg})")
            continue

        entries = payload.get("labels", [payload]) if isinstance(payload, dict) else payload
        if not isinstance(entries, list):
            registry.load_errors.append(f"{path.name}: expected a list of labels")
            continue

        for entry in entries:
            try:
                record = label_from_dict(entry, chain_default=chain_default)
            except LabelRegistryError as exc:
                registry.load_errors.append(f"{path.name}: {exc}")
                continue

            if record.is_synthetic and not is_demo:
                registry.load_errors.append(
                    f"{path.name}: synthetic label skipped because demo mode is off"
                )
                continue

            registry.add(record)

    registry.snapshot_hash = registry.compute_hash()
    return registry


def default_registry_dir() -> Path:
    """Return the configured label registry directory."""
    from app.core.config import get_settings

    settings = get_settings()
    configured = Path(settings.LABEL_REGISTRY_DIR)
    if configured.is_absolute():
        return configured
    backend_root = Path(__file__).resolve().parents[2]
    return backend_root / configured


def registry_from_settings() -> LabelRegistry:
    """Load the registry using current application settings."""
    from app.core.config import get_settings

    settings = get_settings()
    return load_registry(
        default_registry_dir(),
        is_demo=settings.DEMO_MODE,
        chain_default=settings.CHAIN_DEFAULT,
    )


def seed_timestamp() -> datetime:
    """Return the timestamp recorded with seeded labels."""
    return datetime.now(UTC)

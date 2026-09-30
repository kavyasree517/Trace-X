"""Controlled vocabulary enums for TRACE-X."""

from enum import Enum


class EntityType(str, Enum):
    EXCHANGE = "exchange"
    EXCHANGE_HOT_WALLET = "exchange_hot_wallet"
    EXCHANGE_DEPOSIT_ADDRESS = "exchange_deposit_address"
    PAYMENT_SERVICE = "payment_service"
    MIXER = "mixer"
    BRIDGE = "bridge"
    SMART_CONTRACT_SERVICE = "smart_contract_service"
    DECENTRALIZED_EXCHANGE = "decentralized_exchange"
    OTHER_SERVICE = "other_service"
    UNKNOWN = "unknown"


class ConnectionType(str, Enum):
    DIRECT = "direct"
    INDIRECT = "indirect"
    INFERRED = "inferred"


class AttributionState(str, Enum):
    VERIFIED_LABEL_MATCH = "verified_label_match"
    POTENTIAL_ASSOCIATION = "potential_association"
    NO_MATCH_IN_CURRENT_REFERENCES = "no_match_in_current_references"
    INSUFFICIENT_DATA = "insufficient_data"


class VerificationLevel(str, Enum):
    LEVEL_3_PRIMARY_SOURCE = "level_3_primary_source"
    LEVEL_2_REPUTABLE_SECONDARY = "level_2_reputable_secondary"
    LEVEL_1_COMMUNITY_OR_UNVERIFIED = "level_1_community_or_unverified"
    LEVEL_0_SYNTHETIC = "level_0_synthetic"


class EvidenceTag(str, Enum):
    OBSERVED = "observed"
    DERIVED = "derived"
    INFERRED = "inferred"


class PathBreakReason(str, Enum):
    MIXER_INTERACTION = "mixer_interaction"
    BRIDGE_INTERACTION = "bridge_interaction"
    UNSUPPORTED_CONTRACT = "unsupported_contract"
    SWAP_ASSET_CHANGE = "swap_asset_change"
    PRIVACY_PROTOCOL = "privacy_protocol"
    EXPANSION_LIMIT_REACHED = "expansion_limit_reached"
    DATA_UNAVAILABLE = "data_unavailable"
    TIME_WINDOW_EXCEEDED = "time_window_exceeded"


class CorroborationStrength(str, Enum):
    NONE = "none"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"


class SignalLevel(str, Enum):
    NOT_OBSERVED = "not_observed"
    OBSERVED_LOW = "observed_low"
    OBSERVED_MODERATE = "observed_moderate"
    OBSERVED_HIGH = "observed_high"


class CaseStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class IncidentDatePrecision(str, Enum):
    EXACT = "exact"
    DAY = "day"
    APPROXIMATE = "approximate"
    UNKNOWN = "unknown"


class TransferKind(str, Enum):
    NATIVE = "native"
    INTERNAL = "internal"
    TOKEN = "token"


class LabelOrigin(str, Enum):
    OBSERVED_LABEL = "observed_label"
    INFERRED_CLUSTER = "inferred_cluster"


class SourceType(str, Enum):
    PRIMARY_DISCLOSURE = "primary_disclosure"
    REPUTABLE_SECONDARY = "reputable_secondary"
    COMMUNITY = "community"
    DATASET = "dataset"
    SYNTHETIC = "synthetic"


class LabelChangeType(str, Enum):
    CREATED = "created"
    UPDATED = "updated"
    DEACTIVATED = "deactivated"


class TracingMethod(str, Enum):
    PROPORTIONAL = "proportional"
    FIFO = "fifo"
    NONE = "none"


class AttributionConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class AuditEventType(str, Enum):
    CASE_CREATED = "case_created"
    RETRIEVAL_STARTED = "retrieval_started"
    RETRIEVAL_COMPLETED = "retrieval_completed"
    RETRIEVAL_FAILED = "retrieval_failed"
    GRAPH_BUILT = "graph_built"
    ATTRIBUTION_APPLIED = "attribution_applied"
    SIGNALS_COMPLETED = "signals_computed"
    CORROBORATION_RUN = "corroboration_run"
    REPORT_GENERATED = "report_generated"
    CASE_DELETED = "case_deleted"

"""Typed application configuration loader and validator."""

from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application metadata
    APP_ENV: str = "development"
    APP_VERSION: str = "0.1.0"
    LOG_LEVEL: str = "INFO"

    # Network and CORS
    CORS_ALLOWED_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
        ]
    )

    # Execution modes
    DEMO_MODE: bool = True
    ALLOW_SYNTHETIC_LABELS: bool = True

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./tracex_dev.db"

    # Blockchain and adapter defaults
    CHAIN_DEFAULT: str = "ethereum"
    DATA_ADAPTER: str = "mock"

    # Upstream explorer configuration
    EXPLORER_API_BASE_URL: str = "https://api.etherscan.io/api"
    EXPLORER_API_KEY: str = ""
    EXPLORER_TIMEOUT_SECONDS: int = 15
    EXPLORER_MAX_RETRIES: int = 3
    EXPLORER_RATE_LIMIT_PER_SECOND: int = 4

    # Cache TTL configuration
    CACHE_TTL_HISTORICAL_SECONDS: int = 3600
    CACHE_TTL_RECENT_SECONDS: int = 60

    # Graph expansion thresholds
    GRAPH_MAX_HOPS_DEFAULT: int = 4
    GRAPH_MAX_HOPS_HARD_LIMIT: int = 6
    GRAPH_MAX_NODES_DEFAULT: int = 500
    GRAPH_MAX_NODES_HARD_LIMIT: int = 2000
    GRAPH_MAX_EDGES_DEFAULT: int = 2000
    GRAPH_MAX_EDGES_HARD_LIMIT: int = 8000
    GRAPH_TIME_WINDOW_DAYS_DEFAULT: int = 30
    GRAPH_TIME_WINDOW_DAYS_HARD_LIMIT: int = 180
    GRAPH_HIGH_DEGREE_THRESHOLD: int = 200
    GRAPH_MIN_TRANSFER_VALUE_USD_EQUIVALENT: float = 0.0
    GRAPH_VALUE_TRACING_METHOD: str = "proportional"
    GRAPH_INCOMING_EXPANSION_DEFAULT: bool = False
    GRAPH_DEADLINE_SECONDS: int = 90
    GRAPH_MIN_CONTINUITY_RATIO: float = 0.05
    GRAPH_MAX_PATHS_RETURNED: int = 25

    # Path ranking weights. Ordering only. Never shown as a probability.
    RANKING_WEIGHT_ANCHORED_TX: int = 40
    RANKING_WEIGHT_CONTINUITY: int = 25
    RANKING_WEIGHT_TIME_PROXIMITY: int = 20
    RANKING_WEIGHT_HOP_COUNT: int = 10
    RANKING_WEIGHT_TERMINAL_LABELLED: int = 5

    # Attribution thresholds
    LABEL_STALE_AFTER_DAYS: int = 365

    # Behavioral rule thresholds. Rationale recorded in docs/behavioral-signals.md.
    BEHAVIOR_RAPID_PASS_THROUGH_SECONDS: int = 3600
    BEHAVIOR_SPLIT_OUT_DEGREE: int = 3
    BEHAVIOR_MERGE_IN_DEGREE: int = 3
    BEHAVIOR_SPLIT_INTERVAL_SECONDS: int = 86400
    BEHAVIOR_EQUAL_VALUE_TOLERANCE: float = 0.001
    BEHAVIOR_EQUAL_VALUE_MIN_REPEATS: int = 3
    BEHAVIOR_PEEL_CHAIN_MAX_DEPTH: int = 4
    BEHAVIOR_BURST_WINDOW_SECONDS: int = 3600
    BEHAVIOR_ACTIVITY_WINDOW_SECONDS: int = 86400

    # Corroboration thresholds
    CORROBORATION_MIN_SHARED_PATH_LENGTH: int = 2
    CORROBORATION_MAX_TIME_SKEW_DAYS: int = 45
    CORROBORATION_HUB_EXCLUSION_DEGREE: int = 100

    # Rate limiting and request limits
    RATE_LIMIT_CASES_PER_MINUTE_PER_IP: int = 10
    RATE_LIMIT_REFRESH_PER_HOUR_PER_CASE: int = 3
    RATE_LIMIT_LABELS_PER_MINUTE_PER_IP: int = 30
    MAX_CONCURRENT_ANALYSES: int = 4
    IDEMPOTENCY_WINDOW_SECONDS: int = 60
    REQUEST_MAX_BODY_BYTES: int = 16384

    # Retention windows in days
    REPORT_RETENTION_DAYS: int = 90
    CASE_RETENTION_DAYS: int = 180

    # Analysis behaviour
    SYNC_ANALYSIS_IN_TEST_MODE: bool = True
    EXPLORER_MAX_ITEMS_PER_ADDRESS: int = 10000
    EXPLORER_FINALITY_BLOCKS: int = 64
    LABEL_REGISTRY_DIR: str = "data/label_registry"
    FIXTURES_DIR: str = "data/fixtures"

    # Internal secrets and roles
    APP_SECRET_KEY: str = "dev_secret_key_change_in_production_min32chars!"
    INVESTIGATOR_TOKEN: str = "dev_investigator_token_12345"
    ADMIN_TOKEN: str = "dev_admin_token_67890"

    @field_validator("ALLOW_SYNTHETIC_LABELS", mode="after")
    @classmethod
    def force_synthetic_labels_false_in_production(cls, v: bool, info: Any) -> bool:
        demo_mode = info.data.get("DEMO_MODE", False)
        if not demo_mode:
            return False
        return v

    def redacted_dict(self) -> dict[str, Any]:
        """Return configuration dictionary with sensitive values redacted."""
        secret_keys = {
            "EXPLORER_API_KEY",
            "APP_SECRET_KEY",
            "INVESTIGATOR_TOKEN",
            "ADMIN_TOKEN",
            "DATABASE_URL",
        }
        res: dict[str, Any] = {}
        for key, value in self.model_dump().items():
            if key in secret_keys:
                res[key] = "[REDACTED]" if value else ""
            else:
                res[key] = value
        return res


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached singleton application settings."""
    return Settings()

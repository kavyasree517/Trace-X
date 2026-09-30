"""Cache interface for adapter responses."""

from datetime import datetime, timezone
from typing import Any


class AdapterCache:
    """In-memory cache for historical immutable blocks."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[datetime, Any]] = {}

    def get(self, key: str) -> Any | None:
        if key not in self._store:
            return None
        expires_at, value = self._store[key]
        if datetime.now(timezone.utc) > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        from datetime import timedelta
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        self._store[key] = (expires_at, value)

    def clear(self) -> None:
        self._store.clear()

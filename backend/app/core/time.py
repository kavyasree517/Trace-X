"""Time utility functions enforcing UTC timezone standard."""

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return the current datetime in UTC timezone."""
    return datetime.now(UTC)


def format_iso_utc(dt: datetime) -> str:
    """Format datetime as ISO 8601 UTC string with trailing Z."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    else:
        dt = dt.astimezone(UTC)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso_utc(dt_str: str) -> datetime:
    """Parse ISO 8601 timestamp string into UTC datetime object."""
    if dt_str.endswith("Z"):
        dt_str = dt_str[:-1] + "+00:00"
    dt = datetime.fromisoformat(dt_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)

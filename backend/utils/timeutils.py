"""All timestamps are stored as naive UTC, generated on the SERVER (never trust the client clock)."""
from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_utc_naive(dt: datetime) -> datetime:
    """Client deadlines: aware -> converted to UTC; naive -> assumed already UTC."""
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def iso(dt: datetime | None) -> str | None:
    return dt.isoformat() + "Z" if dt else None

"""Application + audit logging (lines that CloudWatch / Cloud Logging / Render can ingest)."""
import json
import logging
import sys

from backend.config import settings

_configured = False


def _configure() -> None:
    global _configured
    if _configured:
        return
    logging.basicConfig(
        level=settings.log_level,
        stream=sys.stdout,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    _configured = True


def get_logger(name: str) -> logging.Logger:
    _configure()
    return logging.getLogger(name)


_audit = get_logger("audit")


def audit(event: str, **fields) -> None:
    """Security-relevant events: login, logout, grade, download, delete..."""
    _audit.info(json.dumps({"event": event, **fields}, default=str))

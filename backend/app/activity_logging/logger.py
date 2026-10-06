"""
Async activity logger — writes to ActivityLog in a background thread
so it never adds latency to the translation response (SRS requirement).
"""
import uuid
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.activity_log import ActivityLog

_executor = ThreadPoolExecutor(max_workers=2)


def _write_log(
    org_id: str,
    api_key_id: str | None,
    endpoint: str,
    status_code: int,
    latency_ms: int | None = None,
    region: str | None = None,
    request_summary: str | None = None,
) -> None:
    """Synchronous DB write — runs in a background thread."""
    with SessionLocal() as db:
        log = ActivityLog(
            id=str(uuid.uuid4()),
            org_id=org_id,
            api_key_id=api_key_id,
            endpoint=endpoint,
            status_code=status_code,
            latency_ms=latency_ms,
            region=region,
            request_summary=request_summary,
        )
        db.add(log)
        db.commit()


def log_activity(
    org_id: str,
    api_key_id: str | None,
    endpoint: str,
    status_code: int,
    latency_ms: int | None = None,
    region: str | None = None,
    request_summary: str | None = None,
) -> None:
    """Fire-and-forget activity log — never blocks the caller."""
    _executor.submit(
        _write_log,
        org_id,
        api_key_id,
        endpoint,
        status_code,
        latency_ms,
        region,
        request_summary,
    )

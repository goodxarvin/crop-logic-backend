from __future__ import annotations

from datetime import datetime
from typing import Any


def _isoformat(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def build_integration_meta(
    *,
    flow_type: str,
    source_type: str,
    source_service: str,
    ownership: str,
    live: bool,
    cached: bool,
    generated_at: Any = None,
    snapshot_at: Any = None,
    sync_attempted: bool | None = None,
    sync_status: str | None = None,
    notes: list[str] | None = None,
) -> dict[str, Any]:
    meta = {
        "flow_type": flow_type,
        "source_type": source_type,
        "source_service": source_service,
        "ownership": ownership,
        "live": live,
        "cached": cached,
    }
    if generated_at is not None:
        meta["generated_at"] = _isoformat(generated_at)
    if snapshot_at is not None:
        meta["snapshot_at"] = _isoformat(snapshot_at)
    if sync_attempted is not None:
        meta["sync_attempted"] = sync_attempted
    if sync_status is not None:
        meta["sync_status"] = sync_status
    if notes:
        meta["notes"] = notes
    return meta

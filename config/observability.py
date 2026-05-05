from __future__ import annotations

import logging
import time
from collections import Counter
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any


logger = logging.getLogger(__name__)
_request_id_ctx: ContextVar[str | None] = ContextVar("backend_request_id", default=None)
METRICS: Counter[str] = Counter()


def set_request_id(request_id: str | None) -> None:
    _request_id_ctx.set(request_id)


def get_request_id() -> str | None:
    return _request_id_ctx.get()


def record_metric(name: str, value: int = 1, **tags: Any) -> None:
    suffix = ",".join(f"{key}={tags[key]}" for key in sorted(tags) if tags[key] is not None)
    metric_key = f"{name}|{suffix}" if suffix else name
    METRICS[metric_key] += value


@dataclass
class ClassifiedFailure:
    error_code: str
    failure_type: str
    retriable: bool


def classify_exception(exc: Exception) -> ClassifiedFailure:
    exc_name = exc.__class__.__name__.lower()
    message = str(exc).lower()
    if "timeout" in exc_name or "timeout" in message:
        return ClassifiedFailure("timeout", "timeout", True)
    if "json" in exc_name or "json" in message:
        return ClassifiedFailure("parse_error", "parse_error", False)
    if "validation" in exc_name or "invalid" in message:
        return ClassifiedFailure("validation_failure", "validation_failure", False)
    if "connection" in exc_name or "unavailable" in message:
        return ClassifiedFailure("dependency_unavailable", "dependency_unavailable", True)
    return ClassifiedFailure("provider_error", "provider_error", True)


def log_event(
    *,
    level: int,
    message: str,
    source: str,
    provider: str | None,
    operation: str,
    result_status: str,
    duration_ms: float | None = None,
    error_code: str | None = None,
    **extra: Any,
) -> None:
    payload = {
        "source": source,
        "provider": provider,
        "operation": operation,
        "result_status": result_status,
        "duration_ms": round(duration_ms, 2) if duration_ms is not None else None,
        "error_code": error_code,
        "request_id": get_request_id(),
    }
    payload.update({key: value for key, value in extra.items() if value is not None})
    logger.log(level, message, extra={"event": payload})


class observe_operation:
    def __init__(self, *, source: str, provider: str | None, operation: str):
        self.source = source
        self.provider = provider
        self.operation = operation
        self.started_at = 0.0

    def __enter__(self):
        self.started_at = time.monotonic()
        log_event(
            level=logging.INFO,
            message="backend operation started",
            source=self.source,
            provider=self.provider,
            operation=self.operation,
            result_status="started",
        )
        return self

    def __exit__(self, exc_type, exc, _tb):
        duration_ms = (time.monotonic() - self.started_at) * 1000
        if exc is None:
            log_event(
                level=logging.INFO,
                message="backend operation completed",
                source=self.source,
                provider=self.provider,
                operation=self.operation,
                result_status="success",
                duration_ms=duration_ms,
            )
            record_metric("backend.operation.success", source=self.source, provider=self.provider, operation=self.operation)
            return False

        failure = classify_exception(exc)
        log_event(
            level=logging.ERROR,
            message="backend operation failed",
            source=self.source,
            provider=self.provider,
            operation=self.operation,
            result_status="error",
            duration_ms=duration_ms,
            error_code=failure.error_code,
            failure_type=failure.failure_type,
        )
        record_metric(
            "backend.operation.failure",
            source=self.source,
            provider=self.provider,
            operation=self.operation,
            error_code=failure.error_code,
        )
        return False

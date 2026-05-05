from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FailureContract:
    status: str = "error"
    error_code: str = "internal_error"
    message: str = ""
    source: str = "application"
    warnings: list[str] = field(default_factory=list)
    retriable: bool = False
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "status": self.status,
            "error_code": self.error_code,
            "message": self.message,
            "source": self.source,
            "warnings": list(self.warnings),
            "retriable": self.retriable,
        }
        if self.details:
            payload["details"] = self.details
        return payload


class StructuredServiceError(Exception):
    def __init__(
        self,
        *,
        error_code: str,
        message: str,
        source: str,
        warnings: list[str] | None = None,
        retriable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.contract = FailureContract(
            error_code=error_code,
            message=message,
            source=source,
            warnings=warnings or [],
            retriable=retriable,
            details=details or {},
        )

    def to_dict(self) -> dict[str, Any]:
        return self.contract.to_dict()

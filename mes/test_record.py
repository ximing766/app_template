# -*- coding: utf-8 -*-
"""Test result model and MES JSON payload.

The payload schema is deliberately flat and explicit — adapt :meth:`TestResult.to_payload`
once the real MES field names are known.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    """Current time as an ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class TestItem:
    """A single measurement inside a test run."""

    name: str
    value: Any = None
    unit: str = ""
    lower_limit: Optional[float] = None
    upper_limit: Optional[float] = None
    passed: bool = True
    message: str = ""

    def failed_limits(self) -> bool:
        """Check numeric value against inclusive limits when provided."""
        if not isinstance(self.value, (int, float)) or isinstance(self.value, bool):
            return False
        if self.lower_limit is not None and self.value < self.lower_limit:
            return True
        if self.upper_limit is not None and self.value > self.upper_limit:
            return True
        return False

    def is_pass(self) -> bool:
        return bool(self.passed) and not self.failed_limits()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "lower_limit": self.lower_limit,
            "upper_limit": self.upper_limit,
            "passed": self.is_pass(),
            "message": self.message,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestItem":
        return cls(
            name=str(data.get("name", "")),
            value=data.get("value"),
            unit=str(data.get("unit", "")),
            lower_limit=data.get("lower_limit"),
            upper_limit=data.get("upper_limit"),
            passed=bool(data.get("passed", True)),
            message=str(data.get("message", "")),
        )


@dataclass
class TestResult:
    """One complete production test run for a unit."""

    serial_number: str
    product: str = ""
    station: str = ""
    operator: str = ""
    started_at: str = field(default_factory=utc_now_iso)
    finished_at: str = field(default_factory=utc_now_iso)
    items: List[TestItem] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)
    record_id: str = field(default_factory=lambda: uuid.uuid4().hex)

    # ------------------------------------------------------------------
    # Result helpers
    # ------------------------------------------------------------------

    def overall_passed(self) -> bool:
        """A run passes only when every item passes."""
        return all(item.is_pass() for item in self.items)

    def add_item(self, item: TestItem) -> "TestResult":
        self.items.append(item)
        return self

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_payload(self) -> Dict[str, Any]:
        """JSON body expected by the MES upload endpoint."""
        payload: Dict[str, Any] = {
            "recordId": self.record_id,
            "serialNumber": self.serial_number,
            "product": self.product,
            "station": self.station,
            "operator": self.operator,
            "startedAt": self.started_at,
            "finishedAt": self.finished_at,
            "overallPassed": self.overall_passed(),
            "items": [item.to_dict() for item in self.items],
        }
        if self.extra:
            payload["extra"] = dict(self.extra)
        return payload

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "TestResult":
        return cls(
            serial_number=str(payload.get("serialNumber", "")),
            product=str(payload.get("product", "")),
            station=str(payload.get("station", "")),
            operator=str(payload.get("operator", "")),
            started_at=str(payload.get("startedAt", utc_now_iso())),
            finished_at=str(payload.get("finishedAt", utc_now_iso())),
            items=[TestItem.from_dict(item) for item in payload.get("items", [])],
            extra=dict(payload.get("extra", {}) or {}),
            record_id=str(payload.get("recordId") or uuid.uuid4().hex),
        )

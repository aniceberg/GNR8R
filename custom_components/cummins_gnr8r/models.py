from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class BackendUpdate:
    backend: str
    logical_signals: dict[str, bool | None]
    values: dict[str, Any]
    details: dict[str, Any]
    fetched_at: datetime


@dataclass(slots=True)
class CoordinatorSnapshot:
    backend: str
    values: dict[str, Any]
    details: dict[str, Any]
    fetched_at: datetime


@dataclass(frozen=True, slots=True)
class LogicalSignalMapping:
    entity_id: str
    inverted: bool = False


@dataclass(frozen=True, slots=True)
class RegisterGroup:
    key: str
    start_address: int
    count: int

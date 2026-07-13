"""Shared read-only generator status normalization."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .const import (
    ACTION_REQUIRED_KEY,
    OPERATING_STATUS_KEY,
    ROLE_GENERATOR_FAULT,
    ROLE_GENERATOR_RUNNING,
)


def decode_operating_status(values: Mapping[str, Any]) -> dict[str, bool | str | None]:
    """Normalize backend values into conservative status entities."""
    fault = _as_bool(values.get(ROLE_GENERATOR_FAULT))
    running = _as_bool(values.get(ROLE_GENERATOR_RUNNING))
    not_in_auto = _as_bool(values.get("not_in_auto"))
    action_required = _as_bool(values.get(ACTION_REQUIRED_KEY))

    if action_required is None:
        action_required = fault

    if fault is True:
        status = "Fault"
    elif not_in_auto is True:
        status = "Not in auto"
    elif running is True:
        status = "Running"
    elif fault is False and running is False:
        status = "Stopped"
    else:
        status = "Transition / unknown"

    return {
        OPERATING_STATUS_KEY: status,
        ACTION_REQUIRED_KEY: action_required,
    }


def _as_bool(value: Any) -> bool | None:
    """Return boolean values without treating unknown values as false."""
    return value if isinstance(value, bool) else None

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from ..const import (
    BACKEND_ESPHOME_DISCRETE,
    ROLE_ATS_ON_GENERATOR,
    ROLE_GENERATOR_FAULT,
    ROLE_GENERATOR_RUNNING,
    ROLE_UTILITY_AVAILABLE,
)
from ..models import BackendUpdate, LogicalSignalMapping
from .base import DiscreteEntityValidationError


class ESPHomeDiscreteBackend:
    """Read logical generator signals from mapped HA entities."""

    backend_type = BACKEND_ESPHOME_DISCRETE
    backend_name = "ESPHome Discrete"
    device_model = "Discrete I/O Monitor"

    def __init__(self, hass: HomeAssistant, mappings: Mapping[str, LogicalSignalMapping]) -> None:
        self.hass = hass
        self._mappings = dict(mappings)
        self.source_identifier = ",".join(
            sorted(mapping.entity_id for mapping in self._mappings.values())
        )

    @property
    def mappings(self) -> dict[str, LogicalSignalMapping]:
        """Return configured mappings."""
        return self._mappings

    async def async_fetch(self) -> BackendUpdate:
        """Fetch mapped source states from Home Assistant."""
        logical_signals: dict[str, bool | None] = {}
        source_states: dict[str, str | None] = {}

        for role, mapping in self._mappings.items():
            state = self.hass.states.get(mapping.entity_id)
            source_states[role] = state.state if state is not None else None
            logical_signals[role] = _apply_inversion(
                _coerce_state(state.state if state else None), mapping
            )

        return BackendUpdate(
            backend=self.backend_type,
            logical_signals=logical_signals,
            values={},
            details={
                "backend_name": self.backend_name,
                "source_states": source_states,
                "mappings": {
                    role: {"entity_id": mapping.entity_id, "inverted": mapping.inverted}
                    for role, mapping in self._mappings.items()
                },
            },
            fetched_at=datetime.now(UTC),
        )


async def async_validate_entity_mappings(
    hass: HomeAssistant, mappings: Mapping[str, LogicalSignalMapping]
) -> None:
    """Validate that mapped entities exist."""
    registry = er.async_get(hass)
    missing: list[str] = []
    for mapping in mappings.values():
        if (
            hass.states.get(mapping.entity_id) is None
            and registry.async_get(mapping.entity_id) is None
        ):
            missing.append(mapping.entity_id)

    if missing:
        raise DiscreteEntityValidationError(
            f"Missing mapped entities: {', '.join(sorted(missing))}"
        )


def build_discrete_mappings(data: Mapping[str, Any]) -> dict[str, LogicalSignalMapping]:
    """Build logical role mappings from config data."""
    return {
        ROLE_UTILITY_AVAILABLE: LogicalSignalMapping(
            entity_id=data["utility_available_entity_id"],
            inverted=bool(data["invert_utility_available"]),
        ),
        ROLE_ATS_ON_GENERATOR: LogicalSignalMapping(
            entity_id=data["ats_on_generator_entity_id"],
            inverted=bool(data["invert_ats_on_generator"]),
        ),
        ROLE_GENERATOR_RUNNING: LogicalSignalMapping(
            entity_id=data["generator_running_entity_id"],
            inverted=bool(data["invert_generator_running"]),
        ),
        ROLE_GENERATOR_FAULT: LogicalSignalMapping(
            entity_id=data["generator_fault_entity_id"],
            inverted=bool(data["invert_generator_fault"]),
        ),
    }


def _coerce_state(state: str | None) -> bool | None:
    """Convert a Home Assistant state string into a boolean-ish value."""
    if state is None or state in {STATE_UNKNOWN, STATE_UNAVAILABLE}:
        return None
    if state == STATE_ON:
        return True
    if state == STATE_OFF:
        return False
    lowered = state.lower()
    if lowered in {"true", "open", "detected"}:
        return True
    if lowered in {"false", "closed", "clear"}:
        return False
    return None


def _apply_inversion(value: bool | None, mapping: LogicalSignalMapping) -> bool | None:
    """Apply configured inversion to a logical value."""
    if value is None:
        return None
    return not value if mapping.inverted else value
